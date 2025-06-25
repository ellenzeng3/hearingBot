#!/usr/bin/env python3
"""
Fetch and print all upcoming hearings and committee meetings
for the current U.S. Congress, along with their full descriptions.
"""

import os 
from datetime import datetime, date, timedelta, timezone
import requests
from pathlib import Path
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import sqlite3
from slack_sdk import WebClient

# ─── Setup SQLite ─────────────────────────────────────

conn = sqlite3.connect("hearingsTest.db")
c    = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS hearings (
    id        TEXT PRIMARY KEY,
    date      TEXT,
    title     TEXT,
    committee TEXT,      
    date_inserted TEXT
)
""")
conn.commit()

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

def fetch_all(kind) -> list:

    """
    Fetch all hearings or committee meetings for the current Congress.
    https://api.congress.gov/v3/committee-meeting/118?api_key=[INSERT_KEY]
    """

    try:
        url = HEARING_URL if kind == "hearing" else MEETING_URL

        params = {
        "meetingStatus": "Scheduled",
        "limit": 250,
        # "fromDate": cutoff 
        }

        r = session.get(url, params=params, timeout=10) 
        # r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status() 
        key = "hearings" if kind == "hearing" else "committeeMeetings"
        return r.json().get(key, [])

    except Exception as e:
        print(f"Error fetching {kind}s: {e}")
        return []
    

def fetch_event_detail(url) -> str:
    
    # Fetch the full details of a hearing or committee meeting
    # https://api.congress.gov/v3/committee-meeting/118/house/115538?api_key=[INSERT_KEY]

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        r = session.get(url, headers=HEADERS, timeout=10)
        # r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        payload = r.json()
        return payload.get("hearing") or payload.get("committeeMeeting") or {}


    except Exception as e:
        print(f"Error fetching event detail: {e}")
        return {}
    
# ─── Detail Extractors ───────────────────────────────────────────────────────────


def normalize_date(detail: dict) -> str:
    """
    Pull a YYYY-MM-DD date from either 'meetingDate' or the first
    entry in 'dates' (for hearings), or 'date' (for meetings).
    """
    if date_obj :=  detail.get("date"):
        return date_obj
    date_obj = detail.get("dates")
    return date_obj[0].get("meetingDate", "N/A") if date_obj else "N/A"

def normalize_title(detail: dict) -> str:
    """Safely pull the hearing/meeting title."""
    return detail.get("title" "") 

def normalize_committee(detail: dict) -> str:
    """
    Use 'committeeName' if present, otherwise first entry
    in the 'committees' list, or fall back to "N/A".
    """
    if name := detail.get("committeeName"):
        return name
    committees = detail.get("committees", [])
    return committees[0].get("name", "N/A") if committees else "N/A"

# ─── Database ───────────────────────────────────────────────────────────

def list_all_hearings_sorted():
    
    try:
        conn = sqlite3.connect("hearings.db")
        c    = conn.cursor()

        # ASC for oldest→newest, or DESC for newest→oldest
        c.execute("""
            SELECT id, date, title, committee, date_inserted
            FROM hearings
            ORDER BY date(date) ASC
        """)
        for ev_id, ev_date, title, committee, inserted in c.fetchall():
            try:
                print(f"{ev_date[:10]} | {committee} | {title}")
            except Exception as e:
                print(f"Error printing hearing: {e}")
        conn.close()

    except Exception as e:
        print(f"Error listing hearings: {e}")
        return []


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Open SQLite DB
    conn = sqlite3.connect("hearings.db")
    c    = conn.cursor()

    # Preload seen IDs
    
    # Preload seen IDs or start fresh if table missing
    try:
        c.execute("SELECT id FROM hearings")
        seen_ids = {row[0] for row in c.fetchall()}
    except Exception as e:
        seen_ids = set() 

    # Fetch all hearings and committee meetings
    # start_time = time.time()
    new_hearings = []
    today = date.today().isoformat()  # e.g. "2025-06-18"
    # print(today)
    events = fetch_all("hearing") + fetch_all("meeting")


    # 3) Begin a single transaction for all your lookups + inserts
    # with conn:
    for event in events:
        ev_id = event.get("eventId") or event.get("jacketNumber")

        # skip if already seen
        if ev_id in seen_ids:
            continue
        seen_ids.add(ev_id)

        # Not in DB → fetch detail and parse date
        detail = fetch_event_detail(event["url"])
        date_obj   = normalize_date(detail)        
        now_str  = datetime.now() # fallback to today if date_obj is None

        # Already past → insert & skip
        if date_obj < today: 
            new_hearings.append((ev_id, date_obj[:10], None, None, now_str))
            continue 

        # Not past → insert & append to all_events
        title     = normalize_title(detail)
        committee = normalize_committee(detail)
        new_hearings.append({ev_id, date_obj[:10], title, committee, now_str})

    with conn:
        c.executemany(
            "INSERT INTO hearings (id, date, title, committee, date_inserted) "
            "VALUES (?, ?, ?, ?, ?)",
            new_hearings
        )

    print(f"\nPosted {len(new_hearings)} new hearings")


main()