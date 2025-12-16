import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from gspread.exceptions import WorksheetNotFound

# ================================
# CONFIG
# ================================

SERVICE_ACCOUNT_FILE = "credentials.json"
SPREADSHEET_ID = "1jI2vj3Gwhzgp76ERdB9Sou8JaqpnIpcIBV2oqldh-6M"
WORKSHEET_NAME = "content generation & optimization "   # will be created if missing

# ================================
# FUNCTION
# ================================

def save_to_google_sheet(topic, platform, content):
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError("❌ credentials.json not found")

    scope = ["https://www.googleapis.com/auth/spreadsheets"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # ✅ Get worksheet or create it
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows="1000",
            cols="10"
        )
        # Add header row once
        worksheet.append_row([
            "Timestamp",
            "Topic",
            "Platform",
            "Generated Content"
        ])

    worksheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        topic,
        platform,
        content
    ])
