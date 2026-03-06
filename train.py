from __future__ import annotations

# NOTE: Skeleton only. Fill in TODOs yourself.

import io
import uuid
from datetime import datetime

import joblib
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os
import json
from db import get_connection
from config import KMEANS_K
from datetime import timedelta

def persist_kmeans_model_to_db(
    conn,
    *,
    model_bytes: bytes,
    k: int,
    inertia: float | None = None,
    silhouette_score: float | None = None,
    window_start=None,
    window_end=None,
) -> str:
    """
    Save the trained KMeans artifact into DB tables:
      - kmeans_run (metadata; mark as active)
      - kmeans_model (blob)

    Returns run_id (str).
    """
    # psycopg2 can't reliably adapt numpy scalars (e.g., np.float64). Coerce to builtin types.
    inertia_val = float(inertia) if inertia is not None else None
    silhouette_val = float(silhouette_score) if silhouette_score is not None else None

    # window_start/window_end columns are DATE in DB; accept datetime/date/None.
    if hasattr(window_start, "date"):
        window_start = window_start.date()
    if hasattr(window_end, "date"):
        window_end = window_end.date()

    run_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        # Ensure only one active model at a time.
        cur.execute("UPDATE kmeans_run SET is_active = FALSE WHERE is_active = TRUE;")
        cur.execute(
            """
            INSERT INTO kmeans_run (
                run_id,
                trained_at,
                window_start,
                window_end,
                k,
                inertia,
                silhouette_score,
                is_active
            )
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, TRUE)
            """,
            (
                run_id,
                window_start,
                window_end,
                int(k),
                inertia_val,
                silhouette_val,
            ),
        )
        cur.execute(
            """
            INSERT INTO kmeans_model (run_id, model_blob)
            VALUES (%s, %s)
            """,
            (run_id, model_bytes),
        )
    conn.commit()
    return run_id


def preprocess_data(df):
    """Preprocess the input DataFrame."""
    try:
        df["work_load_per_day"] = df["work_load_per_day"].apply(json.loads)
        df["avg_workload"] = df["work_load_per_day"].apply(lambda x: sum(x) / len(x) if x else 0)
        df["work_speed"] = df["work_speed"].apply(lambda s: json.loads(s) if s else [])
        df["avg_work_speed"] = df["work_speed"].apply(lambda x: (sum(x) / len(x)) if x else 0.0)
        df["overall_quality_score"] = df["work_quality"].fillna(0.0)
        df["strength"] = df["strength"].fillna("UNKNOWN").astype(str)
        label_encoder = LabelEncoder()
        df["work_category_encoded"] = label_encoder.fit_transform(df["strength"])
    except Exception as e:
        print(f"Error in preprocessing data: {e}")
        raise
    return df


def standardize_features(df, feature_cols):
    """Standardize the features using StandardScaler."""
    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[feature_cols])
    except Exception as e:
        print(f"Error in standardizing features: {e}")
        raise
    return X_scaled, scaler


def get_cluster_summary(df):
    """Generate a summary of the clusters."""
    try:
        # Ensure numeric dtypes for aggregation
        for col in ["avg_workload", "team_work", "avg_work_speed", "overall_quality_score"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        profile = df.groupby("cluster")[[
            "avg_workload", "team_work", "avg_work_speed", "overall_quality_score"
        ]].mean()
        counts = df["cluster"].value_counts().sort_index()
        summary = profile.copy()
        summary["count"] = counts
    except Exception as e:
        print(f"Error in generating cluster summary: {e}")
        raise
    return summary


class TeamRoleClusteringModel:
    """
    Custom model class for K-means clustering and role assignment.

    Attributes:
        kmeans (KMeans): Trained KMeans model.
        scaler (StandardScaler): StandardScaler for feature scaling.
        role_mapping (dict): Mapping of cluster labels to roles.
        feature_names (list): List of feature names used for training.
    """

    def __init__(self, kmeans=None, scaler=None, role_mapping=None, feature_names=None):
        self.kmeans = kmeans
        self.scaler = scaler
        self.role_mapping = role_mapping
        self.feature_names = feature_names

    def predict(self, df):
        """
        Predict the role of team members based on their features.
        """
        try:
            if self.feature_names is None:
                raise ValueError("Model not loaded. Call load() first.")

            X = df[self.feature_names].values
            X_scaled = self.scaler.transform(X)
            clusters = self.kmeans.predict(X_scaled)

            roles = [self.role_mapping.get(int(c), "Unknown") for c in clusters]

            return roles

        except Exception as e:
            print(f"Error during prediction: {e}")
            raise

def explain_assignment_verbose(df, cluster_summary):
    """Explain cluster assignment with a SHAP-like textual style."""
    explanations = []

    for _, row in df.iterrows():
        cluster = row["cluster"]
        role = row["assigned_role"]
        cluster_info = cluster_summary.loc[cluster]
        reasoning = {
            0: "Balanced but unremarkable — contributes, but may lack initiative",
            1: "High quality and teamwork, but very slow — may hold up the group",
            2: "Works quickly but produces low quality",
            3: "Very fast but extremely low quality and teamwork — risky contributor",
            4: "Takes on everything, delivers high quality",
            5: "Reliable and collaborative, though slow-moving",
            6: "Mediocre in all areas — lacks standout traits"
        }

        lines = []
        for feature in ["avg_workload", "team_work", "avg_work_speed", "overall_quality_score"]:
            diff = row[feature] - cluster_info[feature]
            sign = "+" if diff > 0 else "–"
            lines.append(f"{sign} {feature}: {diff:+.2f} vs cluster avg")

        lines.append(f"⇒ Overall pattern matches “{role}”: {reasoning.get(cluster, 'No reasoning available')}")
        explanations.append("\n".join(lines))

    df["shap_style_explanation"] = explanations
    return df


def train_kmeans_if_new_data(*, should_train: bool) -> None:
    """
    Skeleton: train a GLOBAL KMeans model from user_feature_daily when ETL has new data.

    Columns to use (as per your spec):
      - work_load_per_day (JSON array text)
      - team_work (float)
      - strength (string)
      - work_speed (JSON array text)
      - diligence (float)
      - work_quality (float)
    """
    if not should_train:
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM user_feature_daily;")
            if cur.fetchone()[0] < KMEANS_K:
                return

        df = pd.read_sql(
            """
            SELECT
              project_member_id,
              work_load_per_day,
              team_work,
              strength,
              work_speed,
              diligence,
              work_quality
            FROM user_feature_daily
            """,
            conn,
        )

        if df.empty or len(df) < KMEANS_K:
            return

        try:

            df = preprocess_data(df)
            features = ["avg_workload", "team_work", "avg_work_speed", "diligence", "overall_quality_score"]
            X_scaled, scaler = standardize_features(df, features)

            # Train KMeans
            kmeans = KMeans(n_clusters=KMEANS_K, random_state=42)
            df["cluster"] = kmeans.fit_predict(X_scaled)

            final_score = silhouette_score(X_scaled, df["cluster"])
            print(f"Final Silhouette Score: {final_score}")

            # Role mapping
            role_mapping = {
                0: "Balancer",
                1: "Perfectionist",
                2: "Task finisher",
                3: "Lone Wolf",
                4: "Leader",
                5: "Helper",
                6: "Genelarist"
            }

            df["assigned_role"] = df["cluster"].map(role_mapping)

            # Explain result
            # Ensure numeric dtypes for aggregation
            for col in ["avg_workload", "team_work", "avg_work_speed", "overall_quality_score"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

            cluster_summary = df.groupby("cluster")[[
                "avg_workload",
                "team_work",
                "avg_work_speed",
                "overall_quality_score"
            ]].mean()

            df = explain_assignment_verbose(df, cluster_summary)

            # Create model wrapper
            model = TeamRoleClusteringModel(
                kmeans=kmeans,
                scaler=scaler,
                role_mapping=role_mapping,
                feature_names=features
            )

            # serialize artifact bytes
            model_buffer = io.BytesIO()
            joblib.dump(model, model_buffer)
            model_bytes = model_buffer.getvalue()

            persist_kmeans_model_to_db(
                conn,
                model_bytes=model_bytes,
                k=KMEANS_K,
                inertia=float(kmeans.inertia_),
                silhouette_score=final_score,
                window_start=None,
                window_end=datetime.now().date(),
            )

        except Exception as e:
            print(f"Error during the main execution: {e}")
            raise

    finally:
        conn.close()


def train_kmeans() -> None:
    """
    Backwards-compatible entry point used by main.run_training().\n
    Skeleton: always attempts training when called directly.\n
    """
    train_kmeans_if_new_data(should_train=True)