from googleapiclient.discovery import build
from automate import *
import re

MIN_SCORE = 7

def create_task(title, score):
    doist = Todoist()
    # TODO: Create this into a model, so that we can store constant variables
    albums_project_id = list(filter(lambda x: x['name'] == 'Albums to listen to', doist.api.projects.all()))[0]['id']
    title = title.replace(' ALBUM REVIEW', '')
    item_content = "[{}] {}".format(score, title)
    project_items = list(filter(lambda x: x['project_id'] == albums_project_id, doist.api.items.all()))
    filt = filter(lambda x: x['content'] == item_content, project_items)
    print(item_content)
    print(project_items)
    print(list(filt))
    if any(filt):
        return False
    else:
        doist.api.add_item(item_content, project_id=albums_project_id)
        print("Created task for {}".format(title))
    return True

def fetch_score(description):
    try:
        score = re.search(r'\b(?P<score>\d{1}|10)\/10', description).groupdict()['score']
        return score
    except:
        return None

def playlist_video_scores(playlistId, youtube, album_limit=3):
    nextPageToken = None
    album_count = 0
    while album_count < album_limit:
        # Retrieve youtube video results
        pl_request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlistId,
            maxResults=50,
            pageToken=nextPageToken
        )
        pl_response = pl_request.execute()
  
        # Iterate through all response and get video description
        for item in pl_response['items']:
            # Check if we've hit the album limit
            if album_count >= album_limit:
                break
            title = item['snippet']['title']
            description = item['snippet']['description']
            score = fetch_score(description)
            if score and int(score) >= MIN_SCORE:
                if create_task(title, score):
                    album_count += 1

        nextPageToken = pl_response.get('nextPageToken')
        # Stop if we've reached the end
        if not nextPageToken:
            break

def fetch_playlists(channel_id, youtube):
    ch_request = youtube.channels().list(
            part='contentDetails',
            forUsername='theneedledrop',
            maxResults=50
        )
    ch_response = ch_request.execute()

    playlist_id = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    playlists = {'All Reviews': playlist_id}

    pl_request = youtube.playlists().list(
            part='snippet',
            channelId=channel_id,
            maxResults=50
        )
    pl_response = pl_request.execute()
    
    for item in pl_response['items']:
        playlist_title = item['snippet']['title']
        playlist_id = item['id']
        if "Reviews" in playlist_title and "Weekly" not in playlist_title:
            playlists[playlist_title] = playlist_id

    return playlists

def get_token():
    token = os.getenv("YOUTUBE_API_KEY")
    if not token:
        raise Exception("Please set the YOUTUBE API token in environment variable.")
    return token

if __name__ == "__main__":
    api_key = get_token()
    youtube = build('youtube', 'v3', developerKey=api_key)
    doist = Todoist()

    # If a todoist project doesn't exist, create one
    if not any(list(filter(lambda x: x['name'] == 'Albums to listen to', doist.api.projects.all()))):
        doist.api.projects.add('Albums to listen to')
        doist.api.commit()

    # Get channel_id for theneedledrop
    request = youtube.channels().list(
        part='id',
        forUsername='theneedledrop'
    )
    response = request.execute()
    channel_id = response['items'][0]['id']

    # Get playlists
    playlists = fetch_playlists(channel_id, youtube)

    # TODO: Add an option to select genre

    # For a playlist add albums todoist that match the minimum score
    playlist_id = playlists['All Reviews']
    playlist_video_scores(playlist_id, youtube)

    
