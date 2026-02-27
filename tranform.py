import pandas as pd


def build_features(logs):
    df = pd.DataFrame(logs)

    if df.empty:
        return None

    grouped = df.groupby("user_id").agg({
        "completion_time": "mean",
        "delay_time": "mean",
        "complexity_score": "mean",
        "quality_score": "mean",
        "task_id": "count"
    }).reset_index()

    grouped.rename(columns={
        "task_id": "tasks_completed",
        "completion_time": "avg_completion_time",
        "delay_time": "avg_delay_time",
        "complexity_score": "avg_complexity",
        "quality_score": "quality_score_mean",
    }, inplace=True)

    return grouped