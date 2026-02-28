from extract import extract_data
from train import train_kmeans
from transform.transform import transform
from transform.work_speed_calculation import work_speed_calculate

def run_pipeline():
    build_member_log_data = extract_data("2026-01-18 17:35:43.347119+00")
    transform(build_member_log_data)
    # while True:
    #     logs = fetch_logs(last_id)
    #
    #     if not logs:
    #         break
    #
    #     features = build_features(logs)
    #
    #     if features is not None:
    #         upsert_features(features)
    #
    #     last_id = logs[-1]["id"]
    #     update_checkpoint(last_id)

    print("ETL completed")


def run_training():
    train_kmeans()
    print("Training completed")


if __name__ == "__main__":
    run_pipeline()