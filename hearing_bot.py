from datetime import datetime, date
import sqlite3
from fetch import fetch_all, fetch_event_detail
from extract import normalize_date, normalize_title, normalize_committee, parse_date
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
    upcoming_hearings = [] 

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
        elif ev_id in known_errors:
            continue
        seen_ids.add(ev_id)

        # Not in DB → fetch detail and parse date
        detail = fetch_event_detail(event["url"])
        title     = normalize_title(detail)
        committee = normalize_committee(detail)
        date_obj   = normalize_date(detail)

        today = date.today().isoformat()

        try:
            dt = parse_date(date_obj)
            date_str = dt.date()
            new_hearings.append((ev_id, date_str.isoformat(), title, committee, today))
            # print(f"New hearing found: {date_str} | {committee} | {title}")
        except Exception as e:
            if ev_id in known_errors:
                continue
            print(f"Error parsing date for {ev_id}: {e}")
            continue
        # Not past = post an update
        if date_obj > today: 
            upcoming_hearings.append((date_str, committee, title))
            # print(f"Upcoming hearing")
            continue 
 
    with conn:
        c.executemany(
            "INSERT INTO hearings (id, date, title, committee, date_inserted) "
            "VALUES (?, ?, ?, ?, ?)",
            new_hearings
        )

    print(f"\nPosted {len(new_hearings)} new hearings")
    post_upcoming(c)

    post_last_update(c)

    conn.close()


main()