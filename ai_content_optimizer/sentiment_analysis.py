"""
Milestone 3 – Module 2
Sentiment Analysis (Same Content_Creation Sheet)
------------------------------------------------
- Reads Generated_Content
- Performs rule-based sentiment analysis
- Writes Sentiment + Sentiment_Score in SAME sheet
- Auto-creates columns if missing
- Sends Slack notification
"""

# ===============================
# IMPORTS
# ===============================
import os
import re
import gspread
import requests
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GSPREAD_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = "Content_Creation"   
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID:
    raise EnvironmentError("❌ Google Sheets config missing")

# ===============================
# CONNECT TO SHEET
# ===============================
def connect_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# ===============================
# SENTIMENT WORD LISTS
# ===============================
POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "awesome",
    "love", "best", "positive", "success", "improved",
    "powerful", "efficient", "innovative"
}

NEGATIVE_WORDS = {
    "bad", "poor", "worst", "hate", "terrible",
    "boring", "awful", "negative", "fail", "problem",
    "slow", "difficult"
}

# ===============================
# SENTIMENT FUNCTION
# ===============================
def analyze_sentiment(text):
    text = text.lower()
    words = set(re.findall(r"\b\w+\b", text))

    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)

    score = pos - neg
    score = max(-3, min(3, score))  # clamp

    if score > 0:
        return "Positive", score
    elif score < 0:
        return "Negative", score
    else:
        return "Neutral", 0

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
# MAIN
# ===============================
if __name__ == "__main__":
    print("📊 Running Sentiment Analysis on Content_Creation sheet...\n")

    ws = connect_sheet()
    rows = ws.get_all_values()

    if not rows:
        print("❌ Sheet is empty")
        exit()

    headers = rows[0]
    data = rows[1:]

    # -------------------------------
    # Ensure required columns exist
    # -------------------------------
    REQUIRED_COLUMNS = ["Sentiment_analysis", "Sentiment_Score"]

    for col in REQUIRED_COLUMNS:
        if col not in headers:
            ws.update_cell(1, len(headers) + 1, col)
            headers.append(col)

    gen_col = headers.index("Generated_Content")
    sent_col = headers.index("Sentiment_analysis") + 1
    score_col = headers.index("Sentiment_Score") + 1

    updated = 0

    for idx, row in enumerate(data, start=2):
        if len(row) <= gen_col:
            continue

        content = row[gen_col].strip()
        if not content:
            continue

        sentiment, score = analyze_sentiment(content)

        ws.update_cell(idx, sent_col, sentiment)
        ws.update_cell(idx, score_col, score)

        updated += 1
        print(f"✅ Row {idx}: {sentiment} ({score})")

    send_slack(f"📊 Sentiment Analysis completed for {updated} rows")
    print(f"\n🎉 Sentiment analysis finished: {updated} rows updated")
