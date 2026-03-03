from __future__ import annotations

from typing import Optional


def ensure_checkpoint_row(conn, pipeline_name: str = "log_pipeline") -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_checkpoint (pipeline_name, last_time)
            VALUES (%s, NOW())
            ON CONFLICT (pipeline_name) DO NOTHING;
            """,
            (pipeline_name,),
        )


def get_checkpoint_last_time(conn, pipeline_name: str = "log_pipeline"):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT last_time
            FROM etl_checkpoint
            WHERE pipeline_name = %s
            """,
            (pipeline_name,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def set_checkpoint_last_time(conn, last_time, pipeline_name: str = "log_pipeline") -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_checkpoint
            SET last_time = %s, updated_at = NOW()
            WHERE pipeline_name = %s;
            """,
            (last_time, pipeline_name),
        )


def touch_checkpoint(conn, pipeline_name: str = "log_pipeline") -> None:
    """Update updated_at without changing last_time."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_checkpoint
            SET updated_at = NOW()
            WHERE pipeline_name = %s;
            """,
            (pipeline_name,),
        )


def etl_run_start(conn, pipeline_name: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_run (pipeline_name, status)
            VALUES (%s, 'RUNNING')
            RETURNING run_id;
            """,
            (pipeline_name,),
        )
        return str(cur.fetchone()[0])


def etl_run_finish(
    conn,
    run_id: str,
    *,
    status: str,
    logs_processed: int = 0,
    error_message: Optional[str] = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_run
            SET finished_at = NOW(),
                status = %s,
                logs_processed = %s,
                error_message = %s
            WHERE run_id = %s;
            """,
            (status, int(logs_processed), error_message, str(run_id)),
        )



