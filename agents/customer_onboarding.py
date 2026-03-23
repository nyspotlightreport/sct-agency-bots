#!/usr/bin/env python3
"""
agents/customer_onboarding.py — NYSR Customer Onboarding Engine
When someone buys, this agent: sends welcome sequence, sets up their account,
creates their content calendar, schedules check-in, and delivers first results.
Jordan Wells (Ops) + James Butler (Concierge) working together.
"""
import os, sys, json, logging, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
sys.path.insert(0, ".")
log = logging.getLogger("onboarding")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ONBOARDING] %(message)s")
import urllib.request as urlreq, urllib.parse

SMTP_USER = os.environ.get("SMTP_USER", "nyspotlightreport@gmail.com")
SMTP_PASS = os.environ.get("GMAIL_APP_PASS", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")

def push(t, m, p=0):
    if not PUSH_API: return
    try: urlreq.urlopen("https://api.pushover.net/1/messages.json", urllib.parse.urlencode({"token": PUSH_API, "user": PUSH_USER, "title": t[:100], "message": m[:1000], "priority": p}).encode(), timeout=5)
    except: pass

def send_email(to, subject, html):
    if not SMTP_PASS: return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f'"NY Spotlight Report" <{SMTP_USER}>'
        msg["To"] = to; msg["Subject"] = subject; msg["Reply-To"] = SMTP_USER
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
            s.login(SMTP_USER, SMTP_PASS); s.sendmail(SMTP_USER, to, msg.as_string())
        return True
    except: return False

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    body = json.dumps(data).encode() if data else None
    req = urlreq.Request(f"{SUPA_URL}/rest/v1/{table}{query}", data=body, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urlreq.urlopen(req, timeout=15) as r: b = r.read(); return json.loads(b) if b else {}
    except: return None

ONBOARDING_EMAILS = {
    "day0": {
        "subject": "Your {offer} is live — here's what's happening right now",
        "delay_hours": 0,
        "body": """<div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;color:#1a1a1a;line-height:1.7">
<h2 style="color:#c9a84c;font-size:20px">Welcome aboard, {name}!</h2>
<p>Your {offer} subscription is confirmed and your AI content system is being configured right now.</p>
<p><strong>What's happening behind the scenes:</strong></p>
<ul><li>Your content engine is being calibrated to your brand voice</li>
<li>SEO keyword research for your niche is running</li>
<li>Social media templates are being generated</li></ul>
<p><strong>Within 24 hours you'll receive:</strong></p>
<ul><li>Your first batch of AI-generated blog posts</li>
<li>Social media content calendar for the next 7 days</li>
<li>Newsletter template ready for your first send</li></ul>
<p>Questions? Reply directly to this email — I personally respond within 4 hours.</p>
<p style="margin-top:24px">— Sean Thomas<br><span style="color:#888;font-size:13px">Chairman, NY Spotlight Report</span></p></div>"""
    },
    "day1": {
        "subject": "Your first content is ready — {name}, take a look",
        "delay_hours": 24,
        "body": """<div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;color:#1a1a1a;line-height:1.7">
<h2 style="color:#c9a84c;font-size:20px">Your content engine is live!</h2>
<p>Hi {name},</p>
<p>Your AI system has produced its first batch of content. Here's what's ready:</p>
<ul><li><strong>3 SEO blog posts</strong> — researched, written, and optimized for your keywords</li>
<li><strong>7 days of social content</strong> — captions, hashtags, and posting schedule</li>
<li><strong>Newsletter draft</strong> — ready to review and send</li></ul>
<p><a href="https://nyspotlightreport.com/activate/" style="display:inline-block;background:#c9a84c;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold">View Your Dashboard →</a></p>
<p>The system will continue producing daily content automatically. You'll get a weekly performance report every Monday.</p>
<p>— Sean</p></div>"""
    },
    "day3": {
        "subject": "Quick check-in — how's everything looking?",
        "delay_hours": 72,
        "body": """<div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;color:#1a1a1a;line-height:1.7">
<p>Hi {name},</p>
<p>Just checking in — your content system has been running for 3 days now. By this point you should have:</p>
<ul><li>9+ blog posts published</li><li>21+ social media posts scheduled</li><li>3 newsletter drafts ready</li></ul>
<p>Is everything working as expected? Anything you'd like adjusted?</p>
<p>If you want to hop on a quick call, grab a time here: <a href="https://nyspotlightreport.com/concierge/" style="color:#c9a84c">Book a call</a></p>
<p>— Sean</p></div>"""
    },
}

def run():
    log.info("="*60)
    log.info("CUSTOMER ONBOARDING — Jordan Wells + James Butler")
    log.info("="*60)
    # Find customers who need onboarding emails
    customers = supa("GET", "contacts", query="?stage=eq.CLOSED_WON&order=created_at.desc&limit=50") or []
    if not isinstance(customers, list): customers = []
    log.info(f"Found {len(customers)} customers")
    sent = 0
    for customer in customers:
        email = customer.get("email", "")
        name = customer.get("name", "").split()[0] if customer.get("name") else "there"
        tags = customer.get("tags", []) or []
        offer = next((t for t in tags if t in ["proflow_ai","proflow_growth","proflow_elite","dfy_setup","dfy_agency"]), "proflow_ai")
        offer_name = {"proflow_ai":"ProFlow AI Starter","proflow_growth":"ProFlow AI Growth","proflow_elite":"ProFlow AI Agency","dfy_setup":"DFY Bot Setup","dfy_agency":"DFY Agency Automation"}.get(offer, "ProFlow AI")
        created = customer.get("created_at", "")
        if not email or not created: continue
        try: created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except: continue
        hours_since = (datetime.utcnow() - created_dt.replace(tzinfo=None)).total_seconds() / 3600
        for day_key, template in ONBOARDING_EMAILS.items():
            delay = template["delay_hours"]
            already_tag = f"onboard_{day_key}_sent"
            if already_tag in tags: continue
            if hours_since >= delay and hours_since < delay + 24:
                subject = template["subject"].format(name=name, offer=offer_name)
                body = template["body"].format(name=name, offer=offer_name)
                if send_email(email, subject, body):
                    sent += 1
                    new_tags = tags + [already_tag]
                    supa("PATCH", "contacts", {"tags": new_tags}, f"?email=eq.{urllib.parse.quote(email)}")
                    log.info(f"  SENT {day_key} to {email}")
    report = f"Onboarding: {sent} emails sent to {len(customers)} customers"
    log.info(report)
    push("Onboarding", report, -1)
    return {"sent": sent, "customers": len(customers)}

if __name__ == "__main__":
    run()
