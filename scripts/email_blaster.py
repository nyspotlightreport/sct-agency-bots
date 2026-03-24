#!/usr/bin/env python3
"""
Email Blaster — 10 personalized cold emails/day via Gmail SMTP
Pulls prospects from Apollo API, runs 3-touch sequence over 7 days.
Logs all sends to data/sales/outreach_log.json.
"""
import os
import json
import smtplib
import ssl
import time
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────
GMAIL_USER = os.environ.get("GMAIL_USER", "nyspotlightreport@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS", "")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")
DAILY_LIMIT = 10
LOG_FILE = Path(__file__).parent.parent / "data" / "sales" / "outreach_log.json"

# ── Email Sequence ──────────────────────────────────────
SEQUENCE = [
    {
        "touch": 1,
        "delay_days": 0,
        "subject": "Cut your content team cost by 90%",
        "body": """Hi {first_name},

I replaced a $4,000/month content team with 63 AI bots.

The system now publishes daily blogs, weekly newsletters, and posts to 6 social platforms — automatically.

Total cost: $70/month.

If you're spending more than that on content, I'd love to show you how it works.

15-minute call? nyspotlightreport.com/proflow/

Or call our AI receptionist: (631) 892-9817

— SC Thomas
NY Spotlight Report"""
    },
    {
        "touch": 2,
        "delay_days": 3,
        "subject": "Re: Cut your content team cost by 90%",
        "body": """Hi {first_name},

Just following up — wanted to make sure this landed.

Quick question: what does your current content operation cost monthly? (Team, tools, agencies combined)

I ask because most people I talk to are at $2,000-8,000/month. Our system replaces all of it for $70.

Happy to walk you through the architecture — no pitch, just a look at what we built.

nyspotlightreport.com/proflow/

— SC Thomas"""
    },
    {
        "touch": 3,
        "delay_days": 7,
        "subject": "Last note from NY Spotlight Report",
        "body": """Hi {first_name},

Last time reaching out.

If content cost and consistency aren't a problem, no worries at all.

If they ever are — nyspotlightreport.com/proflow/ — the full system is there.

Wishing you the best,
— SC Thomas"""
    },
]


def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return {"sent": [], "prospects": []}


def save_log(log):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(log, indent=2, default=str))


def fetch_prospects(count=10):
    """Pull fresh prospects from Apollo API."""
    if not APOLLO_KEY:
        print("No APOLLO_API_KEY — using test mode")
        return []

    payload = json.dumps({
        "api_key": APOLLO_KEY,
        "q_organization_num_employees_ranges": ["11,50", "51,200"],
        "person_titles": ["content manager", "marketing director", "head of marketing",
                          "growth lead", "founder", "ceo", "marketing manager"],
        "person_locations": ["United States"],
        "page": 1,
        "per_page": count,
    }).encode()

    req = urllib.request.Request(
        "https://api.apollo.io/v1/mixed_people/search",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            people = data.get("people", [])
            prospects = []
            for p in people:
                email = p.get("email")
                if not email:
                    continue
                prospects.append({
                    "email": email,
                    "first_name": p.get("first_name", email.split("@")[0]),
                    "last_name": p.get("last_name", ""),
                    "title": p.get("title", ""),
                    "company": p.get("organization", {}).get("name", ""),
                    "fetched_at": datetime.utcnow().isoformat(),
                })
            return prospects
    except Exception as e:
        print(f"Apollo API error: {e}")
        return []


def send_email(to_email, subject, body):
    """Send a single email via Gmail SMTP."""
    if not GMAIL_PASS:
        print(f"  DRY RUN (no GMAIL_APP_PASS): {to_email} — {subject}")
        return True

    msg = MIMEMultipart("alternative")
    msg["From"] = f"SC Thomas <{GMAIL_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = GMAIL_USER
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        print(f"  SENT: {to_email} — {subject}")
        return True
    except Exception as e:
        print(f"  FAILED: {to_email} — {e}")
        return False


def run():
    log = load_log()
    sent_emails = {s["email"] for s in log["sent"]}
    now = datetime.utcnow()
    sent_today = 0

    # ── Send follow-ups first (Touch 2 and 3) ──
    for record in log["sent"]:
        if sent_today >= DAILY_LIMIT:
            break
        touch = record.get("touch", 1)
        sent_at = datetime.fromisoformat(record["sent_at"])

        if touch == 1 and (now - sent_at).days >= 3:
            # Check if touch 2 already sent
            if any(s["email"] == record["email"] and s.get("touch") == 2 for s in log["sent"]):
                continue
            seq = SEQUENCE[1]
            body = seq["body"].format(first_name=record.get("first_name", "there"))
            if send_email(record["email"], seq["subject"], body):
                log["sent"].append({
                    "email": record["email"],
                    "first_name": record.get("first_name"),
                    "touch": 2,
                    "subject": seq["subject"],
                    "sent_at": now.isoformat(),
                })
                sent_today += 1

        elif touch == 2 and (now - sent_at).days >= 4:
            # Check if touch 3 already sent
            if any(s["email"] == record["email"] and s.get("touch") == 3 for s in log["sent"]):
                continue
            seq = SEQUENCE[2]
            body = seq["body"].format(first_name=record.get("first_name", "there"))
            if send_email(record["email"], seq["subject"], body):
                log["sent"].append({
                    "email": record["email"],
                    "first_name": record.get("first_name"),
                    "touch": 3,
                    "subject": seq["subject"],
                    "sent_at": now.isoformat(),
                })
                sent_today += 1

    # ── Send new outreach (Touch 1) ──
    remaining = DAILY_LIMIT - sent_today
    if remaining > 0:
        prospects = fetch_prospects(remaining)
        for p in prospects:
            if p["email"] in sent_emails:
                continue
            seq = SEQUENCE[0]
            body = seq["body"].format(first_name=p["first_name"])
            if send_email(p["email"], seq["subject"], body):
                log["sent"].append({
                    "email": p["email"],
                    "first_name": p["first_name"],
                    "company": p.get("company", ""),
                    "title": p.get("title", ""),
                    "touch": 1,
                    "subject": seq["subject"],
                    "sent_at": now.isoformat(),
                })
                sent_today += 1
                time.sleep(5)  # 5s delay between sends

    save_log(log)
    print(f"\nDone: {sent_today} emails sent today. Total in log: {len(log['sent'])}")


if __name__ == "__main__":
    run()
