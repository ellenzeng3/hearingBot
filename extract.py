from datetime import datetime

# ─── Detail Extractors ───────────────────────────────────────────────────────────

def get_date(detail: dict): 
    if date_obj :=  detail.get("date", None):
        return date_obj
    date_obj = detail.get("dates", None)
    return date_obj[0].get("date", None) if date_obj else None

def get_title(detail: dict) -> str: 
    return detail.get("title", "") 

def get_committee(detail: dict) -> str: 
    if name := detail.get("committeeName", ""):
        return name
    committees = detail.get("committees", "")
    return committees[0].get("name", "") if committees else ""

def get_URL(detail: dict) -> str:
    """
    Returns the URL for the event detail.
    """

    if detail.get("meetingDocuments"):
        meetingDocuments = detail.get("meetingDocuments", [])
        return meetingDocuments[0].get("url", "") if meetingDocuments else ""
    if detail.get("formats"):
        meetingDocuments = detail.get("formats", [])
        return meetingDocuments[1].get("url", "") if meetingDocuments else ""
    return 

def parse_date(s):
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except:
            continue
    raise ValueError(f"Unrecognized date format: {s!r}")