from datetime import date, datetime, timedelta

from utils import find_completed_task_by_task_id


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
    assigned_logs = log.get("assigned_task_log") or []
    if today is None:
        today = date.today()

    task_date = {}  # task_id -> (start_date, end_date_or_today)

    for item in assigned_logs:
        completed_log = find_completed_task_by_task_id(data, item.task_id)

        start_date = _to_date(item.created_at)
        end_date = _to_date(completed_log.created_at) if completed_log else None

        task_date[item.task_id] = (start_date, end_date)

    # build result array for [etl_checkpoint_date .. today]
    n_days = (today - etl_checkpoint_date).days + 1
    if n_days <= 0:
        return []

    counts = [0] * n_days

    for i in range(n_days):
        current_day = etl_checkpoint_date + timedelta(days=i)

        for task_id, (start_date, end_date) in task_date.items():
            if start_date is None:
                continue

            # task is active until end_date; if not completed, treat as active until today
            effective_end = end_date or today

            # count as 1 if current_day is inside [start_date, effective_end]
            if start_date <= current_day <= effective_end:
                counts[i] += 1
    return counts