from db import get_connection


def get_last_checkpoint():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT last_log_id
        FROM etl_checkpoint
        WHERE pipeline_name = 'log_pipeline'
    """)

    row = cur.fetchone()
    conn.close()

    return row[0] if row else 0


def update_checkpoint(last_log_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE etl_checkpoint
        SET last_log_id = %s, updated_at = NOW()
        WHERE pipeline_name = 'log_pipeline'
    """, (last_log_id,))

    conn.commit()
    conn.close()