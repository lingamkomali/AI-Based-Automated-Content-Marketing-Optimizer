"""
Milestone 3 – Module 3
Performance Metrics Hub
--------------------------------
- Reads data from Content_Creation sheet
- Calculates sentiment, optimization & engagement metrics
- Writes row-wise metrics history
- Ensures headers are written ONCE
- Slack notification included
"""

# ===============================
# IMPORTS
# ===============================
import os
import pandas as pd
import gspread
import requests
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GSPREAD_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SOURCE_SHEET = "Content_Creation"
METRICS_SHEET = "performance_metrics"

# ===============================
# FIXED HEADER ORDER (DO NOT CHANGE)
# ===============================
HEADERS = [
    "Run_Timestamp",
    "Avg_Sentiment",
    "Positive_%",
    "Neutral_%",
    "Negative_%",
    "Twitter_Posts",
    "Reddit_Posts",
    "YouTube_Posts",
    "Avg_Optimization_Score",
    "Avg_Engagement_Score",
    "Total_Items",
]

# ===============================
# CONFIG CHECK (FIX)
# ===============================
def is_configured():
    return (
        SERVICE_ACCOUNT_FILE
        and SPREADSHEET_ID
        and os.path.exists(SERVICE_ACCOUNT_FILE)
    )

# ===============================
# GOOGLE SHEETS CONNECTION
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
# SLACK NOTIFICATION
# ===============================
def send_slack(message):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
    except Exception:
        pass

# ===============================
# METRICS CALCULATION
# ===============================
def calculate_metrics(df):
    metrics = {}

    metrics["Run_Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "Sentiment" in df.columns:
        metrics["Positive_%"] = round((df["Sentiment"] == "Positive").mean() * 100, 1)
        metrics["Neutral_%"]  = round((df["Sentiment"] == "Neutral").mean() * 100, 1)
        metrics["Negative_%"] = round((df["Sentiment"] == "Negative").mean() * 100, 1)
    else:
        metrics["Positive_%"] = metrics["Neutral_%"] = metrics["Negative_%"] = 0

    if "Sentiment_Score" in df.columns:
        df["Sentiment_Score"] = pd.to_numeric(
            df["Sentiment_Score"], errors="coerce"
        ).fillna(0)
        metrics["Avg_Sentiment"] = round(df["Sentiment_Score"].mean(), 2)
    else:
        metrics["Avg_Sentiment"] = 0

    if "Platform" in df.columns:
        metrics["Twitter_Posts"] = int((df["Platform"] == "twitter").sum())
        metrics["Reddit_Posts"]  = int((df["Platform"] == "reddit").sum())
        metrics["YouTube_Posts"] = int((df["Platform"] == "youtube").sum())
    else:
        metrics["Twitter_Posts"] = metrics["Reddit_Posts"] = metrics["YouTube_Posts"] = 0

    if "Optimization_Score" in df.columns:
        df["Optimization_Score"] = pd.to_numeric(
            df["Optimization_Score"], errors="coerce"
        ).fillna(0)
        metrics["Avg_Optimization_Score"] = round(
            df["Optimization_Score"].mean(), 2
        )
    else:
        metrics["Avg_Optimization_Score"] = 0

    if "Optimization_Score" in df.columns and "Sentiment_Score" in df.columns:
        df["Sentiment_Normalized"] = ((df["Sentiment_Score"] + 3) / 6) * 10
        df["Engagement_Score"] = (
            df["Optimization_Score"] + df["Sentiment_Normalized"]
        ) / 2
        metrics["Avg_Engagement_Score"] = round(
            df["Engagement_Score"].mean(), 2
        )
    else:
        metrics["Avg_Engagement_Score"] = 0

    metrics["Total_Items"] = len(df)

    return metrics

# ===============================
# UPLOAD METRICS (HEADERS SAFE)
# ===============================
def upload_metrics(sheet, metrics):
    try:
        try:
            ws = sheet.worksheet(METRICS_SHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=METRICS_SHEET, rows="200", cols="20")

        existing_headers = ws.row_values(1)
        if existing_headers != HEADERS:
            ws.clear()
            ws.append_row(HEADERS)

        ws.append_row([metrics[h] for h in HEADERS])
        print("✅ Performance metrics appended successfully")

    except Exception as e:
        print("❌ Failed to upload metrics:", e)

# ===============================
# ENTRY POINT (SAFE)
# ===============================
def run_performance_metrics():
    if not is_configured():
        return {
            "status": "error",
            "message": "Google Sheets credentials not configured"
        }

    sheet = connect_spreadsheet()
    source_ws = sheet.worksheet(SOURCE_SHEET)
    df = pd.DataFrame(source_ws.get_all_records())

    if df.empty:
        return {
            "status": "empty",
            "message": "No data found in Content_Creation sheet"
        }

    metrics = calculate_metrics(df)
    upload_metrics(sheet, metrics)

    send_slack(
        f"📈 Performance Metrics Updated\n"
        f"Total Items: {metrics['Total_Items']}\n"
        f"Avg Sentiment: {metrics['Avg_Sentiment']}\n"
        f"Avg Engagement Score: {metrics['Avg_Engagement_Score']}"
    )

    return {
        "status": "success",
        "metrics": metrics
    }

# ===============================
# RUN (CLI ONLY)
# ===============================
if __name__ == "__main__":
    result = run_performance_metrics()
    print(result)
