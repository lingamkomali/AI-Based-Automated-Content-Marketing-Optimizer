import os
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_notification(topic, platform):
    if not SLACK_WEBHOOK_URL:
        print("⚠️ Slack webhook not configured")
        return

    message = {
        "text": f"""
🚀 *New Content Generated*
• *Topic:* {topic}
• *Platform:* {platform}
• *Status:* Saved to Google Sheets ✅
"""
    }

    requests.post(SLACK_WEBHOOK_URL, json=message)
