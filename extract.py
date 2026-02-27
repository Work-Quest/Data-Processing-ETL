import requests

from config import BACKEND_LOG_ENDPOINT, BACKEND_API_KEY, BATCH_SIZE


def fetch_logs(last_id: int):
    """
    Fetch logs from backend starting after `last_id`.

    Expects BACKEND_LOG_ENDPOINT to return JSON array of log objects, each containing an `id` field.
    """
    if not BACKEND_LOG_ENDPOINT:
        raise RuntimeError("BACKEND_LOG_ENDPOINT is not set")

    headers = {}
    if BACKEND_API_KEY:
        # Be permissive about header conventions used by different backends.
        headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"
        headers["X-API-Key"] = BACKEND_API_KEY

    params = {"after_id": last_id, "limit": BATCH_SIZE}

    resp = requests.get(
        BACKEND_LOG_ENDPOINT,
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError("Expected backend response to be a JSON array of logs")

    return data


