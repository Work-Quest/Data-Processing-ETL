from checkpoint import get_last_checkpoint, update_checkpoint
from extract import fetch_logs
from transform import build_features
from load import upsert_features
from train import train_kmeans


def run_pipeline():
    fetch_logs("2026-01-18 17:35:43.347119+00")
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