from datetime import date, datetime, timedelta

def _to_date(x):
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    # if it's a string ISO datetime
    return datetime.fromisoformat(str(x)).date()

def work_load_calculate(log, data, etl_checkpoint_date: date, today: date | None = None):
    """
    Incremental work load array for [etl_checkpoint_date..today].
    Each index is the COUNT of tasks completed that day.
    (This is additive across ETL runs.)
    """
    completed_logs = log.get("complete_task_log") or []
    if today is None:
        today = date.today()

    # build result array for [etl_checkpoint_date .. today]
    n_days = (today - etl_checkpoint_date).days + 1
    if n_days <= 0:
        return []

    counts = [0] * n_days

    for item in completed_logs:
        d = item.created_at.date()
        if d < etl_checkpoint_date or d > today:
            continue
        idx = (d - etl_checkpoint_date).days
        counts[idx] += 1

    return counts