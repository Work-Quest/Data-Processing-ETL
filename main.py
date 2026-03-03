from __future__ import annotations

import json
from datetime import date, datetime, timezone

from db import get_connection
from extract import build_member_log_data, fetch_logs_with_max_time
from repository.etl_repository import (
    ensure_checkpoint_row,
    etl_run_finish,
    etl_run_start,
    get_checkpoint_last_time,
    set_checkpoint_last_time,
    touch_checkpoint,
)
from repository.user_feature_daily_query import (
    fetch_user_feature_daily_by_member_ids,
    fetch_user_feature_daily_by_project_ids,
)
from repository.user_feature_profile_repository import upsert_user_feature_daily
from train import train_kmeans
from transform.transform import transform
from utils import (
    diligence_score_from_counts,
    merge_additive_arrays,
    parse_t_score,
    safe_json_list,
)


def team_score_from_counts(
    *,
    assigned: int,
    created: int,
    completed: int,
    deleted: int,
    buff: int,
    debuff: int,
) -> float:
    """
    Raw team score before T-score:
      - task actions weight 1
      - buff/debuff weight 3 (more impact)
    """
    task_part = float(assigned + created + completed + deleted) * 1.0
    interaction_part = float(buff) * 3.0 + float(debuff) * 3.0
    return task_part + interaction_part


def run_pipeline():
    conn = get_connection()
    run_id = None
    pipeline_name = "log_pipeline"

    try:
        ensure_checkpoint_row(conn, pipeline_name)
        last_time = get_checkpoint_last_time(conn, pipeline_name) or datetime(
            1970, 1, 1, tzinfo=timezone.utc
        )

        run_id = etl_run_start(conn, pipeline_name)

        # Fetch only new logs since checkpoint time
        logs, max_dt = fetch_logs_with_max_time(last_time.isoformat())
        if not logs:
            touch_checkpoint(conn, pipeline_name)
            etl_run_finish(conn, run_id, status="SUCCESS", logs_processed=0)
            conn.commit()
            print("ETL completed (no new logs)")
            return

        data = build_member_log_data(logs)
        checkpoint_date = last_time.date()
        today = date.today()

        # Compute per-user increments for this window
        increments, logs_processed = transform(data, checkpoint_date)

        impacted_member_ids = list(increments.keys())
        existing_by_member = fetch_user_feature_daily_by_member_ids(conn, impacted_member_ids)

        merged_by_member: dict[str, dict] = {}
        impacted_projects: set[str] = set()

        # Merge arrays + diligence counters for members touched in this window
        for mid, inc in increments.items():
            old = existing_by_member.get(mid)
            pid = inc.get("project_id") or (old.get("project_id") if old else None)
            if not pid:
                continue

            impacted_projects.add(pid)

            old_start = (old.get("window_start_date") if old else None) or checkpoint_date
            old_load = safe_json_list(old.get("work_load_per_day")) if old else []
            old_speed = safe_json_list(old.get("work_speed")) if old else []

            start_date, merged_load = merge_additive_arrays(
                old_start=old_start,
                old_arr=old_load,
                new_start=checkpoint_date,
                new_arr=inc.get("work_load_inc") or [],
                today=today,
            )
            _start_date2, merged_speed = merge_additive_arrays(
                old_start=old_start,
                old_arr=old_speed,
                new_start=checkpoint_date,
                new_arr=inc.get("work_speed_inc") or [],
                today=today,
            )

            p1 = int((old.get("diligence_p1") if old else 0) or 0) + int(inc.get("diligence_p1_inc") or 0)
            p2 = int((old.get("diligence_p2") if old else 0) or 0) + int(inc.get("diligence_p2_inc") or 0)
            p3 = int((old.get("diligence_p3") if old else 0) or 0) + int(inc.get("diligence_p3_inc") or 0)
            p4 = int((old.get("diligence_p4") if old else 0) or 0) + int(inc.get("diligence_p4_inc") or 0)

            team_buff = int((old.get("team_buff") if old else 0) or 0) + int(inc.get("team_buff_inc") or 0)
            team_debuff = int((old.get("team_debuff") if old else 0) or 0) + int(inc.get("team_debuff_inc") or 0)

            task_assigned = int((old.get("task_assigned") if old else 0) or 0) + int(inc.get("task_assigned_inc") or 0)
            task_created = int((old.get("task_created") if old else 0) or 0) + int(inc.get("task_created_inc") or 0)
            task_completed = int((old.get("task_completed") if old else 0) or 0) + int(inc.get("task_completed_inc") or 0)
            task_deleted = int((old.get("task_deleted") if old else 0) or 0) + int(inc.get("task_deleted_inc") or 0)

            merged_by_member[mid] = {
                "project_member_id": mid,
                "project_id": pid,
                "window_start_date": start_date,
                "work_load_per_day": json.dumps(merged_load),
                "work_speed": json.dumps(merged_speed),
                "diligence_p1": p1,
                "diligence_p2": p2,
                "diligence_p3": p3,
                "diligence_p4": p4,
                "team_buff": team_buff,
                "team_debuff": team_debuff,
                "task_assigned": task_assigned,
                "task_created": task_created,
                "task_completed": task_completed,
                "task_deleted": task_deleted,
            }

        # Include all existing members in impacted projects so T-score recompute is correct
        project_rows = fetch_user_feature_daily_by_project_ids(conn, impacted_projects)
        for r in project_rows:
            mid = r["project_member_id"]
            if mid in merged_by_member:
                continue

            old_start = r.get("window_start_date") or checkpoint_date
            old_load = safe_json_list(r.get("work_load_per_day"))
            old_speed = safe_json_list(r.get("work_speed"))

            start_date, merged_load = merge_additive_arrays(
                old_start=old_start,
                old_arr=old_load,
                new_start=today,
                new_arr=[],
                today=today,
            )
            _start_date2, merged_speed = merge_additive_arrays(
                old_start=old_start,
                old_arr=old_speed,
                new_start=today,
                new_arr=[],
                today=today,
            )

            merged_by_member[mid] = {
                "project_member_id": mid,
                "project_id": r["project_id"],
                "window_start_date": start_date,
                "work_load_per_day": json.dumps(merged_load),
                "work_speed": json.dumps(merged_speed),
                "diligence_p1": int(r.get("diligence_p1") or 0),
                "diligence_p2": int(r.get("diligence_p2") or 0),
                "diligence_p3": int(r.get("diligence_p3") or 0),
                "diligence_p4": int(r.get("diligence_p4") or 0),
                "team_buff": int(r.get("team_buff") or 0),
                "team_debuff": int(r.get("team_debuff") or 0),
                "task_assigned": int(r.get("task_assigned") or 0),
                "task_created": int(r.get("task_created") or 0),
                "task_completed": int(r.get("task_completed") or 0),
                "task_deleted": int(r.get("task_deleted") or 0),
            }

        # Compute raw diligence + raw team scores, then recompute T-scores per project
        diligence_array = []
        team_array = []
        for rec in merged_by_member.values():
            diligence_raw = diligence_score_from_counts(
                rec["diligence_p1"], rec["diligence_p2"], rec["diligence_p3"], rec["diligence_p4"]
            )
            diligence_array.append(
                {"project_id": rec["project_id"], "user_id": rec["project_member_id"], "weight": diligence_raw}
            )
            team_raw = team_score_from_counts(
                assigned=rec["task_assigned"],
                created=rec["task_created"],
                completed=rec["task_completed"],
                deleted=rec["task_deleted"],
                buff=rec["team_buff"],
                debuff=rec["team_debuff"],
            )
            team_array.append(
                {"project_id": rec["project_id"], "user_id": rec["project_member_id"], "weight": team_raw}
            )

        diligence_t, _d_stats = parse_t_score(diligence_array)
        team_t, _t_stats = parse_t_score(team_array)

        upsert_rows = []
        for rec in merged_by_member.values():
            pid = rec["project_id"]
            mid = rec["project_member_id"]
            # store diligence t-score in diligence column
            rec["diligence"] = float(diligence_t.get(pid, {}).get(mid, 50.0))
            # store teamwork t-score in team_work column
            rec["team_work"] = float(team_t.get(pid, {}).get(mid, 50.0))
            rec["strength"] = "WIP"
            upsert_rows.append(rec)

        upsert_user_feature_daily(upsert_rows, connection=conn)

        touch_checkpoint(conn, pipeline_name)
        if max_dt is not None:
            set_checkpoint_last_time(conn, max_dt, pipeline_name)
        etl_run_finish(conn, run_id, status="SUCCESS", logs_processed=logs_processed)
        conn.commit()

        print("ETL completed")

    except Exception as e:
        conn.rollback()
        if run_id:
            etl_run_finish(conn, run_id, status="FAILED", logs_processed=0, error_message=str(e))
            conn.commit()
        raise
    finally:
        conn.close()


def run_training():
    train_kmeans()
    print("Training completed")


if __name__ == "__main__":
    run_pipeline()


