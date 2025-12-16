AI Content Optimizer - Milestone 1 (Starter)
-------------------------------------------
Files included:
- collect_twitter.py      : Fetches your own tweets (Twitter API v2)
- collect_instagram.py    : Fetches your own Instagram media (Graph API)
- googlesheetsexp.py      : Push CSVs to Google Sheets using a service account
- requirements.txt        : Python dependencies (pip install -r requirements.txt)
- credentials.json        : Placeholder for Google service account credentials
- .env.template           : Template for environment variables
- sample_data.csv         : Example normalized output

Instructions:
1. Create a virtualenv and install dependencies:
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. Copy .env.template to .env and fill in values (TWITTER_BEARER_TOKEN, etc.)

3. For Google Sheets export, create a service account, download the JSON, and save as credentials.json.
   Share the target Google Sheet with the service account email (client_email) with Editor access.

4. Run collectors:
   python collect_twitter.py
   python collect_instagram.py

5. Push results to Google Sheets:
   export SPREADSHEET_ID=your_sheet_id
   python googlesheetsexp.py

Notes:
- This starter is "API-ready" (real). Do NOT commit secrets to source control.
- Instagram requires a Business/Creator account connected to a Facebook Page for insights.
- LinkedIn fetcher is not included in this package but can be added similarly.
