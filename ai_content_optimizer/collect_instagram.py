# collect_instagram.py
# Real API-ready fetcher for your own Instagram Business/Creator account via Meta Graph API.
# Requires IG_USER_ID and IG_ACCESS_TOKEN in environment (.env recommended)
#
# Usage: python collect_instagram.py
#
# Notes: Ensure the Instagram account is Business/Creator and connected to a Facebook Page.
from dotenv import load_dotenv
import os, requests, sys, time
import pandas as pd

load_dotenv()

ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
IG_USER_ID = os.getenv('IG_USER_ID')  # numeric id
if not ACCESS_TOKEN or not IG_USER_ID:
    print('Missing IG_ACCESS_TOKEN or IG_USER_ID in environment. See .env.template.')
    sys.exit(1)

GRAPH = 'https://graph.facebook.com/v17.0'  # adjust version as needed

def fetch_media_list(ig_user_id, limit=50):
    url = f'{GRAPH}/{ig_user_id}/media'
    params = {'access_token': ACCESS_TOKEN, 'fields': 'id,caption,media_type,media_url,timestamp' , 'limit': limit}
    all_media = []
    while url:
        resp = requests.get(url, params=params)
        if resp.status_code == 400:
            print('Bad request. Check permissions and access token.')
            resp.raise_for_status()
        resp.raise_for_status()
        data = resp.json()
        items = data.get('data', [])
        all_media.extend(items)
        paging = data.get('paging', {})
        next_page = paging.get('next')
        url = next_page
        params = {}  # when using next, params are in the next url
    return all_media

def fetch_insights(media_id):
    url = f'{GRAPH}/{media_id}/insights'
    params = {'metric': 'engagement,impressions,reach,saved', 'access_token': ACCESS_TOKEN}
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return {}
    data = resp.json().get('data', [])
    return {d['name']: d.get('values', [{}])[0].get('value') for d in data}

def normalize(media_list):
    rows = []
    for m in media_list:
        insights = fetch_insights(m['id'])
        rows.append({
            'platform': 'instagram',
            'post_id': m.get('id'),
            'caption': m.get('caption'),
            'media_type': m.get('media_type'),
            'media_url': m.get('media_url'),
            'timestamp': m.get('timestamp'),
            'engagement': insights.get('engagement'),
            'impressions': insights.get('impressions'),
            'reach': insights.get('reach'),
            'saved': insights.get('saved')
        })
    return rows

def main():
    media = fetch_media_list(IG_USER_ID)
    rows = normalize(media)
    import pandas as pd
    df = pd.DataFrame(rows)
    out = 'sample_data_instagram.csv'
    df.to_csv(out, index=False)
    print(f'Wrote {len(df)} rows to {out}')

if __name__ == '__main__':
    main()
