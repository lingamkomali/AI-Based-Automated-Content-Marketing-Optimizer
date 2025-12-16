# --- Import Google API and pandas ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import os

# --- Google Sheet details ---
SPREADSHEET_ID = "1jI2vj3Gwhzgp76ERdB9Sou8JaqpnIpcIBV2oqldh-6M"

CREDENTIALS_FILE = "credentials.json"  # path to your service account key

# --- Function to upload CSV to Google Sheet ---
def upload_csv(csv_path, sheet_name="Sheet1"):
    # --- Check if CSV exists ---
    if not os.path.exists(csv_path):
        print(f" File not found: {csv_path}")
        return

    # --- Authorize Google Sheets ---
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)

    # --- Check if sheet (tab) exists ---
    metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_names = [s["properties"]["title"] for s in metadata["sheets"]]

    # --- Create sheet if missing ---
    if sheet_name not in sheet_names:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        ).execute()
        print(f" Created new tab: {sheet_name}")

    # --- Read CSV and clean data ---
    df = pd.read_csv(csv_path)
    df = df.fillna('')  
    data = [df.columns.tolist()] + df.values.tolist()

    # --- Upload data to the Google Sheet ---
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": data}
    ).execute()

    print(f" Uploaded '{csv_path}' to tab '{sheet_name}'")

# --- Run uploader for all platforms ---
if __name__ == "__main__":
    upload_csv("sample_data_twitter.csv", "twitter")  
    upload_csv("sample_data_reddit.csv", "reddit")  
    upload_csv("sample_data_youtube.csv", "youtube")
    upload_csv("sample_data_instagram.csv", "instagram") 
