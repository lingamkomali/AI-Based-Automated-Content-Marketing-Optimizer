# --- Import libraries ---
from dotenv import load_dotenv
import os, time
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

# --- Load environment variables ---
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- Connect to YouTube API ---
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# --- Choose search keyword ---
SEARCH_QUERY = "digital marketing"  # You can change this to any topic

# --- Fetch YouTube videos ---
def fetch_youtube_videos(max_videos=100):
    videos = []
    request = youtube.search().list(
        part="snippet",
        q=SEARCH_QUERY,
        type="video",
        maxResults=89
    )
    response = request.execute()

    for item in response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Get video statistics (views, likes)
        stats_req = youtube.videos().list(part="statistics", id=video_id)
        stats_res = stats_req.execute()
        stats = stats_res["items"][0]["statistics"]

        views = stats.get("viewCount", "0")
        likes = stats.get("likeCount", "0")

        videos.append([title, channel, views, likes, url])
        if len(videos) >= max_videos:
            break
        time.sleep(0.2)

    return videos


# --- Upload to Google Sheets ---
def upload_to_sheet(values):
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build("sheets", "v4", credentials=creds)

    SPREADSHEET_ID = "1jI2vj3Gwhzgp76ERdB9Sou8JaqpnIpcIBV2oqldh-6M"
    TAB_NAME = "youtube"

    # Step 1: Ensure the "youtube" tab exists, or create it
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_titles = [s["properties"]["title"] for s in sheet_metadata["sheets"]]

    if TAB_NAME not in sheet_titles:
        print(f" Creating new tab '{TAB_NAME}' in your Google Sheet...")
        add_sheet_request = {
            "requests": [{"addSheet": {"properties": {"title": TAB_NAME}}}]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=add_sheet_request
        ).execute()
        print(f"Tab '{TAB_NAME}' created successfully!")

    #Step 2: Clear old data
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{TAB_NAME}!A1:Z"
        ).execute()
    except HttpError as e:
        print(" Error clearing data:", e)

    # Step 3: Upload new YouTube data
    body = {"values": [["Title", "Channel", "Views", "Likes", "URL"]] + values}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{TAB_NAME}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f" Uploaded {len(values)} YouTube videos to Google Sheet (tab: {TAB_NAME})!")


# --- Run script ---
if __name__ == "__main__":
    data = fetch_youtube_videos(100)
    upload_to_sheet(data)
