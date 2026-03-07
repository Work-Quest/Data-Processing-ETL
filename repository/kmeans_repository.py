from __future__ import annotations


def fetch_active_kmeans_blobs(conn):
    """
    Returns (run_id:str, model_blob:bytes, scaler_blob:bytes|None) for the active model.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.run_id::text, m.model_blob, m.scaler_blob
            FROM kmeans_run r
            JOIN kmeans_model m ON m.run_id = r.run_id
            WHERE r.is_active = TRUE
            LIMIT 1
            """
        )
        row = cur.fetchone()
    if not row:
        return None, None, None
    return row[0], row[1], row[2]


