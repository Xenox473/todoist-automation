import todoist
import os

class Task(object):
    def __init__(self, task):
        self.task = task

    def remove_label(self, label=None):
        if label:
            self.task['labels'].remove(label)
        else:
            self.task.update(labels=[])
        return self.task

class Todoist(object):
    def __init__(self):
        self.api = todoist.TodoistAPI(self.get_token())
        self.api.sync()
    
    def get_token(self):
        token = os.getenv("TODOIST_API_KEY")
        if not token:
            raise Exception("Please set the API token in environment variable.")
        return token
    
    def get_label(self, label):
        return list(filter(lambda x: x['name'] == label, self.api.labels.all()))[0]

    def get_tasks_by_label(self, label):
        all_tasks = self.api.items.all()
        specific_tasks = list(filter(lambda task: label['id'] in task['labels'], all_tasks))            
        return specific_tasks
    
    def reset_this_week_label(self):
        this_week_label = self.get_label('This_Week')
        this_week_tasks = self.get_tasks_by_label(this_week_label)
        this_week_tasks = list(filter(lambda task: task['due'] is None, this_week_tasks))
        print('Clearing {} tasks from next actions.'.format(len(this_week_tasks)))
        for task in this_week_tasks:
            Task(task).remove_label(this_week_label['id'])
            self.api.items.update(task['id'], **task.__dict__['data'])
        self.api.commit()

def main():
    doist = Todoist()
    doist.reset_this_week_label()

if __name__ == "__main__":
    main()