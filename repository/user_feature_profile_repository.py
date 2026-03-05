from __future__ import annotations

from typing import Any, Iterable, Mapping

from psycopg2.extras import execute_values

from db import get_connection


USER_FEATURE_DAILY_COLUMNS = (
    "project_member_id",
    "project_id",
    "window_start_date",
    "work_load_per_day",
    "work_speed",
    "diligence",
    "team_work",
    "strength",
    "most_frequency_task",
    "most_frequency_task_counters",
    "work_quality",
    "best_quality",
    "best_quality_avg",
    "quality_per_category",
    "diligence_p1",
    "diligence_p2",
    "diligence_p3",
    "diligence_p4",
    "team_buff",
    "team_debuff",
    "task_assigned",
    "task_created",
    "task_completed",
    "task_deleted",
)


def upsert_user_feature_daily(
    profiles: Iterable[Mapping[str, Any]],
    *,
    connection=None,
) -> int:
    """
    UPSERT rows into `user_feature_daily` using PRIMARY KEY(project_member_id).

    Expected keys per profile:
      - project_member_id (UUID/str)
      - project_id (UUID/str)
      - window_start_date (date/str)
      - work_load_per_day (str)
      - work_speed (str)  # JSON string
      - diligence (float)  # raw diligence score
      - team_work (float)  # t-score
      - strength (str)
      - diligence_p1..p4 (int)

    Returns number of input rows.
    """

    rows_list = list(profiles)
    if not rows_list:
        return 0

    values = []
    for p in rows_list:
        strength = p.get("strength") or p.get("work_category") or "WIP"
        # work_speed stored as JSON text; never allow None -> store "[]"
        work_speed = p.get("work_speed")
        if work_speed is None:
            work_speed = "[]"
        quality_per_category = p.get("quality_per_category")
        if quality_per_category is None:
            quality_per_category = "{}"
        best_quality_avg = p.get("best_quality_avg")
        # be defensive: some callers may accidentally pass (best_category, best_avg)
        if isinstance(best_quality_avg, tuple) and len(best_quality_avg) >= 2:
            best_quality_avg = best_quality_avg[1]

        values.append(
            (
                str(p["project_member_id"]),
                str(p["project_id"]),
                p["window_start_date"],
                str(p["work_load_per_day"]),
                str(work_speed),
                float(p.get("diligence") or 0.0),
                float(p.get("team_work") or 0.0),
                str(strength),
                (p.get("most_frequency_task") if p.get("most_frequency_task") is not None else None),
                int(p.get("most_frequency_task_counters") or 0),
                (float(p.get("work_quality")) if p.get("work_quality") is not None else None),
                (p.get("best_quality") if p.get("best_quality") is not None else None),
                (float(best_quality_avg) if best_quality_avg is not None else None),
                str(quality_per_category),
                int(p.get("diligence_p1") or 0),
                int(p.get("diligence_p2") or 0),
                int(p.get("diligence_p3") or 0),
                int(p.get("diligence_p4") or 0),
                int(p.get("team_buff") or 0),
                int(p.get("team_debuff") or 0),
                int(p.get("task_assigned") or 0),
                int(p.get("task_created") or 0),
                int(p.get("task_completed") or 0),
                int(p.get("task_deleted") or 0),
            )
        )

    sql = f"""
    INSERT INTO user_feature_daily ({", ".join(USER_FEATURE_DAILY_COLUMNS)})
    VALUES %s
    ON CONFLICT (project_member_id)
    DO UPDATE SET
        project_id = EXCLUDED.project_id,
        window_start_date = EXCLUDED.window_start_date,
        work_load_per_day = EXCLUDED.work_load_per_day,
        work_speed = EXCLUDED.work_speed,
        diligence = EXCLUDED.diligence,
        team_work = EXCLUDED.team_work,
        strength = EXCLUDED.strength,
        most_frequency_task = EXCLUDED.most_frequency_task,
        most_frequency_task_counters = EXCLUDED.most_frequency_task_counters,
        work_quality = EXCLUDED.work_quality,
        best_quality = EXCLUDED.best_quality,
        best_quality_avg = EXCLUDED.best_quality_avg,
        quality_per_category = EXCLUDED.quality_per_category,
        diligence_p1 = EXCLUDED.diligence_p1,
        diligence_p2 = EXCLUDED.diligence_p2,
        diligence_p3 = EXCLUDED.diligence_p3,
        diligence_p4 = EXCLUDED.diligence_p4,
        team_buff = EXCLUDED.team_buff,
        team_debuff = EXCLUDED.team_debuff,
        task_assigned = EXCLUDED.task_assigned,
        task_created = EXCLUDED.task_created,
        task_completed = EXCLUDED.task_completed,
        task_deleted = EXCLUDED.task_deleted,
        modified_at = NOW()
    """

    conn = connection or get_connection()
    should_close = connection is None

    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=1000)
        if should_close:
            conn.commit()
        return len(values)
    finally:
        if should_close:
            conn.close()



