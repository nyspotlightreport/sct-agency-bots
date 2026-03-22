#!/usr/bin/env python3
"""
Client Acquisition Bot — NYSR Agency
Automatically finds and emails potential ProFlow AI clients.
Targets: entrepreneurs, coaches, agency owners, e-commerce brands.
Sends 50-100 personalized cold emails per day.
Expected: 2-5% response rate = 1-5 demos/week from cold outreach.
"""
import os, requests, json, logging, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ClientAcquisitionBot")

APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")
GMAIL_USER = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS","")
HUBSPOT_KEY = os.environ.get("HUBSPOT_API_KEY","")

TARGET_PERSONAS = [
    {"title": "Business Coach", "min_followers": 1000},
    {"title": "Content Creator", "min_followers": 5000},
    {"title": "Entrepreneur", "industry": "Online Media"},
    {"title": "Agency Owner", "industry": "Marketing and Advertising"},
    {"title": "Founder", "industry": "E-Learning"},
    {"title": "Course Creator", "min_followers": 2000},
]

EMAIL_SEQUENCES = {
    "day_0": {
        "subject": "Quick question about your content",
        "body": """Hi {first_name},

I noticed you're building {company} — impressive work.

Quick question: who handles your blog content and newsletter right now?

The reason I ask is that we built an AI system that publishes daily blog posts, weekly newsletters, and daily social media for entrepreneurs automatically. Our clients usually see 300-500% more content output within the first 30 days.

Given what you're building, it might be worth a 10-minute look.

Worth a quick chat?

— S.C. Thomas
NY Spotlight Report
PS: Not a sales pitch — just want to show you what the system does. You'll know in 10 minutes if it's a fit."""
    },
    "day_3": {
        "subject": "Re: Quick question about your content",
        "body": """Hi {first_name},

Following up on my note from a few days ago.

I put together a short overview of exactly what we'd build for someone in {industry}:
→ nyspotlightreport.com/proflow/

If you're spending more than 5 hours a week on content — or not doing it at all because you don't have time — this pays for itself within 60 days.

Happy to show you the live dashboard of what a client in your space looks like.

15 minutes this week?

— S.C."""
    },
    "day_7": {
        "subject": "Last note — free audit",
        "body": """Hi {first_name},

Last message from me on this.

I'll do a free content audit for {company} — I'll tell you exactly what content opportunities you're missing and what a 90-day automated content system would look like for your specific situation.

No cost. No obligation. Takes 30 minutes.

If that's useful: nyspotlightreport.com/proflow/
If not, no worries — I'll stop reaching out.

Either way, good luck with {company}.

— S.C. Thomas"""
    }
}

def get_prospects(limit=50):
    if not APOLLO_KEY:
        log.warning("No APOLLO_API_KEY — returning empty list")
        return []
    leads = []
    for persona in TARGET_PERSONAS[:2]:
        payload = {
            "api_key": APOLLO_KEY,
            "q_person_titles": [persona["title"]],
            "person_locations": ["United States"],
            "page": 1, "per_page": limit//len(TARGET_PERSONAS),
            "contact_email_status": ["verified"],
        }
        r = requests.post("https://api.apollo.io/api/v1/mixed_people/search",
            json=payload, timeout=30)
        if r.status_code == 200:
            leads.extend(r.json().get("people",[]))
        time.sleep(0.5)
    return leads[:limit]

def add_to_hubspot(lead):
    if not HUBSPOT_KEY: return
    requests.post(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {HUBSPOT_KEY}", "Content-Type": "application/json"},
        json={"properties": {
            "email": lead.get("email",""),
            "firstname": lead.get("first_name",""),
            "lastname": lead.get("last_name",""),
            "company": lead.get("organization",{}).get("name","") if isinstance(lead.get("organization"),dict) else "",
            "jobtitle": lead.get("title",""),
            "hs_lead_status": "NEW",
        }}, timeout=10)

def send_sequence_email(to_email, first_name, company, industry, day):
    seq = EMAIL_SEQUENCES.get(f"day_{day}")
    if not seq or not GMAIL_PASS: return False
    msg = MIMEMultipart()
    msg["From"] = f"S.C. Thomas <{GMAIL_USER}>"
    msg["To"]   = to_email
    msg["Subject"] = seq["subject"]
    body = seq["body"].format(
        first_name=first_name or "there",
        company=company or "your business",
        industry=industry or "your industry"
    )
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        log.info(f"  ✅ Day-{day} email → {to_email}")
        return True
    except Exception as e:
        log.error(f"  ❌ {to_email}: {e}")
        return False

if __name__ == "__main__":
    prospects = get_prospects(50)
    log.info(f"Found {len(prospects)} prospects")
    sent = 0
    for p in prospects[:20]:  # limit daily sends
        email = p.get("email","")
        if not email: continue
        add_to_hubspot(p)
        fn = p.get("first_name","")
        co = p.get("organization",{}).get("name","") if isinstance(p.get("organization"),dict) else ""
        ok = send_sequence_email(email, fn, co, "business", 0)
        if ok: sent += 1
        time.sleep(2)
    log.info(f"Sent {sent} day-0 emails. Expected responses: {max(1,int(sent*.03))}-{max(2,int(sent*.05))}")
