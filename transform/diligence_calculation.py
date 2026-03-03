def diligence_increment_counts(log):
    """
    Incremental diligence counts based on completed tasks in this ETL window.
    Returns: (project_id, p1, p2, p3, p4)
    """
    completed_logs = log.get("complete_task_log") or []
    if not completed_logs:
        return None, 0, 0, 0, 0

    project_id = completed_logs[0].project_id
    p1 = p2 = p3 = p4 = 0

    for item in completed_logs:
        pr = str(getattr(item, "task_priority", "") or "")
        if pr == "1":
            p1 += 1
        elif pr == "2":
            p2 += 1
        elif pr == "3":
            p3 += 1
        elif pr == "4":
            p4 += 1

    return project_id, p1, p2, p3, p4



