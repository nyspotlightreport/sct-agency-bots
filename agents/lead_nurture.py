#!/usr/bin/env python3
"""
agents/lead_nurture.py — Automated Lead Nurture Drip
Queries Supabase for leads by nurture_stage, sends stage-appropriate emails.
Stage 0 (Day 0): Playbook + intro
Stage 1 (Day 2): Case study + stats
Stage 2 (Day 5): CTA + checkout link
"""
import os, json, smtplib, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import urllib.request as urlreq
import urllib.parse

log = logging.getLogger("lead_nurture")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NURTURE] %(message)s")

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")

SITE = "https://nyspotlightreport.com"
PHONE = "(631) 892-9817"

EMAILS = {
    0: {
        "subject": "Your free Content Automation Playbook",
        "body": """Hi {name},

Thanks for checking out NY Spotlight Report! Here's the playbook we promised:

{site}/downloads/proflow-playbook/

ProFlow AI automates everything: daily blog posts, social media, newsletters, and digital product sales. Zero manual work.

Here's what it does for you:
- Publishes content across 6+ platforms daily
- Runs 63+ bots 24/7
- Sells digital products on autopilot

Questions? Call our AI receptionist: {phone}

Best,
S.C. Thomas
NY Spotlight Report
"""
    },
    1: {
        "subject": "What we built for NY Spotlight Report (real numbers)",
        "body": """Hi {name},

Quick follow-up — here's what ProFlow AI built for our own operation:

- 63 active bots running 24/7
- 10,000+ posts published automatically
- $0 daily management time
- Multiple revenue streams on autopilot

We're offering the same system to select businesses.

See the full breakdown: {site}/proflow/

Talk soon,
S.C. Thomas
"""
    },
    2: {
        "subject": "Ready to automate? Plans from $97/mo",
        "body": """Hi {name},

Last email in this series — just wanted to make sure you saw ProFlow AI.

Three plans:
- Starter: $97/mo — daily blog + 3 social platforms + digital store
- Growth: $297/mo — everything + newsletter + YouTube Shorts + syndication
- Agency: $497/mo — full automation + KDP + POD + VPS stack

Get started: {site}/proflow/#pricing

Or call our AI receptionist to learn more: {phone}

Best,
S.C. Thomas
Chairman, NY Spotlight Report
"""
    }
}

def get_leads(stage):
    """Get leads at a specific nurture stage"""
    if not SUPA_URL:
        return []
    try:
        url = f"{SUPA_URL}/rest/v1/contacts?nurture_stage=eq.{stage}&select=email,full_name,created_at&limit=50"
        req = urlreq.Request(url, headers={
            "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"
        })
        with urlreq.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning("Failed to fetch stage %d leads: %s", stage, e)
        return []

def should_send(lead, stage):
    """Check if enough time has passed for this stage"""
    created = lead.get("created_at", "")
    if not created:
        return stage == 0
    try:
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        now = datetime.now(created_dt.tzinfo) if created_dt.tzinfo else datetime.utcnow()
        days_since = (now - created_dt).days
        if stage == 0:
            return True
        elif stage == 1:
            return days_since >= 2
        elif stage == 2:
            return days_since >= 5
    except:
        return False
    return False

SITE_URL = "https://nyspotlightreport.com"

def send_email(to_email, subject, body):
    # Method 1: Netlify relay (bypasses GitHub IP blocks)
    try:
        data = json.dumps({"to": to_email, "subject": subject, "text": body}).encode()
        req = urlreq.Request(
            f"{SITE_URL}/.netlify/functions/send-email",
            data=data,
            headers={"Content-Type": "application/json", "x-auth-key": PUSH_API}
        )
        resp = urlreq.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if result.get("sent"):
            return True
    except Exception as e:
        log.warning("Relay failed, trying direct: %s", e)
    # Method 2: Direct SMTP fallback
    if not GMAIL_USER or not GMAIL_PASS:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = f"S.C. Thomas <{GMAIL_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        log.error("Send failed for %s: %s", to_email, e)
        return False

def update_stage(email, new_stage):
    if not SUPA_URL:
        return
    try:
        data = json.dumps({"nurture_stage": new_stage}).encode()
        encoded_email = urllib.parse.quote(email)
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/contacts?email=eq.{encoded_email}",
            data=data, method="PATCH",
            headers={
                "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json", "Prefer": "return=minimal"
            }
        )
        urlreq.urlopen(req, timeout=10)
    except Exception as e:
        log.warning("Stage update failed for %s: %s", email, e)

def pushover(msg):
    if not PUSH_API or not PUSH_USER:
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_API, "user": PUSH_USER,
            "title": "Lead Nurture", "message": msg
        }).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json", data=data), timeout=10)
    except:
        pass

def run():
    log.info("=== Lead Nurture Starting ===")
    total_sent = 0

    for stage in [0, 1, 2]:
        leads = get_leads(stage)
        template = EMAILS[stage]

        for lead in leads:
            email = lead.get("email", "")
            name = lead.get("full_name", "there") or "there"
            if not email or not should_send(lead, stage):
                continue

            subject = template["subject"]
            body = template["body"].format(name=name, site=SITE, phone=PHONE)

            if send_email(email, subject, body):
                update_stage(email, stage + 1)
                total_sent += 1
                log.info("Stage %d email sent to %s", stage, email)

    pushover(f"🌱 Lead nurture: {total_sent} emails sent across 3 stages")
    log.info("=== Lead Nurture Complete: %d sent ===", total_sent)

if __name__ == "__main__":
    run()
