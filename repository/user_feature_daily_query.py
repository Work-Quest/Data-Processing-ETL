from __future__ import annotations

from typing import Any, Iterable


def fetch_user_feature_daily_by_member_ids(conn, member_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    ids = [str(x) for x in member_ids if x]
    if not ids:
        return {}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              project_member_id::text,
              project_id::text,
              window_start_date,
              work_load_per_day,
              work_speed,
              diligence,
              team_work,
              strength,
              diligence_p1,
              diligence_p2,
              diligence_p3,
              diligence_p4,
              team_buff,
              team_debuff,
              task_assigned,
              task_created,
              task_completed,
              task_deleted
            FROM user_feature_daily
            WHERE project_member_id = ANY(%s::uuid[])
            """,
            (ids,),
        )
        rows = cur.fetchall()

    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        out[r[0]] = {
            "project_member_id": r[0],
            "project_id": r[1],
            "window_start_date": r[2],
            "work_load_per_day": r[3],
            "work_speed": r[4],
            "diligence": r[5],
            "team_work": r[6],
            "strength": r[7],
            "diligence_p1": r[8],
            "diligence_p2": r[9],
            "diligence_p3": r[10],
            "diligence_p4": r[11],
            "team_buff": r[12],
            "team_debuff": r[13],
            "task_assigned": r[14],
            "task_created": r[15],
            "task_completed": r[16],
            "task_deleted": r[17],
        }
    return out


def fetch_user_feature_daily_by_project_ids(conn, project_ids: Iterable[str]) -> list[dict[str, Any]]:
    ids = [str(x) for x in project_ids if x]
    if not ids:
        return []

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              project_member_id::text,
              project_id::text,
              window_start_date,
              work_load_per_day,
              work_speed,
              diligence,
              team_work,
              strength,
              diligence_p1,
              diligence_p2,
              diligence_p3,
              diligence_p4,
              team_buff,
              team_debuff,
              task_assigned,
              task_created,
              task_completed,
              task_deleted
            FROM user_feature_daily
            WHERE project_id = ANY(%s::uuid[])
            """,
            (ids,),
        )
        rows = cur.fetchall()

    out = []
    for r in rows:
        out.append(
            {
                "project_member_id": r[0],
                "project_id": r[1],
                "window_start_date": r[2],
                "work_load_per_day": r[3],
                "work_speed": r[4],
                "diligence": r[5],
                "team_work": r[6],
                "strength": r[7],
                "diligence_p1": r[8],
                "diligence_p2": r[9],
                "diligence_p3": r[10],
                "diligence_p4": r[11],
                "team_buff": r[12],
                "team_debuff": r[13],
                "task_assigned": r[14],
                "task_created": r[15],
                "task_completed": r[16],
                "task_deleted": r[17],
            }
        )
    return out


