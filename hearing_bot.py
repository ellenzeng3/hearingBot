from datetime import datetime, date
import sqlite3
from fetch import fetch_all, fetch_event_detail, backfill_missing_urls
from extract import get_date, get_title, get_committee, get_URL, parse_date
from slack_sdk import WebClient
from sql import post_upcoming, post_last_update


# ─── Setup SQLite ─────────────────────────────────────

conn = sqlite3.connect("hearings.db")
c    = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS hearings (
    id        TEXT PRIMARY KEY,
    date      TEXT,
    title     TEXT,
    committee TEXT,
    URL       TEXT,      
    API_call  TEXT,
    date_inserted TEXT
)
""")
conn.commit()

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():

    # Open SQLite DB
    conn = sqlite3.connect("hearings.db")
    c    = conn.cursor()

    # Preload seen IDs or start fresh if table missing
    try:
        c.execute("SELECT id FROM hearings")
        seen_ids = {row[0] for row in c.fetchall()}
    except Exception as e:
        seen_ids = set() 

    print(f"Seen IDs loaded: {len(seen_ids)}")

    known_errors = [118388, 118320, 118290, 118290, 58326] 
    new_hearings = [] 

    try:
        events = fetch_all("hearing") + fetch_all("meeting") 
        # events = fetch_all("hearing") 
    except Exception as e:
        print(f"Error fetching events: {e}")
        return

    for event in events:
        ev_id = event.get("eventId") or str(event.get("jacketNumber"))

        # print("ID:", ev_id)
        # print(type(ev_id))
        # skip if already seen
        if ev_id in seen_ids:
            continue 
        # elif ev_id in known_errors:
        #     continue
        seen_ids.add(ev_id)

        # Not in DB → fetch detail and parse date
        try:
            api_call = event["url"]
            detail = fetch_event_detail(api_call)
            title     = get_title(detail)
            committee = get_committee(detail)
            date_obj  = get_date(detail)
            url       = get_URL(detail)
        except Exception as e:
            print(f"Error processing event {ev_id}: {e}")
            continue 

        today = date.today().isoformat()

        try:
            dt = parse_date(date_obj)
            date_str = dt.date().isoformat()
            new_hearings.append((ev_id, date_str, title, committee, url, today, api_call))
            # print(f"New hearing found: {date_str} | {committee} | {title}")
        except Exception as e:
            if ev_id in known_errors:
                continue
            print(f"Error parsing date for {ev_id}: {e}")
            continue
 
    with conn:
        c.executemany(
            "INSERT INTO hearings (id, date, title, committee, url, date_inserted, API_call) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            new_hearings
        )

    print(f"New hearings: {len(new_hearings)}")

    post_upcoming(c)
    
    # post_last_update(c)

    # backfill_missing_urls(c)

    conn.close()


main()