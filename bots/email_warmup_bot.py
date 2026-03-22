#!/usr/bin/env python3
# Email Warmup Bot - Warms up new email domains/inboxes for cold outreach deliverability.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""
log = logging.getLogger(__name__)

WARMUP_SCHEDULE = {
    1:  {"emails_per_day": 5,  "reply_rate": 0.3, "notes": "Start slow"},
    7:  {"emails_per_day": 15, "reply_rate": 0.3, "notes": "Ramp up"},
    14: {"emails_per_day": 30, "reply_rate": 0.2, "notes": "Mid ramp"},
    21: {"emails_per_day": 50, "reply_rate": 0.2, "notes": "Full volume"},
    30: {"emails_per_day": 100,"reply_rate": 0.15,"notes": "Cruise speed"},
}

def generate_warmup_email(day_num):
    topic = claude("Write a 3-sentence professional email about AI trends. Conversational, no selling.",
        f"Email #{day_num} for email warmup. Make it natural.",
        max_tokens=150) or "Just wanted to share some thoughts on AI automation - it's changing how teams work. Happy to connect with fellow practitioners in this space."
    return {"day":day_num,"email":topic,"volume":WARMUP_SCHEDULE.get(min(day_num,30),WARMUP_SCHEDULE[30])["emails_per_day"]}

def get_warmup_status(start_date_str):
    try:
        from datetime import date
        start = datetime.strptime(start_date_str,"%Y-%m-%d").date()
        days = (date.today() - start).days
        schedule = WARMUP_SCHEDULE.get(min(days,30), WARMUP_SCHEDULE[30])
        return {"days_warmed":days,"current_daily_volume":schedule["emails_per_day"],"status":"ON_TRACK" if days > 0 else "STARTING"}
    except:
        return {"status":"UNKNOWN"}

def run():
    status = get_warmup_status("2026-03-01")
    log.info(f"Warmup status: {status}")
    return status

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
