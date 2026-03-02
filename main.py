from extract import extract_data
from train import train_kmeans
from transform.transform import transform
from db import get_connection

from repository.etl_repository import (
    ensure_checkpoint_row,
    etl_run_finish,
    etl_run_start,
    touch_checkpoint,
)
from repository.user_feature_profile_repository import upsert_user_feature_daily

def run_pipeline():
    build_member_log_data = extract_data("2026-01-18 17:35:43.347119+00")
    rows, logs_processed = transform(build_member_log_data)

    conn = get_connection()
    run_id = None
    pipeline_name = "log_pipeline"
    try:
        ensure_checkpoint_row(conn, pipeline_name)
        run_id = etl_run_start(conn, pipeline_name)

        upsert_user_feature_daily(rows, connection=conn)

        touch_checkpoint(conn, pipeline_name)
        etl_run_finish(conn, run_id, status="SUCCESS", logs_processed=logs_processed)
        conn.commit()
    except Exception as e:
        if run_id:
            etl_run_finish(conn, run_id, status="FAILED", logs_processed=0, error_message=str(e))
            conn.commit()
        raise
    finally:
        conn.close()
    print("ETL completed")


def run_training():
    train_kmeans()
    print("Training completed")


if __name__ == "__main__":
    run_pipeline()