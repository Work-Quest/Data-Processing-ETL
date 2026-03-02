
def work_speed_calculate(log):
    logs = log["complete_task_log"]
    if logs == []:
       return None
    work_speed_per_day_dict = {}
    work_speed_per_day = []
    for log in logs:
        completed_time = log.created_at
        speed =  completed_time - log.task_created_at
        minutes = int(speed.total_seconds() // 60)  # floor minutes
        day = completed_time.date()
        if day not in work_speed_per_day_dict:
            work_speed_per_day_dict[day] = []
        work_speed_per_day_dict[day].append(minutes)

    # print(work_speed_per_day_dict)

    for i in work_speed_per_day_dict.values():
        work_speed_per_day.append(sum(i)/len(i))
    return str(work_speed_per_day)
