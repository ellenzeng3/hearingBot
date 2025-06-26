from fetch import fetch_event_detail
from extract import get_URL

# ─── Post upcoming meetings ─────────────────────────────────────────────────────
def post_upcoming(c):
    c.execute("""
            
    SELECT
        date,
        title,
        committee,
        url
    FROM hearings
    WHERE date(date) >= date('now')
    ORDER BY date(date) ASC;       
            
    """)
    rows = c.fetchall()
    if not rows:
        print("No upcoming hearings.")
    else:
        print("Upcoming hearings:")
        format_hearings_grouped(rows)
        # for ev_id, ev_date, title, committee in rows:
        #     print(f"{ev_date} | {committee} | {title}")



def post_last_update(c):
    c.execute("SELECT MAX(date_inserted) FROM hearings WHERE date(date) >= date('now')")
    row = c.fetchone()
    if not row or row[0] is None:
        print("No insertions found.")
        return

    print(f"\nLast posted hearings:")

    c.execute("""
        SELECT 
            date,
            title,
            committee,
            url
        FROM hearings
        WHERE date(date) >= date('now')
        ORDER BY date(date) ASC
    """)

    rows = c.fetchall()
    if not rows:
        print("None found")
    else:
        format_hearings_grouped(rows)


def format_hearings_grouped(rows):
    """
    Given rows of (date_str, committee, title, url),
    prints them grouped by date in a bullet list.
    """
    
    # print(rows)
    
    by_date = {}
    for date_str, committee, title, url in rows:
        by_date[date_str] = by_date.get(date_str, [])
        by_date[date_str].append((committee, title, url))

    # print("\n", by_date)
    output = []
    for date_str in sorted(by_date):
        output.append(date_str)
        for title, committee, url in by_date[date_str]:
            output.append(f"* {committee} | <{title} | {url}>")
        output.append("")
    print("\n".join(output).rstrip())


def backfill_missing_urls(c):
    c.execute("""
        SELECT id, url
        FROM hearings
        WHERE (url IS NULL OR url = '')
          AND date(date) >= date('now')
    """)
    rows = c.fetchall()

    if not rows:
        print("No missing URLs to backfill.")
        c.close()
        return

    print(f"Backfilling URLs for {len(rows)} hearings…")

    for ev_id, detail_url in rows:
        detail = fetch_event_detail(detail_url)            # your existing detail fetcher
        docs   = detail.get("documents", [])
        if not docs:
            # still no docs published
            continue

        # take the first document’s URL
        doc_url = docs[0].get("url")
        if not doc_url:
            continue

        # 2) Update the row with the new URL and refresh the insert timestamp
        now_ts = datetime.now(timezone.utc).isoformat()
        c.execute("""
            UPDATE hearings
               SET url          = ?,
                   date_inserted= ?
             WHERE id = ?
        """, (doc_url, now_ts, ev_id))
        print(f"  • Filled URL for {ev_id}: {doc_url}")

    conn.commit()
    conn.close()
    print("Done backfilling.")