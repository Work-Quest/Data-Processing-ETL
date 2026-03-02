from transform.diligence_calculation import diligence_calculate
from transform.work_load_calculation import work_load_calculate
from transform.work_speed_calculation import work_speed_calculate
from utils import _parse_dt, parse_t_score
import json


def transform(data):
    """
    Pure transform step: compute per-user features and return rows ready for DB upsert.

    Returns:
      - rows: list[dict] for `user_feature_daily` upsert
      - logs_processed: int
    """

    # array for calculate t-score
    diligence_array = []
    per_user = {}

    for user, log in data.items():
        work_speed = work_speed_calculate(log)
        work_load = work_load_calculate(
            log, data, _parse_dt("2026-02-15T10:39:30.044081Z").date()
        )
        diligence, project_id = diligence_calculate(log, data)

        per_user[str(user)] = {
            "project_member_id": str(user),
            "project_id": str(project_id) if project_id else None,
            "work_load": work_load,
            "work_speed": work_speed,
            "diligence": diligence,
        }

        if diligence is not None and project_id:
            diligence_array.append(
                {"project_id": str(project_id), "user_id": str(user), "weight": float(diligence)}
            )

    diligence_t_score, diligence_stat = parse_t_score(diligence_array)

    # Build rows for upsert into user_feature_daily
    rows = []
    for rec in per_user.values():
        print(rec)
        if not rec["project_id"]:
            continue

        pid = rec["project_id"]
        mid = rec["project_member_id"]

        # simple category rule (not null)
        team_work = 0
        work_category = "WIP"
        rows.append(
            {
                "project_member_id": mid,
                "project_id": pid,
                "work_load_per_day": json.dumps(rec["work_load"]),
                "diligence" : diligence_t_score[pid][mid],
                "team_work": team_work,
                "strength": work_category,
                "work_speed": json.dumps(rec["work_speed"]),
            }
        )

    # logs processed: count list items in each member's log dict
    logs_processed = 0
    for logs in data.values():
        for v in (logs or {}).values():
            if isinstance(v, list):
                logs_processed += len(v)

    return rows, logs_processed

