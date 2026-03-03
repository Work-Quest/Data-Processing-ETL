from __future__ import annotations

from db import get_connection


def get_last_checkpoint_time(pipeline_name: str = "log_pipeline"):
    """Return last_time from etl_checkpoint (or None)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT last_time
        FROM etl_checkpoint
        WHERE pipeline_name = %s
        """,
        (pipeline_name,),
    )

    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def update_checkpoint_time(last_time, pipeline_name: str = "log_pipeline"):
    """Set last_time and updated_at."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE etl_checkpoint
        SET last_time = %s, updated_at = NOW()
        WHERE pipeline_name = %s
        """,
        (last_time, pipeline_name),
    )

    conn.commit()
    conn.close()