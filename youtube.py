from googleapiclient.discovery import build
from automate import *
import re

MIN_SCORE = 9

def create_task(title, score):
    doist = Todoist()
    albums_project_id = list(filter(lambda x: x['name'] == 'Albums to listen to', doist.api.projects.all()))[0]['id']
    title = title.replace(' ALBUM REVIEW', '')
    item_content = "[{}] {}".format(score, title)
    project_items = list(filter(lambda x: x['project_id'] == albums_project_id, doist.api.items.all()))
    if any(filter(lambda x: x['content'] == item_content, project_items)):
        return True
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

def playlist_video_scores(playlistId, youtube, album_limit=10):
    nextPageToken = None
    album_count = 0
    while True:
        # Check if we've hit the album limit
        if album_count > album_limit:
            break
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
            title = item['snippet']['title']
            description = item['snippet']['description']
            score = fetch_score(description)

            if score and int(score) >= MIN_SCORE:
                create_task(title, score)
                album_count += 1

        nextPageToken = pl_response.get('nextPageToken')
        
        # Stop if we've reached the end
        if not nextPageToken:
            break

def fetch_genres(channel_id, youtube):
    ch_request = youtube.channels().list(
            part='contentDetails',
            forUsername='theneedledrop',
            maxResults=50
        )
    ch_response = ch_request.execute()

    playlist_id = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    genres = {'All Reviews': playlist_id}

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
            genres[playlist_title] = playlist_id

    return genres

def get_token():
    token = os.getenv("YOUTUBE_API_KEY")
    if not token:
        raise Exception("Please set the YOUTUBE API token in environment variable.")
    return token

if __name__ == "__main__":
    api_key = get_token()
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Get channel_id for theneedledrop
    request = youtube.channels().list(
        part='id',
        forUsername='theneedledrop'
    )
    response = request.execute()
    channel_id = response['items'][0]['id']

    # Get playlist genres
    genres = fetch_genres(channel_id, youtube)

    # Add an option to select genre

    # For a playlist return all the scores and videos that match the minimum score
    playlist_id = genres['All Reviews']
    playlist_video_scores(playlist_id, youtube)

    