#!/usr/bin/env python3
"""
Fetch and print all upcoming hearings and committee meetings
for the current U.S. Congress, along with their full descriptions.
"""

import os 
from datetime import datetime, date, timedelta
import requests
from pathlib import Path
from dotenv import load_dotenv

# ─── Configuration ────────────────────────────────────────────────────────────

CONGRESS = 119
HEARING_LIST_URL   = f"https://api.congress.gov/v3/hearing/{CONGRESS}"
MEETING_LIST_URL   = f"https://api.congress.gov/v3/committee-meeting/{CONGRESS}"
today = date.today().isoformat()  # e.g. "2025-06-18"

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("CONGRESS_API_KEY")
HEADERS = {"X-Api-Key": API_KEY}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def fetch_info(type, url, output) -> str:
    
    r = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    r.raise_for_status()
    if type == "meeting":
        hearing = r.json().get("committeeMeeting", {})
    elif type == "hearing":
        hearing = r.json().get("hearing", {})


    # meeting: 
    if output == "date":
        if type == "meeting":
            hearing = r.json().get("committeeMeeting", {})
            date_raw = hearing.get("date", "N/A")
            date_str = date_raw.split("T")[0]
            return date_str 
        
        # hearing: 
        hearing = r.json().get("hearing", {})
        dates = hearing.get("dates", [])
        date_str = dates[0].get("date")
        return date_str
    else:
        title = hearing["title"]
        committees = hearing.get("committees", [])
        if committees:
            committee_name = committees[0].get("name")
        else:
            committee_name = "N/A"

    return title, committee_name



def fetch_all(type) -> list:
    """
    Fetch all hearings or committee meetings for the current Congress.
    """
    # params = {
    #     "format": "json",
    #     "meetingStatus": "Scheduled",
    #     "limit": 250,
    #     # "fromDate": today
    # }
    if type == "hearing":
        url = HEARING_LIST_URL
    elif type == "meeting":
        url = MEETING_LIST_URL
    else:
        raise ValueError("Invalid type. Use 'hearing' or 'meeting'.")

    r = requests.get(url, headers=HEADERS, timeout=10)

    # r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    if type == "hearing":
        return r.json().get("hearings", [])
    else:
        return r.json().get("committeeMeetings", [])



# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    meetings = fetch_all("meeting")
    print(meetings)
    # hearings = fetch_all("hearing")  

    for m in meetings:

        try:
            chamber = m["chamber"].lower()  # "house" or "senate"
            event_id  = m["eventId"] 
            url     = m["url"]
            # update_date = m["updateDate"]

            date_str = fetch_info("meeting", url, "date") 
            date_format = "%Y-%m-%d"
            date_obj = datetime.strptime(date_str, date_format).date()

            if date_obj < date.today():
                continue   

            title, committee = fetch_info("meeting", url, "title")
            print(f'{committee}: "{title}" on {date_str}')

        except Exception as e:
            print(f"Error meeting {m}: {e}")
            continue

    # {'chamber': 'House', 'congress': 119, 
    # 'jacketNumber': 60447, 'updateDate': '2025-06-18T22:51:15Z', 
    # 'url': 'https://api.congress.gov/v3/hearing/119/house/60447'}, 

    # print(f"\nHearings scheduled for today ({len(hearings)})")
    # for h in hearings:
    #     try:
    #         chamber = h["chamber"].lower()  # "house" or "senate"
    #         jacket  = h["jacketNumber"] 
    #         url     = h["url"]
    #         update_date = h["updateDate"]
    #         print(update_date)

    #         date_str = fetch_date(chamber, jacket)
    #         date_format = "%Y-%m-%d"
    #         date_obj = datetime.strptime(date_str, date_format).date()

    #         if date_obj < date.today():
    #             continue   

    #         title, committee = fetch_description(chamber, jacket)
    #         print(f'{committee}: "{title}" on {date_str}')


    #     except Exception as e:
    #         print(f"Error hearing {h}: {e}")
    #         continue  

main()