from transform.diligence_calculation import diligence_increment_counts
from transform.work_load_calculation import work_load_calculate
from transform.work_speed_calculation import work_speed_calculate
from datetime import date
from transform.team_calculation import team_increment_counts


def transform(data, etl_checkpoint_date: date):
    """
    Incremental transform step: compute per-user increments for the window
    [etl_checkpoint_date..today].

    Returns:
      - increments: dict[project_member_id -> dict]
      - logs_processed: int
    """

    increments = {}
    for user, log in data.items():
        mid = str(user)
        work_speed_inc = work_speed_calculate(log, data, etl_checkpoint_date)
        work_load_inc = work_load_calculate(log, data, etl_checkpoint_date)
        project_id, p1, p2, p3, p4 = diligence_increment_counts(log)
        (
            project_id_team,
            assigned_inc,
            created_inc,
            completed_inc,
            deleted_inc,
            buff_inc,
            debuff_inc,
        ) = team_increment_counts(log)

        # prefer diligence project_id but fallback to team project_id
        project_id = project_id or project_id_team

        increments[mid] = {
            "project_member_id": mid,
            "project_id": str(project_id) if project_id else None,
            "window_start_date": etl_checkpoint_date,
            "work_load_inc": work_load_inc,
            "work_speed_inc": work_speed_inc,
            "diligence_p1_inc": p1,
            "diligence_p2_inc": p2,
            "diligence_p3_inc": p3,
            "diligence_p4_inc": p4,
            "team_buff_inc": buff_inc,
            "team_debuff_inc": debuff_inc,
            "task_assigned_inc": assigned_inc,
            "task_created_inc": created_inc,
            "task_completed_inc": completed_inc,
            "task_deleted_inc": deleted_inc,
        }

    # logs processed: count list items in each member's log dict
    logs_processed = 0
    for logs in data.values():
        for v in (logs or {}).values():
            if isinstance(v, list):
                logs_processed += len(v)

    return increments, logs_processed

