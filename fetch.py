import requests
from datetime import date
from dotenv import load_dotenv
import os 
from pathlib import Path
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from extract import get_URL


# ─── Configuration ────────────────────────────────────────────────────────────

CONGRESS = 119
HEARING_URL   = f"https://api.congress.gov/v3/hearing/{CONGRESS}"
MEETING_URL   = f"https://api.congress.gov/v3/committee-meeting/{CONGRESS}"
today = date.today().isoformat()  # e.g. "2025-06-18"

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("CONGRESS_API_KEY")
HEADERS = {"X-Api-Key": API_KEY}

# ─── Session with retries ─────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({"X-Api-Key": API_KEY})
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods=["GET"],
)

session.headers.update({"X-Api-Key": API_KEY})
session.mount("https://", HTTPAdapter(max_retries=retry))

# ─── Main fetches ───────────────────────────────────────────────────────────────

def fetch_all(kind):

    """
    Fetch all hearings or committee meetings for the current Congress.
    https://api.congress.gov/v3/committee-meeting/118?api_key=[INSERT_KEY]
    """
    try:
        url = HEARING_URL if kind == "hearing" else MEETING_URL

        params = {
        "meetingStatus": "Scheduled",
        "limit": 250
        }

        r = session.get(url, params=params, timeout=10)
        r.raise_for_status() 
        key = "hearings" if kind == "hearing" else "committeeMeetings"
        return r.json().get(key, [])

    except Exception as e:
        print(f"Error fetching {kind}s: {e}")
        return []
    

def fetch_event_detail(url):
     
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        r = session.get(url, headers=HEADERS, timeout=10) 
        r.raise_for_status()
        payload = r.json()
        return payload.get("hearing") or payload.get("committeeMeeting") or {}


    except Exception as e:
        print(f"Error fetching event detail: {e}")
        return {}
    

def backfill_missing_urls(c):
    c.execute("""
        SELECT id, API_call
        FROM hearings
        WHERE (url IS NULL OR url = '')
          AND date(date) >= date('now')
    """)
    rows = c.fetchall()

    if not rows:
        print("No upcoming hearings' missing URLs to backfill.")
        c.close()
        return

    print(f"Backfilling URLs for {len(rows)} hearings…")

    for ev_id, api_call in rows:
        detail = fetch_event_detail(api_call)            # your existing detail fetcher
        url    = get_URL(detail)
        if not url:
            print(f"still no URL for {ev_id}, skipping")
            continue

        c.execute("""
            UPDATE hearings
               SET url          = ?,
             WHERE id = ?
        """, (url, ev_id))
        print(f"  • Filled URL for {ev_id}: {url}")
        c.commit()

    c.close()
    print("Done backfilling.")
    