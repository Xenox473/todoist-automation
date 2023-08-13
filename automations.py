import random
import os
import sys

from datetime import datetime, timedelta
from todoist_api_python.api import TodoistAPI
from dotenv import dotenv_values
from sync_reclaim import SyncReclaim

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
    
    tasks = list(filter(lambda x: task_filter(x), api.get_tasks()))
    # Select five random tasks
    tasks = random.sample(tasks, 3)

    for task in tasks:
        task.labels.append('Review')
        api.update_task(task_id=task.id, labels=task.labels)

def reset_priorities(api, today):
    # Get all tasks that have a priority
    tasks = list(filter(lambda x: x.priority != 1 and x.due is not None and x.due.date == today.strftime("%Y-%m-%d"), api.get_tasks()))

    for task in tasks:
        api.update_task(task_id=task.id, priority=1)
    return True

if __name__ == "__main__":
    # get arguments
    arg = sys.argv[1]

    # If secrets.env exists, load it. Else, load environment variables
    if os.path.exists("secrets.env"):
        token = dotenv_values("secrets.env").get("TODOIST_API_KEY")
        os.environ["RECLAIM_TOKEN"] = dotenv_values("secrets.env").get("RECLAIM_TOKEN")
    else:
        token = os.environ.get("TODOIST_API_KEY")
    
    if not token:
        raise Exception("Please set the TODOIST API token in environment variable.")

    today = datetime.today()
    day = today.weekday()
    api = TodoistAPI(token)

    if arg == "todoist":
        # Reset This_Week label if Sunday
        if day == 6:
            reset_this_week(api)
            # Review tasks
            # review_tasks(api, today)

        # Reset priorities
        reset_priorities(api, today)
        
    elif arg == "reclaim":
        try:
            reclaim = SyncReclaim(api)
            reclaim.sync()
        except Exception as e:
            task_content = "Fix Reclaim Sync"
            tasks = list(filter(lambda x: x.content == task_content, api.get_tasks()))
            if len(tasks) == 0:
                task = api.add_task(
                    content=task_content,
                    due_string="today",
                    due_lang="en",
                    description=f"Error: {e}",
                    priority=3
                )
                print(task)
            else:
                print("Task already exists")
                print(e)
        # reclaim.delete_tasks()