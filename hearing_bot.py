from datetime import datetime, date
import sqlite3
from fetch import fetch_all, fetch_event_detail 
from extract import get_date, get_title, get_committee, get_URL, parse_date, get_status
from slack_sdk import WebClient
from post import post_upcoming, post_last_update, format_hearings_grouped, post_changed
from backfill import backfill_missing_urls, check_status

# ─── Setup SQLite ─────────────────────────────────────

# conn = sqlite3.connect("hearings.db")
# c    = conn.cursor()
# c.execute("""
#     ALTER TABLE hearings
#     ADD status  TEXT;
#     """)

# c.execute("""
# CREATE TABLE IF NOT EXISTS hearings (
#     id        TEXT PRIMARY KEY,
#     date      TEXT,
#     title     TEXT,
#     committee TEXT,
#     URL       TEXT,      
#     API_call  TEXT,
#     date_inserted TEXT
# )
# """)
# conn.commit()



# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    # update()
    # backfill_missing_urls()
    post_upcoming()
    # post_last_update()
    # check_status()
    # post_changed()
     
def update():

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

    known_errors = ["118388", "118320", "118290", "118290", "58326", "118259"] 
    new_hearings = [] 
    new_upcoming_hearings = []

    try:
        events = fetch_all("hearing") + fetch_all("meeting") 
        # events = fetch_all("hearing") 
    except Exception as e:
        print(f"Error fetching events: {e}")
        return

    for event in events:
        ev_id = event.get("eventId") or str(event.get("jacketNumber"))
        if ev_id in seen_ids:
            # print("Seen")
            continue 
        if ev_id in known_errors:
            # print(f"Skipping known error event {ev_id}")
            continue
        seen_ids.add(ev_id)

        # Not in DB → fetch detail and parse date
        try:
            api_call = event["url"]
            detail = fetch_event_detail(api_call)
            title     = get_title(detail)
            committee = get_committee(detail)
            date_obj  = get_date(detail)
            url       = get_URL(detail)
            status    = get_status(detail)

        except Exception as e:
            print(f"Error processing event {ev_id}: {e}")
            continue 

        today = date.today().isoformat()

        try:
            dt = parse_date(date_obj)
            date_str = dt.date().isoformat()
            new_hearings.append((ev_id, date_str, title, committee, url, today, api_call, status))

            if date_str >= today:
                new_upcoming_hearings.append((date_str, committee, title, url, status)) 
                print(f"New hearing found: {status}: {date_str} | {committee} | {title}")
        except Exception as e:
            if ev_id in known_errors:
                # print(ev_id, "is known to have errors.")
                continue
            print(f"Error parsing {ev_id}: {e}")
            continue
 
    with conn:
        c.executemany(
            "INSERT INTO hearings (id, date, title, committee, url, date_inserted, API_call, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            new_hearings
        )
    conn.close()
    print(f"New hearings: {len(new_hearings)}")
    print(f"New upcoming hearings: {len(new_upcoming_hearings)}")
    if new_upcoming_hearings:
        format_hearings_grouped(new_upcoming_hearings) 



main()