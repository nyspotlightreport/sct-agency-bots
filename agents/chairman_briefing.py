#!/usr/bin/env python3
"""
agents/chairman_briefing.py — Daily Chairman Morning Briefing
Pulls metrics from Supabase, Stripe, and logs. Sends via Pushover.
"""
import os, json, logging
from datetime import datetime, timedelta
import urllib.request as urlreq
import urllib.parse

log = logging.getLogger("briefing")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [BRIEFING] %(message)s")

SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")

def supa_query(table, select="*", filters="", limit=100):
    if not SUPA_URL:
        return []
    try:
        url = f"{SUPA_URL}/rest/v1/{table}?select={select}&{filters}&limit={limit}"
        req = urlreq.Request(url, headers={
            "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"
        })
        with urlreq.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return []

def get_stripe_revenue():
    """Get this month's Stripe revenue"""
    if not STRIPE_KEY:
        return 0
    try:
        now = datetime.utcnow()
        start = int(datetime(now.year, now.month, 1).timestamp())
        url = f"https://api.stripe.com/v1/charges?created[gte]={start}&limit=100"
        req = urlreq.Request(url, headers={
            "Authorization": f"Bearer {STRIPE_KEY}"
        })
        with urlreq.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        total = sum(c["amount"] for c in data.get("data", []) if c["paid"]) / 100
        return total
    except Exception as e:
        log.warning("Stripe query failed: %s", e)
        return 0

def pushover(msg):
    if not PUSH_API or not PUSH_USER:
        log.warning("Pushover credentials not set")
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_API, "user": PUSH_USER,
            "title": "☀️ Morning Briefing", "message": msg
        }).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json", data=data), timeout=10)
    except Exception as e:
        log.error("Pushover failed: %s", e)

def run():
    log.info("=== Chairman Briefing ===")
    now = datetime.utcnow()
    yesterday = (now - timedelta(days=1)).isoformat()

    # Lead count
    leads = supa_query("contacts", "id", f"created_at=gte.{yesterday}")
    lead_count = len(leads)

    # Total leads
    all_leads = supa_query("contacts", "id", "", 10000)
    total_leads = len(all_leads)

    # Emails sent yesterday
    emails = supa_query("outreach_log", "id", f"sent_at=gte.{yesterday}")
    email_count = len(emails)

    # Revenue
    revenue = get_stripe_revenue()

    # Site health
    health = supa_query("site_health_log", "all_passed", f"checked_at=gte.{yesterday}&order=checked_at.desc", 1)
    site_status = "ALL GREEN" if health and health[0].get("all_passed") else "CHECK NEEDED"

    briefing = f"""MORNING BRIEF — {now.strftime('%b %d, %Y')}

💰 Revenue (MTD): ${revenue:,.2f}
👥 New leads (24h): {lead_count} | Total: {total_leads}
✉️ Emails sent (24h): {email_count}
🌐 Site status: {site_status}

Dashboard: https://nyspotlightreport.com
"""

    pushover(briefing)
    log.info("Briefing sent:\n%s", briefing)

if __name__ == "__main__":
    run()
