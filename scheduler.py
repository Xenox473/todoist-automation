from automate import *

def get_token():
    token = os.getenv("YOUTUBE_API_KEY")
    if not token:
        raise Exception("Please set the YOUTUBE API token in environment variable.")
    return token

if __name__ == "__main__":
    api_key = get_token()