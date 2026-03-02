from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from math import sqrt

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

def parse_t_score(calculated_data):
    # {project_id : {user: score, }}
    raw_score = {}
    for i in calculated_data:
        pid = str(i["project_id"])
        mid = str(i["user_id"])
        x = float(i["weight"])
        raw_score.setdefault(pid, {})[mid] = x

    # compute T-scores per project
    t_scores = {}  # {project_id: {member_id: t_score}}
    stats = {}  # optional: {project_id: {"mean":..., "std":...}}

    for pid, member_scores in raw_score.items():
        xs = list(member_scores.values())
        n = len(xs)
        if n == 0:
            t_scores[pid] = {}
            stats[pid] = {"mean": 0.0, "std": 0.0}
            continue

        mean = sum(xs) / n

        # population std (divide by n). If you want sample std, divide by (n-1) when n>1.
        var = sum((x - mean) ** 2 for x in xs) / n
        std = sqrt(var)

        stats[pid] = {"mean": mean, "std": std}

        if std == 0:
            # everyone same score -> all get 50
            t_scores[pid] = {mid: 50.0 for mid in member_scores}
        else:
            t_scores[pid] = {
                mid: 50.0 + 10.0 * ((x - mean) / std)
                for mid, x in member_scores.items()
            }

    return t_scores, stats