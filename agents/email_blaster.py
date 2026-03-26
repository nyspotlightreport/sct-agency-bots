#!/usr/bin/env python3
"""
agents/email_blaster.py — Daily Cold Email Outreach
Sends 10 personalized ProFlow emails/day via Gmail SMTP.
Logs to Supabase outreach_log table.
"""
import os, json, smtplib, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import urllib.request as urlreq

log = logging.getLogger("email_blaster")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [EMAIL] %(message)s")

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")

PROFLOW_URL = "https://myproflow.org"
SITE_URL = "https://nyspotlightreport.com"
PHONE = "(631) 892-9817"
RESEND_KEY = os.environ.get("RESEND_API_KEY", "")

def load_prospects():
    """Load prospect list from data/sales/prospects.json"""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "sales", "prospects.json")
    if not os.path.exists(path):
        log.warning("No prospects file found at %s", path)
        return []
    with open(path) as f:
        prospects = json.load(f)
    return prospects

def get_already_sent():
    """Get list of emails already sent from Supabase"""
    if not SUPA_URL:
        return set()
    try:
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/outreach_log?select=recipient_email",
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"}
        )
        with urlreq.urlopen(req, timeout=10) as r:
            rows = json.loads(r.read())
        return {row["recipient_email"] for row in rows}
    except Exception as e:
        log.warning("Could not fetch sent log: %s", e)
        return set()

def personalize_email(prospect):
    """Generate personalized email body"""
    name = prospect.get("name", "there")
    company = prospect.get("company", "your business")
    industry = prospect.get("industry", "your industry")

    subject = f"{name}, automate {company}'s entire content pipeline"
    body = f"""Hi {name},

I came across {company} and thought this might be relevant for your team.

We built ProFlow AI — it automates blog publishing, social media, newsletters, and digital product sales. Our clients run 63+ bots 24/7 with zero daily management.

It starts at $97/mo and pays for itself in the first week:
{PROFLOW_URL}

Worth a quick look? Happy to walk you through a live demo.

Best,
S.C. Thomas
Editor-in-Chief, NY Spotlight Report
{PHONE}
"""
    return subject, body

def send_email(to_email, subject, body):
    """Send email via Resend API (primary) with Netlify relay fallback."""
    # Method 1: Resend API (primary — Gmail is receiving only)
    if not RESEND_KEY:
        log.error("RESEND_API_KEY not set — cannot send email")
        return False
    try:
        resend_data = json.dumps({
            "from": "NY Spotlight Report <outreach@mail.nyspotlightreport.com>",
            "to": [to_email],
            "subject": subject,
            "text": body
        }).encode()
        req = urlreq.Request(
            "https://api.resend.com/emails",
            data=resend_data,
            headers={
                "Authorization": f"Bearer {RESEND_KEY}",
                "Content-Type": "application/json"
            }
        )
        resp = urlreq.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if result.get("id"):
            return True
        log.warning("Resend returned: %s", result)
    except Exception as e:
        log.warning("Resend failed, trying Netlify relay: %s", e)

    # Method 2: Netlify relay fallback
    try:
        data = json.dumps({"to": to_email, "subject": subject, "text": body}).encode()
        req = urlreq.Request(
            f"{SITE_URL}/.netlify/functions/send-email",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-auth-key": PUSH_API
            }
        )
        resp = urlreq.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if result.get("sent"):
            return True
        log.warning("Relay returned: %s", result)
        return False
    except Exception as e:
        log.error("Failed to send to %s: %s", to_email, e)
        return False

def log_to_supabase(recipient, subject, status):
    """Log outreach to Supabase"""
    if not SUPA_URL:
        return
    try:
        data = json.dumps({
            "recipient_email": recipient,
            "subject": subject,
            "status": status,
            "sent_at": datetime.utcnow().isoformat()
        }).encode()
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/outreach_log",
            data=data,
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
        )
        urlreq.urlopen(req, timeout=10)
    except Exception as e:
        log.warning("Supabase log failed: %s", e)

def pushover(msg):
    """Send Pushover notification"""
    if not PUSH_API or not PUSH_USER:
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_API, "user": PUSH_USER,
            "title": "Email Blaster", "message": msg
        }).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json", data=data), timeout=10)
    except:
        pass

import urllib.parse

def run():
    log.info("=== Email Blaster Starting ===")
    prospects = load_prospects()
    if not prospects:
        log.info("No prospects to email")
        pushover("⚠️ No prospects loaded — check data/sales/prospects.json")
        return

    already_sent = get_already_sent()
    unsent = [p for p in prospects if p.get("email") not in already_sent]

    batch = unsent[:10]
    sent_count = 0
    for prospect in batch:
        email = prospect.get("email")
        if not email:
            continue
        subject, body = personalize_email(prospect)
        if send_email(email, subject, body):
            log_to_supabase(email, subject, "sent")
            sent_count += 1
            log.info("Sent to %s", email)
        else:
            log_to_supabase(email, subject, "failed")

    pushover(f"✉️ {sent_count} cold emails sent — {len(unsent) - sent_count} remaining in pipeline")
    log.info("=== Email Blaster Complete: %d sent ===", sent_count)

if __name__ == "__main__":
    run()
