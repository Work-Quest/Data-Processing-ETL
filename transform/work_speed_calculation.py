from datetime import date, timedelta


def work_speed_calculate(log, data, etl_checkpoint_date: date, today: date | None = None):
    """
    Incremental work speed array for [etl_checkpoint_date..today].
    Each index is the SUM of completion durations (minutes) for tasks completed that day.
    (This is additive across ETL runs.)
    """
    completed_logs = log.get("complete_task_log") or []
    if today is None:
        today = date.today()

    n_days = (today - etl_checkpoint_date).days + 1
    if n_days <= 0:
        return []

    per_day_sum = {}  # date -> sum_minutes
    for item in completed_logs:
        d = item.created_at.date()
        if d < etl_checkpoint_date or d > today:
            continue
        td = item.created_at - item.task_created_at
        minutes = int(td.total_seconds() // 60)
        per_day_sum[d] = per_day_sum.get(d, 0) + minutes

    result = []
    for i in range(n_days):
        day = etl_checkpoint_date + timedelta(days=i)
        result.append(per_day_sum.get(day, 0))

    return result