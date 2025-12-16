"""
Milestone 3 – Module 3
A/B Testing Engine (FINAL – STABLE)
----------------------------------
- Reads Generated_Content from Content_Creation sheet
- Creates Variant B using rule-based optimization
- Scores Variant A vs Variant B
- Writes results to AB_Testing sheet
- Sends Slack notification
"""

# ===============================
# IMPORTS
# ===============================
import os
import re
import time
import gspread
import requests
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GSPREAD_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SOURCE_SHEET = "Content_Creation"
AB_SHEET = "AB_Testing"

if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID:
    raise EnvironmentError("❌ Google Sheets config missing in .env")

# ===============================
# CONNECT TO GOOGLE SHEETS
# ===============================
def connect_spreadsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

# ===============================
# SLACK
# ===============================
def send_slack(message):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
    except Exception:
        pass

# ===============================
# CREATE VARIANT B
# ===============================
def create_variant_b(text, platform):
    text = re.sub(r"\s+", " ", text).strip()

    cta_map = {
        "twitter": "👉 What’s your take? Reply below!",
        "reddit": "🧠 Let’s discuss.",
        "youtube": "🔔 Like, subscribe & comment!",
    }

    hashtags = re.findall(r"#\w+", text)
    hashtags = list(dict.fromkeys(hashtags))[:3]
    text = re.sub(r"#\w+", "", text).strip()

    optimized = f"{text}\n\n{cta_map.get(platform, '📢 Share your thoughts!')}"

    if hashtags:
        optimized += "\n\n" + " ".join(hashtags)

    return optimized.strip()

# ===============================
# SCORING FUNCTION
# ===============================
def score_content(text):
    score = 0

    words = len(text.split())
    if 10 <= words <= 60:
        score += 3

    if any(w in text.lower() for w in ["reply", "comment", "subscribe", "discuss"]):
        score += 3

    hashtags = re.findall(r"#\w+", text)
    if 1 <= len(hashtags) <= 3:
        score += 2

    if any(w in text.lower() for w in ["ai", "growth", "smart", "boost"]):
        score += 2

    return min(score, 10)

# ===============================
# MAIN A/B TESTING
# ===============================
def run_ab_testing():
    print("\n⚖️ Starting A/B Testing Engine...\n")

    sheet = connect_spreadsheet()
    source_ws = sheet.worksheet(SOURCE_SHEET)
    rows = source_ws.get_all_records()

    if not rows:
        print("⚠️ No content found in Content_Creation")
        return

    # ---------- Output Sheet ----------
    try:
        ab_ws = sheet.worksheet(AB_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        ab_ws = sheet.add_worksheet(title=AB_SHEET, rows="1000", cols="15")

    # ---------- Headers ----------
    headers = [
        "Test_ID",
        "Timestamp",
        "Topic",
        "Platform",
        "Variant_A",
        "Variant_B",
        "Score_A",
        "Score_B",
        "Winner",
    ]

    if ab_ws.row_values(1) != headers:
        ab_ws.clear()
        ab_ws.append_row(headers)

    processed = 0

    for idx, row in enumerate(rows, start=1):
        print(f"🔄 Processing row {idx}...")

        original = row.get("Generated_Content", "").strip()
        if not original:
            continue

        topic = row.get("Topic", "")
        platform = row.get("Platform", "").lower()

        variant_b = create_variant_b(original, platform)
        score_a = score_content(original)
        score_b = score_content(variant_b)

        winner = "Variant A" if score_a >= score_b else "Variant B"

        ab_ws.append_row([
            f"AB-{int(time.time())}-{idx}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            topic,
            platform,
            original,
            variant_b,
            score_a,
            score_b,
            winner,
        ])

        print(f"✅ Winner: {winner} (A={score_a}, B={score_b})")
        processed += 1

    send_slack(f"⚖️ A/B Testing completed for {processed} items")
    print(f"\n🎉 A/B Testing finished: {processed} rows processed")

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    run_ab_testing()
