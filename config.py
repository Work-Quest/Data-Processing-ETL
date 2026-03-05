import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_LOG_ENDPOINT = os.getenv("BACKEND_LOG_ENDPOINT")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")

FEATURE_DB_URL = os.getenv("FEATURE_DB_URL")

BATCH_SIZE = 1000
KMEANS_K = 4
TRAIN_WINDOW_DAYS = 30

# Optional: local artifact-based team role model (no MLflow server needed).
# Copy artifacts (kmeans_model.pkl, scaler.pkl, role_mapping.json, feature_names.json)
# into this directory inside the ETL image.
TEAM_ROLE_ARTIFACT_DIR = os.getenv("TEAM_ROLE_ARTIFACT_DIR")