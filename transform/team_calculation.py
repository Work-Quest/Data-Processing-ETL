def team_increment_counts(log):
    """
    Incremental teamwork counters from logs in the current ETL window.

    Task-related logs:
      - create_task_log
      - assigned_task_log
      - complete_task_log
      - delete_task_log

    Team-interaction logs:
      - buff_log + buffed_log
      - debuff_log + debuffed_log

    Returns:
      (project_id, assigned, created, completed, deleted, buff, debuff)
    """
    assigned_logs = log.get("assigned_task_log") or []
    created_logs = log.get("create_task_log") or []
    completed_logs = log.get("complete_task_log") or []
    deleted_logs = log.get("delete_task_log") or []

    buff_logs = (log.get("buff_log") or []) + (log.get("buffed_log") or [])
    debuff_logs = (log.get("debuff_log") or []) + (log.get("debuffed_log") or [])

    # Best-effort project_id discovery from any available log
    project_id = None
    for group in (assigned_logs, created_logs, completed_logs, deleted_logs, buff_logs, debuff_logs):
        if group:
            project_id = getattr(group[0], "project_id", None)
            if project_id:
                break

    return (
        project_id,
        len(assigned_logs),
        len(created_logs),
        len(completed_logs),
        len(deleted_logs),
        len(buff_logs),
        len(debuff_logs),
    )


