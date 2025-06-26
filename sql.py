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
    last_date = c.fetchone()[0]
    print(last_date)
    if not last_date:
        print("No insertions found.")
        return

    print(f"\nLast posted hearings:")

    c.execute("""
        SELECT 
            date,
            committee,
            title,
            url
        FROM hearings
        WHERE date(date) >= date('now')
        AND date(date_inserted) = ?
        ORDER BY date(date) ASC
    """, (last_date,))

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
