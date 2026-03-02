from transform.diligence_calculation import diligence_calculate
from transform.work_load_calculation import work_load_calculate
from transform.work_speed_calculation import work_speed_calculate
from utils import _parse_dt, parse_t_score


def transform(data):
    # array for calculate t-score
    diligence_array = []
    for user, log in data.items():
        print(user)
        work_speed = work_speed_calculate(log)
        work_load = work_load_calculate(log, data, _parse_dt("2026-02-15T10:39:30.044081Z").date())
        diligence, project_id = diligence_calculate(log, data)
        if diligence:
            diligence_array.append({"project_id": project_id, "user_id": user, "weight": diligence})

    t_score, stat = parse_t_score(diligence_array)

    print(t_score)