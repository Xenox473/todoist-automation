import os

from datetime import datetime
from todoist_api_python.api import TodoistAPI

def reset_this_week():
    api = TodoistAPI(token)
    ## Get all tasks associated with the label
    tasks = list(filter(lambda x: 'This_Week' in x.labels, api.get_tasks()))
    for task in tasks:
        api.update_task(task_id=task.id, labels=list(filter(lambda x: x != "This_Week", task.labels)))
    return True

if __name__ == "__main__":
    token = os.getenv("TODOIST_API_KEY")
    if not token:
        raise Exception("Please set the TODOIST API token in environment variable.")

    today = datetime.today()
    day = today.weekday()

    # Reset This_Week label if Sunday
    if day == 6:
        reset_this_week()
