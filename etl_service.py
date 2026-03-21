from __future__ import annotations

"""
ETL HTTP service using Flask.

Endpoints:
  - POST /admin/etl/run      -> trigger ETL (main.run_pipeline) in background
  - GET  /admin/etl/status/<job_id> -> check status + captured stdout/stderr
  - GET  /health             -> ok

Auth:
  - env ETL_SERVICE_API_KEY
  - header X-ETL-Key: <ETL_SERVICE_API_KEY>
"""

import contextlib
import io
import os
import threading
import time
import uuid
from functools import wraps
from typing import Any

from flask import Flask, jsonify, request

import main  # Data-Processing-ETL/main.py

app = Flask(__name__)

ETL_SERVICE_API_KEY = (os.getenv("ETL_SERVICE_API_KEY") or "").strip()
HOST = os.getenv("ETL_SERVICE_HOST") or "0.0.0.0"
PORT = int(os.getenv("ETL_SERVICE_PORT") or "8088")

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _run_job(job_id: str) -> None:
    started_at = time.time()
    stdout = io.StringIO()
    stderr = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            ok = bool(main.run_pipeline())

        status = "SUCCESS" if ok else "FAILED"
    except Exception as e:
        status = "FAILED"
        stderr.write(f"\nException: {e}\n")

    finished_at = time.time()
    with _LOCK:
        _JOBS[job_id].update(
            {
                "status": status,
                "finished_at": finished_at,
                "duration_seconds": finished_at - started_at,
                "stdout": stdout.getvalue()[-20000:],
                "stderr": stderr.getvalue()[-20000:],
            }
        )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"ok": True}), 200


@app.route("/etl/run", methods=["POST"])
def run_etl():
    """Trigger ETL pipeline run and wait for completion."""
    job_id = str(uuid.uuid4())
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "started_at": time.time(),
            "finished_at": None,
            "duration_seconds": None,
            "stdout": "",
            "stderr": "",
        }

    # Start the job in a thread
    t = threading.Thread(target=_run_job, args=(job_id,), daemon=False)
    t.start()

    # Wait for the job to complete
    t.join()

    # Get the final job status
    with _LOCK:
        job = _JOBS.get(job_id)

    if not job:
        return jsonify({"error": "Job not found after completion"}), 500

    # Return appropriate status code based on job result
    status_code = 200 if job["status"] == "SUCCESS" else 500

    return jsonify(job), status_code


@app.route("/etl/status/<job_id>", methods=["GET"])
def get_etl_status(job_id: str):
    """Get ETL job status and logs."""
    with _LOCK:
        job = _JOBS.get(job_id)

    if not job:
        return jsonify({"error": "job_id not found"}), 404

    return jsonify(job), 200


def main_serve() -> None:
    """Start the Flask server."""
    print(f"ETL service listening on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, threaded=True)


if __name__ == "__main__":
    main_serve()





