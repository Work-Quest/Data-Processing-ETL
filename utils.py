from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

def find_completed_task_by_task_id(data,task_id):
    """
    data: { project_member_id: { 'complete_task_log': [CompleteTasklLogDTO, ...], ... }, ... }
    Returns list of (project_member_id, complete_task_dto) for matching task_id.
    """
    for member_id, logs in data.items():
        completed = logs.get("complete_task_log") or []
        for dto in completed:
            if str(getattr(dto, "task_id", "")) == str(task_id):
                return dto
    return None

def _parse_dt(value: Any) -> datetime:
    """
    Backend returns ISO strings for created_at / deadline / etc.
    Make it resilient to both 'Z' and '+00:00' formats.
    """
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    s = str(value).strip()
    # Django often serializes as "2026-02-28T12:34:56.123456Z"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        # ensure tz-aware (default to UTC if missing)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)