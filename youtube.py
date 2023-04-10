import os
import re

from todoist_api_python.api import TodoistAPI
from dotenv import dotenv_values

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

MIN_SCORE = 7

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1vim8hXwLoYF0zTDswatSq9UNwgpNDRSr_VK8h8DU0ZU'
SAMPLE_RANGE_NAME = 'Sheet1'

def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists('token.json.gpg'):
        # Decrypt the file
        print("Decrypting token.json.gpg")
        os.system('gpg --quiet --batch --yes --decrypt --passphrase="$GPG_PASSPHRASE" --output token.json token.json.gpg')

    if os.path.exists('credentials.json.gpg'):
        # Decrypt the file
        print("Decrypting credentials.json.gpg")
        os.system('gpg --quiet --batch --yes --decrypt --passphrase="$GPG_PASSPHRASE" --output credentials.json credentials.json.gpg')

    print(os.path.exists('credentials.json'))
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_albums_listened_to(creds):
    albums = []
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        for row in values:
            # Only print if row 1 equals to Albums to listen to
            if row[1] == 'Albums to listen to':
                albums.append(row[0])

    except HttpError as err:
        print(err)

    return albums

def create_task(title, score, albums_listened_to):
    doist = TodoistAPI(get_tokens()[0])
    # TODO: Create this into a model, so that we can store constant variables
    albums_project_id = list(filter(lambda x: x.name == 'Albums to listen to', doist.get_projects()))[0].id
    title = title.replace(' ALBUM REVIEW', '')
    item_content = "[{}] {}".format(score, title)

    if item_content in albums_listened_to:
        return False
    
    project_items = list(filter(lambda x: x.project_id == albums_project_id, doist.get_tasks()))
    filt = list(filter(lambda x: x.content == item_content, project_items))
    
    if any(filt):
        return False
    else:
        doist.add_task(item_content, project_id=albums_project_id)
        print("Created task for {}".format(title))
    return True

def fetch_score(description):
    try:
        score = re.search(r'\b(?P<score>\d{1}|10)\/10', description).groupdict()['score']
        return score
    except:
        return None

def playlist_video_scores(playlistId, youtube, albums_listened_to=[], album_limit=3):
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
                if create_task(title, score, albums_listened_to):
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

def get_tokens():
    # If secrets.env exists, load it. Else, load environment variables
    if os.path.exists("secrets.env"):
        secrets = dotenv_values("secrets.env")
    else:
        secrets = os.environ

    td_token = secrets["TODOIST_API_KEY"]
    yt_token = secrets["YOUTUBE_API_KEY"]

    if not td_token or not yt_token:
        raise Exception("Please set the YOUTUBE and TODOIST API token in environment variable.")
    return td_token, yt_token

if __name__ == "__main__":
    td_token, yt_token = get_tokens()
    youtube = build('youtube', 'v3', developerKey=yt_token)
    doist = TodoistAPI(td_token)
    creds = get_creds()
    albums_listened_to = get_albums_listened_to(creds)

    # If a todoist project doesn't exist, create one
    if not any(list(filter(lambda x: x.name == 'Albums to listen to', doist.get_projects()))):
        doist.add_project(name='Albums to listen to')
        print("Created Albums to listen to project")

    # Get channel_id for theneedledrop
    request = youtube.channels().list(
        part='id',
        forUsername='theneedledrop'
    )
    response = request.execute()
    channel_id = response['items'][0]['id']

    # # Get playlists
    playlists = fetch_playlists(channel_id, youtube)

    # # TODO: Add an option to select genre

    # # For a playlist add albums todoist that match the minimum score
    playlist_id = playlists['All Reviews']
    playlist_video_scores(playlist_id, youtube, albums_listened_to)

    
