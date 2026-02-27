from db import get_connection
from datetime import datetime, timezone


def upsert_features(feature_df):
    conn = get_connection()
    cur = conn.cursor()

    feature_date = datetime.now(timezone.utc).date()

    for _, row in feature_df.iterrows():
        cur.execute("""
            INSERT INTO user_feature_daily (
                user_id,
                date,
                tasks_completed,
                avg_completion_time,
                avg_delay_time,
                avg_complexity,
                quality_score_mean
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                tasks_completed = EXCLUDED.tasks_completed,
                avg_completion_time = EXCLUDED.avg_completion_time,
                avg_delay_time = EXCLUDED.avg_delay_time,
                avg_complexity = EXCLUDED.avg_complexity,
                quality_score_mean = EXCLUDED.quality_score_mean
        """, (
            row["user_id"],
            feature_date,
            row["tasks_completed"],
            row["avg_completion_time"],
            row["avg_delay_time"],
            row["avg_complexity"],
            row["quality_score_mean"],
        ))

    conn.commit()
    conn.close()