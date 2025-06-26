# ─── Post upcoming meetings ─────────────────────────────────────────────────────
def post_upcoming(c):
    c.execute("""
            
    SELECT
    id,
    date,
    title,
    committee
    FROM hearings
    WHERE date(date) >= date('now')
    ORDER BY date(date) ASC;       
            
    """)
    rows = c.fetchall()
    if not rows:
        print("No upcoming hearings.")
    else:
        print("Upcoming hearings:")
        for ev_id, ev_date, title, committee in rows:
            print(f"{ev_date} | {committee} | {title}")



def post_last_update(c):
    c.execute("SELECT MAX(date_inserted) FROM hearings")
    row = c.fetchone()
    if not row or row[0] is None:
        print("No insertions found.")
        return

    last_ts = row[0]
    print(f"\nNew Upcoming Hearings (inserted at {last_ts}):\n" + "="*50)

    # 2) Select only those with that timestamp AND in the future
    c.execute("""
        SELECT
            id,
            date,
            title,
            committee
        FROM hearings
        WHERE date_inserted = ?
          AND date(date) >= date('now')
        ORDER BY date(date) ASC
    """, (last_ts,))

    rows = c.fetchall()
    if not rows:
        print("  (None upcoming)")
    else:
        for ev_id, ev_date, title, committee in rows:
            print(f"{ev_date} | {committee} | {title}")