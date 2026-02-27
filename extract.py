import requests

from config import BACKEND_LOG_ENDPOINT, BACKEND_API_KEY, BATCH_SIZE


def fetch_logs(time_begin: str):
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

    params = {"time_begin_raw": time_begin}

    res = requests.get(
        f"{BACKEND_LOG_ENDPOINT}/api/internal/logs",
        headers=headers,
        params=params,
        timeout=30,
    )
    res.raise_for_status()

    data = res.json()
    print(data)
    # if data is None:
    #     return []
    # if not isinstance(data, list):
    #     raise ValueError("Expected backend response to be a JSON array of logs")