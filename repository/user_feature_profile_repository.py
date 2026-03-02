from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from psycopg2.extras import execute_values

from db import get_connection


PROFILE_INSERT_COLUMNS = (
    "project_member_id",
    "project_id",
    "work_load_per_day",
    "team_work",
    "work_category",
    "work_speed",
)


def insert_user_feature_profiles(
    profiles: Iterable[Mapping[str, Any]],
    *,
    connection=None,
) -> int:
    """
    Insert rows into `user_feature_profile`.

    Expected keys per profile (post-migration 0003):
      - project_member_id (UUID/str)
      - project_id (UUID/str)
      - work_load_per_day (str)
      - team_work (float/int)
      - work_category (str)
      - work_speed (float/int/None)

    Returns number of inserted rows.
    """

    # Materialize once; execute_values requires a concrete sequence anyway.
    rows_list = list(profiles)
    if not rows_list:
        return 0

    values = []
    for p in rows_list:
        values.append(
            (
                p["project_member_id"],
                p["project_id"],
                p["work_load_per_day"],
                float(p["team_work"]),
                p["work_category"],
                p.get("work_speed"),
            )
        )

    sql = (
        "INSERT INTO user_feature_profile ("
        + ", ".join(PROFILE_INSERT_COLUMNS)
        + ") VALUES %s"
    )

    conn = connection or get_connection()
    should_close = connection is None

    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=1000)
        conn.commit()
        return len(values)
    finally:
        if should_close:
            conn.close()



