from checkpoint import get_last_checkpoint, update_checkpoint
from extract import fetch_logs
from transform import build_features
from load import upsert_features
from train import train_kmeans


def run_pipeline():
    last_id = get_last_checkpoint()

    while True:
        logs = fetch_logs(last_id)

        if not logs:
            break

        features = build_features(logs)

        if features is not None:
            upsert_features(features)

        last_id = logs[-1]["id"]
        update_checkpoint(last_id)

    print("ETL completed")


def run_training():
    train_kmeans()
    print("Training completed")


if __name__ == "__main__":
    run_pipeline()
    run_training()