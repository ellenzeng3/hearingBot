from datetime import datetime

# ─── Detail Extractors ───────────────────────────────────────────────────────────

def normalize_date(detail: dict): 
    if date_obj :=  detail.get("date", None):
        return date_obj
    date_obj = detail.get("dates", None)
    return date_obj[0].get("date", None) if date_obj else None

def normalize_title(detail: dict) -> str: 
    return detail.get("title", "") 

def normalize_committee(detail: dict) -> str: 
    if name := detail.get("committeeName", ""):
        return name
    committees = detail.get("committees", "")
    return committees[0].get("name", "") if committees else ""

def parse_date(s):
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except:
            continue
    raise ValueError(f"Unrecognized date format: {s!r}")