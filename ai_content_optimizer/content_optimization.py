"""
Milestone 2 – Module 1
Rule-Based Content Optimization Engine
-------------------------------------
- Reads generated marketing content from Google Sheets
- Applies deterministic optimization rules
- Calculates optimization score (0–10)
- Updates optimized content + score in Google Sheets
- Sends Slack notification
"""

# ===============================
# IMPORTS
# ===============================
import os
import re
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GSPREAD_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# ⚠️ THIS MUST BE YOUR CONTENT CREATION SHEET (NOT twitter/reddit)
WORKSHEET_NAME = os.getenv("CONTENT_CREATION_SHEET", "Content_Creation")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID:
    raise EnvironmentError("❌ Google Sheets configuration missing")

# ===============================
# CONNECT TO GOOGLE SHEET
# ===============================
def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# ===============================
# COLUMN HELPERS
# ===============================
def find_generated_content(row_dict):
    for key, value in row_dict.items():
        if "generated" in key.lower() and "content" in key.lower():
            return str(value).strip()
    return ""

def find_platform(row_dict):
    for key, value in row_dict.items():
        if "platform" in key.lower():
            return str(value).strip().lower()
    return ""

# ===============================
# OPTIMIZATION RULES
# ===============================
def optimize_content(text, platform):
    text = re.sub(r"\s+", " ", text).strip()

    hashtags = re.findall(r"#\w+", text)
    hashtags = list(dict.fromkeys(hashtags))[:3]
    text = re.sub(r"#\w+", "", text).strip()

    cta_map = {
        "twitter": "👉 What’s your take? Reply below!",
        "youtube": "🔔 Like, subscribe & comment!",
        "reddit": "🧠 Let’s discuss.",
        "linkedin": "💬 Share your thoughts in the comments."
    }

    optimized = f"{text}\n\n{cta_map.get(platform, '📢 Let us know your thoughts!')}"

    if hashtags:
        optimized += "\n\n" + " ".join(hashtags)

    return optimized

# ===============================
# SCORE (0–10)
# ===============================
def calculate_score(original, optimized, platform):
    score = 0

    if len(optimized) <= len(original):
        score += 2

    if any(w in optimized.lower() for w in ["reply", "comment", "subscribe", "discuss"]):
        score += 3

    if 1 <= len(re.findall(r"#\w+", optimized)) <= 3:
        score += 3

    platform_words = {
        "twitter": "reply",
        "youtube": "subscribe",
        "reddit": "discuss",
        "linkedin": "comment",
    }

    if platform in platform_words and platform_words[platform] in optimized.lower():
        score += 2

    return min(score, 10)

# ===============================
# SLACK NOTIFICATION
# ===============================
def send_slack(count):
    if not SLACK_WEBHOOK_URL:
        return

    payload = {
        "text": f"✅ Content Optimization Completed\nOptimized Rows: {count}"
    }

    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    ws = connect_sheet()

    rows = ws.get_all_values()
    headers = rows[0]
    data_rows = rows[1:]

    # 🔒 REQUIRED COLUMNS
    REQUIRED_COLUMNS = [
        "Generated_Content",
        "Optimized_Content",
        "Optimization_Score",
    ]

    for col in REQUIRED_COLUMNS:
        if col not in headers:
            ws.update_cell(1, len(headers) + 1, col)
            headers.append(col)

    gen_col = headers.index("Generated_Content") + 1
    opt_col = headers.index("Optimized_Content") + 1
    score_col = headers.index("Optimization_Score") + 1

    optimized_count = 0

    for idx, row in enumerate(data_rows, start=2):
        row_dict = dict(zip(headers, row))

        original = find_generated_content(row_dict)
        platform = find_platform(row_dict)

        if not original:
            continue

        optimized = optimize_content(original, platform)
        score = calculate_score(original, optimized, platform)

        # ✅ FIXED UPDATE (2D LIST REQUIRED)
        ws.update(f"{chr(64 + opt_col)}{idx}", [[optimized]])
        ws.update(f"{chr(64 + score_col)}{idx}", [[score]])

        optimized_count += 1
        print(f"✅ Optimized row {idx} | Score: {score}")

    send_slack(optimized_count)
    print(f"\n🎉 Optimization finished: {optimized_count} rows updated")
