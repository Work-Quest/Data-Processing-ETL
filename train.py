import io
import uuid
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from datetime import datetime
from db import get_connection
from config import KMEANS_K


def train_kmeans():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM user_feature_daily", conn)

    if df.empty:
        conn.close()
        return

    feature_cols = [
        "tasks_completed",
        "avg_completion_time",
        "avg_delay_time",
        "avg_complexity",
        "quality_score_mean"
    ]

    X = df[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    kmeans = KMeans(n_clusters=KMEANS_K, random_state=42)
    kmeans.fit(X_pca)

    artifact = {
        "scaler": scaler,
        "pca": pca,
        "kmeans": kmeans,
        "feature_columns": feature_cols,
        "trained_at": datetime.utcnow()
    }

    buffer = io.BytesIO()
    joblib.dump(artifact, buffer)
    model_bytes = buffer.getvalue()

    run_id = str(uuid.uuid4())

    cur = conn.cursor()
    # Ensure only one active model at a time (migration enforces a unique index on active runs).
    cur.execute("UPDATE kmeans_run SET is_active = FALSE WHERE is_active = TRUE;")
    cur.execute(
        """
        INSERT INTO kmeans_run (run_id, trained_at, k, is_active)
        VALUES (%s, NOW(), %s, TRUE)
        """,
        (run_id, KMEANS_K),
    )
    cur.execute(
        """
        INSERT INTO kmeans_model (run_id, model_blob)
        VALUES (%s, %s)
        """,
        (run_id, model_bytes),
    )

    conn.commit()
    conn.close()