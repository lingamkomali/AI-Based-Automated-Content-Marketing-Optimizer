# --- Import libraries ---
from dotenv import load_dotenv
import os, requests, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Load API keys from .env file ---
load_dotenv()

# Get Twitter Bearer Token
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# --- Twitter API endpoint ---
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

# --- Topics to fetch tweets about --- 
QUERIES = [
    "digital marketing",
    "AI marketing",
    "social media strategy",
]

# --- Function to fetch tweets ---
def fetch_tweets(query, max_results=20):
    params = {
        "query": query + " -is:retweet lang:en",  # exclude retweets
        "tweet.fields": "id,text,author_id,created_at,public_metrics",
        "max_results": max_results
    }

    response = requests.get(SEARCH_URL, headers=headers, params=params)

    # Handle errors
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    tweets = response.json().get("data", [])
    result = []

    for t in tweets:
        result.append([
            query,
            t["text"].replace("\n", " "),
            t["author_id"],
            t["public_metrics"]["like_count"],
            t["created_at"]
        ])
    return result

# --- Function to upload data to Google Sheets ---
def upload_to_sheet(values):
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    body = {"values": [["Topic", "Text", "Author ID", "Likes", "Created At"]] + values}

    # Upload to the 'twitter' tab in Google Sheet
    service.spreadsheets().values().update(
        spreadsheetId="1jI2vj3Gwhzgp76ERdB9Sou8JaqpnIpcIBV2oqldh-6M",
        range="sheet1!A1",
        valueInputOption="RAW",
        body=body
    ).execute()
    print(f" Uploaded {len(values)} tweets to Google Sheet (tab: twitter)!")

# --- Run script ---
if __name__ == "__main__":
    all_tweets = []
    for q in QUERIES:
        all_tweets.extend(fetch_tweets(q, max_results=20))
        time.sleep(2)  
    upload_to_sheet(all_tweets)
