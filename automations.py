from datetime import datetime, timedelta
from todoist_api_python.api import TodoistAPI
from dotenv import dotenv_values

def reset_this_week(api):
    ## Get all tasks associated with the label
    tasks = list(filter(lambda x: 'This_Week' in x.labels, api.get_tasks()))
    for task in tasks:
        api.update_task(task_id=task.id, labels=list(filter(lambda x: x != "This_Week", task.labels)))
    return True

def review_tasks(api, today):
    ## Get 5 tasks that do not have a due date and have been created more than 3 months ago
    def task_filter(task):
        # Separatedinto a multi-line if statement for readability
        if 'Review' not in task.labels:
            if task.due is None:
                if task.parent_id is None:
                    if datetime.strptime(task.created_at.split("T")[0], '%Y-%m-%d') < today - timedelta(days=90):
                        return True
        return False
    
    tasks = list(filter(lambda x: task_filter(x), api.get_tasks()))[0:5]
    for task in tasks:
        task.labels.append('Review')
        api.update_task(task_id=task.id, labels=task.labels)

if __name__ == "__main__":
    secrets = dotenv_values("secrets.env")

    # Retrieve API token from environment variable
    token = secrets.get("TODOIST_API_KEY")
    
    if not token:
        raise Exception("Please set the TODOIST API token in environment variable.")

    today = datetime.today()
    day = today.weekday()
    api = TodoistAPI(token)

    # Reset This_Week label if Sunday
    if day == 6:
        reset_this_week(api)

    # Review tasks every other 
    review_tasks(api, today)