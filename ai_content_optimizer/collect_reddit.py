# --- Import necessary libraries ---
from dotenv import load_dotenv
import os, praw, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Load environment variables ---
load_dotenv()

# --- Connect to Reddit API using PRAW ---
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="AIContentOptimizer/1.0"
)

# --- Choose subreddits to collect posts from ---
SUBREDDITS = [
    "marketing", "digitalmarketing", "ContentMarketing",
    "socialmedia", "Entrepreneur", "growthhacking"
]

# --- Function to fetch Reddit posts ---
def fetch_posts(max_posts=120):
    posts = []
    for sub in SUBREDDITS:
        for post in reddit.subreddit(sub).hot(limit=20):
            posts.append([sub, post.title, str(post.author), post.score, post.url])
            if len(posts) >= max_posts:  # stop when enough posts collected
                return posts
            time.sleep(0.2)
    return posts

# --- Function to upload data to Google Sheets ---
def upload_to_sheet(values):
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    # Connect to Google Sheets API
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = "1jI2vj3Gwhzgp76ERdB9Sou8JaqpnIpcIBV2oqldh-6M"
    sheet_name = "reddit"  # Only upload to this tab

    # --- Clear old data before writing new ---
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1:Z"
        ).execute()
        print("🧹 Old data cleared in 'reddit' tab.")
    except Exception as e:
        print(f" Could not clear old data: {e}")

    # --- Upload new Reddit data ---
    body = {"values": [["Subreddit", "Title", "Author", "Score", "URL"]] + values}

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f"✅ Uploaded {len(values)} Reddit posts to Google Sheet (tab: {sheet_name})!")

# --- Run the script ---
if __name__ == "__main__":
    data = fetch_posts(120)  # You can change 50 → any number
    upload_to_sheet(data)
