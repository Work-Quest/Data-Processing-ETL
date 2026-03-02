from datetime import date, datetime, timedelta

from utils import find_completed_task_by_task_id



def diligence_calculate(log, data):
    assigned_logs = log.get("assigned_task_log") or []
    if not assigned_logs:
        return None, None

    project_id = assigned_logs[0].project_id

    weight = {"1" : 0, "2": 0, "3": 0, "4": 0 }  # task_id -> (start_date, end_date_or_today)
    n = 0
    for item in assigned_logs:
        completed_log = find_completed_task_by_task_id(data, item.task_id)
        if completed_log:
            if completed_log.task_priority != "":
                weight[str(completed_log.task_priority)] += 1
                n += 1

    if n == 0:
        return 0, project_id

    score = ((weight["1"] * 1) + (weight["2"] * 2) + (weight["3"] * 3) + (weight["4"] * 4)) / n

    return score, project_id



