import random
import os
import sys

from datetime import datetime, timedelta
from todoist_api_python.api import TodoistAPI
from dotenv import dotenv_values
from reclaim_sdk.models.task import ReclaimTask
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

def create_reclaim_task(todoist_task, today):
    with ReclaimTask() as reclaim_task:
        reclaim_task.name = todoist_task.content
        # All durations are set in hours
        # Set using labels
        if todoist_task.labels is not None:
            durations = list(filter(lambda x: x in ["15", "30", "60", "120"], todoist_task.labels))
            if len(durations) == 0:
                reclaim_task.duration = 0.5
            else:
                durations = list(map(lambda x: round(int(x)/60, 2), durations))
                duration = sum(durations)
                reclaim_task.duration = duration
        else: 
            reclaim_task.duration = 0.5

        reclaim_task.min_work_duration = 0.15
        reclaim_task.max_work_duration = 2
        
        reclaim_task.start_date = datetime.now()
        reclaim_task.priority = todoist_task.priority

        if todoist_task.due is not None:
            reclaim_task.due_date = datetime.strptime(todoist_task.due.date, "%Y-%m-%d") + timedelta(days=1)
        elif todoist_task.priority == 1:
            reclaim_task.due_date = datetime.now() + timedelta(days = 6 - today.weekday())
    
    print("Created Reclaim task: " + todoist_task.content)
    return True

def sync_reclaim(api, today):
    # Check off completed tasks in Reclaim
    # Runs every Monday?
    # Sync tasks that have a due date that is not today (Update it daily)
    todoist_tasks = list(filter(lambda x: x.due is not None and x.due.date != today.strftime("%Y-%m-%d"), api.get_tasks()))
    # For each task, check if it exists in Reclaim, if not, create it
    reclaim_tasks = ReclaimTask.search()
    for task in todoist_tasks:
        if task.content not in map(lambda x: x.name, reclaim_tasks):
            create_reclaim_task(task, today)
        else:
            # Update the task
            pass
    # Sync tasks that have a priority and no due date
    # 1. P1 Gets top priority and due at the end of the week (Sunday)
    # 2. P2 is due at the end of the week (Sunday)
    # 3. P3 is due at the end of the month
    # Updates rollover tasks
    # Update reclaim tasks as completed if they are completed in Todoist
    # Use notes to store the task ids in Reclaim


    return

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
        review_tasks(api, today)
        # Reset priorities
        reset_priorities(api, today)
        
    elif arg == "reclaim":
        reclaim = SyncReclaim(api)
        reclaim.sync()
        # reclaim.delete_tasks()