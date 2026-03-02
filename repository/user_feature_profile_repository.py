from __future__ import annotations

from typing import Any, Iterable, Mapping

from psycopg2.extras import execute_values

from db import get_connection


USER_FEATURE_DAILY_COLUMNS = (
    "project_member_id",
    "project_id",
    "work_load_per_day",
    "diligence",
    "team_work",
    "strength",
    "work_speed",
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
      - work_load_per_day (str)
      - diligence (float)
      - team_work (float)
      - strength (str)
      - work_speed (str/None)

    Returns number of input rows.
    """

    rows_list = list(profiles)
    if not rows_list:
        return 0

    values = []
    for p in rows_list:
        values.append(
            (
                str(p["project_member_id"]),
                str(p["project_id"]),
                str(p["work_load_per_day"]),
                float(p["diligence"]),
                float(p["team_work"]),
                str(p["strength"]),
                str(p["work_speed"]),
            )
        )

    sql = f"""
    INSERT INTO user_feature_daily ({", ".join(USER_FEATURE_DAILY_COLUMNS)})
    VALUES %s
    ON CONFLICT (project_member_id)
    DO UPDATE SET
        project_id = EXCLUDED.project_id,
        work_load_per_day = EXCLUDED.work_load_per_day,
        diligence = EXCLUDED.diligence,
        team_work = EXCLUDED.team_work,
        strength = EXCLUDED.diligence,
        work_speed = EXCLUDED.work_speed
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



