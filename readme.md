## Todoist Automation

- This repo contains a set of automated scripts I run on my personal todoist account. They run on a scheduled basis using the github workflows.

  - [automate.py](#automatepy)
  - [youtube.py](#youtubepy)
  - [Running the scripts](#running-the-scripts)

### automate.py
- This script defines the Todoist and Task class objects - personalized to fit my needs. I use a label called 'This_Week' which I use to label tasks I'd like to complete this week, but don't necessarily have a due date. `reset_this_week_label` removes the label every time it's run (every sunday)
- Requires your todoist API key

### youtube.py
- This script scrapes the youtube video descriptions for all of the needle drop reviews and adds three albums scoring 7 or higher to a new Todoist project tiled `'Albums to listen to'`.
- Requires your todoist api key and a youtube api key to run.

### Running the scripts
You can run the scripts locally or on a scheduled basis using github workflows. 
    To run it locally first run
    ```
    pip install requirements -r
    ```
    Then, set the environment variables like so:
    ```export YOUTUBE_API_KEY={insert api key here}
    export TODOIST_API_KEY={insert api key here}```

To run the script using github workflows, clone the repo and set the secret environment variables for `TODOIST_API_KEY` and `YOUTUBE_API_KEY`.
You can change the schedule by adjusting the crontab in the yml file. The pythonapp schedules `automate.py` while the youtubeapp schedules `youtube.py`