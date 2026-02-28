from transform.work_load_calculation import work_load_calculate
from transform.work_speed_calculation import work_speed_calculate
from utils import _parse_dt


def transform(data):
    for user, log in data.items():
        print(user)
        work_speed = work_speed_calculate(log)
        work_load = work_load_calculate(log,data, _parse_dt("2026-02-15T10:39:30.044081Z").date())
