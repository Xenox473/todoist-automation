from reclaim_sdk.models.task import ReclaimTask
from datetime import datetime, timedelta

class SyncReclaim():
    # Check off completed tasks in Reclaim
    # Runs every Monday?
    # Sync tasks that have a due date that is not today (Update it daily)
    # Sync tasks that have a priority and no due date
    # 1. P1 Gets top priority and due at the end of the week (Sunday)
    # 2. P2 is due at the end of the week (Sunday)
    # 3. P3 is due at the end of the month
    # Updates rollover tasks
    # Update reclaim tasks as completed if they are completed in Todoist
    # Use description to store the task ids in Reclaim
    def __init__(self, todoist_api):
        self.todoist_api = todoist_api
        self.today = datetime.today()
        self.projects = self.todoist_api.get_projects()
        self.timeblocking = list(filter(lambda x: x.name == "Timeblocking", self.projects))[0]
        self.personal = list(filter(lambda x: x.name == "Personal", self.projects))[0]
        self.school = list(filter(lambda x: x.name == "School", self.projects))[0]

    def get_root_project_id(self, task):
        project_id = task.project_id
        while True:
            if project_id in [self.timeblocking.id, self.personal.id, self.school.id]:
                return project_id
            else:
                project_id = list(filter(lambda x: x.id == project_id, self.projects))[0].parent_id
        
    def create_reclaim_task(self, todoist_task, reclaim_task = None):
        meassage = "Updated" if reclaim_task is not None else "Created"

        if reclaim_task is None:
            reclaim_task = ReclaimTask()

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

        # reclaim_task.min_work_duration = 1
        # reclaim_task.max_work_duration = 2

        reclaim_task.description = todoist_task.id
        
        reclaim_task.priority = todoist_task.priority

        project_id = self.get_root_project_id(todoist_task)
        reclaim_task.is_work_task = project_id == self.school.id

        if todoist_task.due is not None:
            reclaim_task.due_date = datetime.strptime(todoist_task.due.date, "%Y-%m-%d") + timedelta(days=1)
            if todoist_task.priority == 1:
                reclaim_task.start_date = self.today
            else:
                reclaim_task.start_date = datetime.strptime(todoist_task.due.date, "%Y-%m-%d") - timedelta(days=2)
        elif todoist_task.priority == 4:
            reclaim_task.due_date = datetime.now() + timedelta(days = 6 - self.today.weekday())
            reclaim_task.start_date = self.today
        elif todoist_task.priority == 3:
            reclaim_task.due_date = datetime.now() + timedelta(days = 6 - self.today.weekday())
            reclaim_task.start_date = datetime.now() + timedelta(days = 6 - self.today.weekday()) - timedelta(days=4)
        else:
            # End of the month or end of next month if in last week
            if self.today.day > 24:
                reclaim_task.due_date = datetime.now() + timedelta(days = 30 - self.today.day) + timedelta(days=30)
            else:
                reclaim_task.due_date = datetime.now() + timedelta(days = 30 - self.today.day)

            reclaim_task.start_date = datetime.now()
        
        reclaim_task.save()
        print(meassage + " Reclaim task: " + todoist_task.content + " " + reclaim_task.due_date.strftime("%Y-%m-%d"))
        return True
    
    def grab_todoist_tasks(self):
        # Grab all tasks that are non recurring tasks and have a due date that is not today
        tasks = list(filter(lambda x: x.due is not None and x.due.is_recurring is False and x.project_id != self.timeblocking.id, self.todoist_api.get_tasks()))
        # Grab all tasks that do not have a due date but have a priority
        tasks += list(filter(lambda x: x.due is None and x.priority > 1 and x.parent_id is None, self.todoist_api.get_tasks()))
        return tasks
    
    def cleanup_reclaim_tasks(self, reclaim_tasks, todoist_tasks):
        # Delete tasks that are in Reclaim but not in Todoist
        for task in reclaim_tasks:
            if task.description not in map(lambda x: x.id, todoist_tasks):
                # Mark tasks as completed in Reclaim if they are completed in Todoist
                todoist_task = self.todoist_api.get_task(task.description)
                if todoist_task is not None and todoist_task.is_completed:
                    task.mark_complete()
                    print("Completed Reclaim task: " + task.name)
                else:
                    print("Deleted Reclaim task: " + task.name)
                    task.delete()
        return
    
    def sync(self):
        # For each task, check if it exists in Reclaim, if not, create it
        reclaim_tasks = ReclaimTask.search()
        todoist_tasks = self.grab_todoist_tasks()

        self.cleanup_reclaim_tasks(reclaim_tasks, todoist_tasks)

        for task in todoist_tasks:
            if task.id not in map(lambda x: x.description, reclaim_tasks):
                self.create_reclaim_task(task)
            else:
                reclaim_task = list(filter(lambda x: x.description == task.id, reclaim_tasks))[0]
                self.create_reclaim_task(task, reclaim_task)
        return

    def delete_tasks(self):
        tasks = ReclaimTask.search()
        for task in tasks:
            task.delete()
        return
    
    