"""
AI-Based Automated Content Marketing Optimizer
Milestone 2 – Content Generation Engine

✔ Separate worksheet for AI-generated content
✔ Does NOT touch twitter / reddit / youtube tabs
✔ Platform-optimized prompts
✔ Google Sheets + Slack integration
✔ Secure .env usage
✔ Streamlit UI appended (NO terminal input when Streamlit runs)
"""

# ===============================
# IMPORTS
# ===============================
import streamlit as st
import os
from datetime import datetime
import requests

import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

SERVICE_ACCOUNT_FILE = os.getenv("GSPREAD_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

CONTENT_SHEET_NAME = "Content_Creation"

if not GEMINI_API_KEY or not GEMINI_MODEL:
    raise EnvironmentError("❌ Gemini API configuration missing")

if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID:
    raise EnvironmentError("❌ Google Sheets configuration missing")

# ===============================
# GEMINI CONFIG
# ===============================
genai.configure(api_key=GEMINI_API_KEY)

# ===============================
# GOOGLE SHEETS CONNECTION
# ===============================
def connect_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)


def get_content_sheet(spreadsheet):
    try:
        ws = spreadsheet.worksheet(CONTENT_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=CONTENT_SHEET_NAME,
            rows="1000",
            cols="10"
        )
        ws.append_row([
            "Timestamp",
            "Topic",
            "Platform",
            "Generated_Content",
            "Source"
        ])
    return ws

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
# CONTENT GENERATION (ORIGINAL)
# ===============================
def generate_content(topic, platform):
    platform = platform.lower()

    if platform == "reddit":
        prompt = f"""
You are a genuine Reddit user.

Write a natural discussion post (120–180 words) about:
"{topic}"

Rules:
- No hashtags
- No marketing language
- Insightful and conversational
- Ask 1 thoughtful question at the end
"""

    elif platform == "twitter":
        prompt = f"""
Write 2 tweets about:
"{topic}"

Rules:
- Under 280 characters each
- Professional and engaging
- Exactly 2 hashtags per tweet
- Max 1 emoji
"""

    elif platform == "youtube":
        prompt = f"""
Create YouTube-ready content for:
"{topic}"

Include:
1. Compelling title
2. Description (120–180 words)
3. 4–6 relevant hashtags

Tone: Informative, professional
"""

    else:
        raise ValueError("❌ Platform must be reddit, twitter, or youtube")

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text.strip()

# ===============================
# SAVE TO GOOGLE SHEET
# ===============================
def save_content(ws, topic, platform, content):
    ws.append_row(
        [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            topic,
            platform,
            content,
            "AI_Generated"
        ],
        value_input_option="USER_ENTERED"
    )

# ===============================
# ORIGINAL CLI MAIN (UNCHANGED)
# ===============================
def main():
    print("\n🚀 AI Content Creation Engine Started\n")

    topic = input("Enter topic: ").strip()
    platform = input("Enter platform (reddit / twitter / youtube): ").strip()

    print("\n🔄 Generating optimized content...\n")
    content = generate_content(topic, platform)

    print("📄 Generated Content:\n")
    print(content)

    try:
        spreadsheet = connect_sheet()
        ws = get_content_sheet(spreadsheet)
        save_content(ws, topic, platform, content)

        send_slack(
            f"✅ *AI Content Created*\n"
            f"Topic: {topic}\n"
            f"Platform: {platform}"
        )

        print("\n✅ Content saved to Content_Creation sheet")

    except Exception as e:
        send_slack(f"❌ Content creation failed: {e}")
        print("\n❌ Error saving content")
        print(e)

# ===============================
# STREAMLIT UI (NEW FEATURE)
# ===============================
def streamlit_app():
    st.set_page_config(
        page_title="AI Content Marketing Optimizer",
        page_icon="🚀",
        layout="wide"
    )

    st.title("🚀 AI-Based Automated Content Marketing Optimizer")
    st.caption("Milestone 2 – Streamlit Content Generator")

    topic = st.text_input("Topic / Product Name")
    platform = st.selectbox(
        "Platform",
        ["reddit", "twitter", "youtube"]
    )

    if st.button("🚀 Generate Content"):
        if not topic:
            st.warning("Please enter a topic")
            return

        with st.spinner("Generating content..."):
            content = generate_content(topic, platform)

        st.subheader("📄 Generated Content")
        st.text_area("", content, height=300)

        try:
            spreadsheet = connect_sheet()
            ws = get_content_sheet(spreadsheet)
            save_content(ws, topic, platform, content)

            send_slack(
                f"✅ *AI Content Created (Streamlit)*\n"
                f"Topic: {topic}\n"
                f"Platform: {platform}"
            )

            st.success("✅ Content saved to Google Sheet & Slack notified")

        except Exception as e:
            st.error(f"❌ Error saving content: {e}")

# ===============================
# ENTRY POINT FIX (CRITICAL)
# ===============================
if __name__ == "__main__":
    if os.getenv("STREAMLIT_SERVER_RUNNING") == "true":
        streamlit_app()
    else:
        main()


