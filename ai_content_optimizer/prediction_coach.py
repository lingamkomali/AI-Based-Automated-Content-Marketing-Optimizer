"""
Milestone 3 – Module 4
Prediction Coach (No Streamlit)
--------------------------------
- Reads A/B testing results from Google Sheets
- Predicts best platform & posting time
- Calculates viral potential score (0–1)
- Writes recommendations to Prediction_Coach sheet
- Sends Slack notification
"""

# ===============================
# IMPORTS
# ===============================
import os
import json
import gspread
import requests
from datetime import datetime
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GSPREAD_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SOURCE_TAB = "AB_Testing"
OUTPUT_TAB = "Prediction_Coach"

PLATFORMS = ["Twitter", "Instagram", "LinkedIn", "YouTube"]

# ===============================
# GOOGLE SHEETS CONNECTION
# ===============================
def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

# ===============================
# SLACK
# ===============================
def send_slack(msg):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": msg}, timeout=5)
    except Exception:
        pass

# ===============================
# VIRAL PREDICTION LOGIC
# ===============================
def platform_modifier(text, platform):
    text = (text or "").lower()
    length = len(text.split())
    score = 0.0

    if platform == "Twitter":
        if length <= 30: score += 0.08
        if "#" in text: score += 0.05
        if "!" in text: score += 0.02

    elif platform == "Instagram":
        if 8 <= length <= 60: score += 0.07
        if "#" in text: score += 0.07
        if any(w in text for w in ["love", "fun", "amazing"]): score += 0.04

    elif platform == "LinkedIn":
        if length >= 20: score += 0.08
        if any(w in text for w in ["growth", "strategy", "data"]): score += 0.06

    elif platform == "YouTube":
        if length >= 40: score += 0.07
        if any(w in text for w in ["how to", "guide", "tutorial"]): score += 0.05

    return round(score, 3)

def best_posting_time(platform):
    return {
        "Twitter": "5–8 PM (Weekdays)",
        "Instagram": "6–9 PM (Weekdays)",
        "LinkedIn": "8–10 AM (Mornings)",
        "YouTube": "5–8 PM (Weekends)",
    }.get(platform, "Anytime")

def predict_viral_score(base_score, text):
    results = {}
    for platform in PLATFORMS:
        modifier = platform_modifier(text, platform)
        viral = 0.7 * float(base_score) + 0.3 * modifier
        results[platform] = round(min(max(viral, 0), 1), 3)

    best_platform = max(results, key=results.get)
    return best_platform, results[best_platform]

# ===============================
# MAIN ENGINE
# ===============================
def run_prediction_coach():
    print("🔮 Running Prediction Coach...\n")

    sheet = connect_sheet()
    ws_ab = sheet.worksheet(SOURCE_TAB)
    df = pd.DataFrame(ws_ab.get_all_records())

    if df.empty:
        print("⚠️ No A/B testing data found.")
        return

    results = []

    for idx, row in df.iterrows():
        text_a = row.get("Variant_A", "")
        text_b = row.get("Variant_B", "")
        score_a = float(row.get("Score_A", 0))
        score_b = float(row.get("Score_B", 0))

        plat_a, viral_a = predict_viral_score(score_a, text_a)
        plat_b, viral_b = predict_viral_score(score_b, text_b)

        if viral_a >= viral_b:
            winner = "Variant A"
            final_text = text_a
            platform = plat_a
            viral_score = viral_a
        else:
            winner = "Variant B"
            final_text = text_b
            platform = plat_b
            viral_score = viral_b

        results.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            winner,
            platform,
            viral_score,
            best_posting_time(platform),
            final_text,
        ])

        print(f"✅ Row {idx+1}: {winner} → {platform} ({viral_score})")

    # ===============================
    # WRITE TO GOOGLE SHEETS
    # ===============================
    try:
        ws_out = sheet.worksheet(OUTPUT_TAB)
        ws_out.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws_out = sheet.add_worksheet(title=OUTPUT_TAB, rows="1000", cols="10")

    headers = [
        "Timestamp",
        "Winning_Variant",
        "Best_Platform",
        "Viral_Score",
        "Recommended_Time",
        "Winning_Text",
    ]

    ws_out.update([headers] + results)
    print("\n✅ Prediction results saved to Google Sheets")

    send_slack(f"🔮 Prediction Coach completed for {len(results)} items")

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    run_prediction_coach()
