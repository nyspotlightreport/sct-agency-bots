#!/usr/bin/env python3
"""
agents/chairman_briefing.py — Daily Chairman Morning Briefing
Pulls metrics from Supabase, Stripe, workflow runs, and site health.
Sends comprehensive daily report via Pushover.
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
GH_PAT = os.environ.get("GH_PAT", "")

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
    except Exception as e:
        log.warning("Supabase query %s failed: %s", table, e)
        return []

def supa_count(table, filters=""):
    """Get row count from Supabase table"""
    if not SUPA_URL:
        return 0
    try:
        url = f"{SUPA_URL}/rest/v1/{table}?select=id&{filters}"
        req = urlreq.Request(url, headers={
            "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
            "Prefer": "count=exact", "Range": "0-0"
        })
        with urlreq.urlopen(req, timeout=10) as r:
            content_range = r.headers.get("Content-Range", "")
            if "/" in content_range:
                return int(content_range.split("/")[1])
        return 0
    except:
        return 0

def get_stripe_revenue():
    if not STRIPE_KEY:
        return 0
    try:
        now = datetime.utcnow()
        start = int(datetime(now.year, now.month, 1).timestamp())
        url = f"https://api.stripe.com/v1/charges?created[gte]={start}&limit=100"
        req = urlreq.Request(url, headers={"Authorization": f"Bearer {STRIPE_KEY}"})
        with urlreq.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        total = sum(c["amount"] for c in data.get("data", []) if c["paid"]) / 100
        return total
    except Exception as e:
        log.warning("Stripe query failed: %s", e)
        return 0

def get_workflow_health():
    """Check recent GitHub Actions failures"""
    if not GH_PAT:
        return "N/A"
    try:
        url = "https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/runs?per_page=20&status=failure"
        req = urlreq.Request(url, headers={
            "Authorization": f"Bearer {GH_PAT}",
            "Accept": "application/vnd.github.v3+json"
        })
        with urlreq.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        failures_24h = 0
        cutoff = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        for run in data.get("workflow_runs", []):
            if run.get("created_at", "") > cutoff:
                failures_24h += 1
        return f"{failures_24h} failures" if failures_24h > 0 else "ALL GREEN"
    except:
        return "CHECK NEEDED"

def pushover(msg):
    if not PUSH_API or not PUSH_USER:
        log.warning("Pushover credentials not set")
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_API, "user": PUSH_USER,
            "title": "☀️ Chairman Morning Briefing", "message": msg,
            "priority": 0
        }).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json", data=data), timeout=10)
    except Exception as e:
        log.error("Pushover failed: %s", e)

def run():
    log.info("=== Chairman Briefing ===")
    now = datetime.utcnow()
    yesterday = (now - timedelta(days=1)).isoformat()

    # --- LEADS ---
    new_leads = supa_query("contacts", "id", f"created_at=gte.{yesterday}")
    total_leads = supa_count("contacts")

    # --- OUTREACH ---
    emails_sent = supa_query("outreach_log", "id", f"sent_at=gte.{yesterday}")
    total_outreach = supa_count("outreach_log")

    # --- BRAND MENTIONS ---
    new_mentions = supa_query("brand_mentions", "id", f"created_at=gte.{yesterday}")
    total_mentions = supa_count("brand_mentions")

    # --- SUBSCRIBERS ---
    new_subs = supa_query("subscribers", "id", f"created_at=gte.{yesterday}")
    total_subs = supa_count("subscribers")

    # --- REVENUE ---
    revenue = get_stripe_revenue()

    # --- SITE HEALTH ---
    health = supa_query("site_health_log", "all_passed", f"checked_at=gte.{yesterday}&order=checked_at.desc", 1)
    site_status = "ALL GREEN" if health and health[0].get("all_passed") else "CHECK NEEDED"

    # --- WORKFLOW HEALTH ---
    wf_health = get_workflow_health()

    briefing = f"""MORNING BRIEF — {now.strftime('%a %b %d, %Y')}

💰 REVENUE
   Stripe MTD: ${revenue:,.2f}

👥 PIPELINE
   New leads (24h): {len(new_leads)}
   Total contacts: {total_leads:,}

✉️ OUTREACH
   Emails sent (24h): {len(emails_sent)}
   Total outreach: {total_outreach:,}

📰 BRAND
   New mentions (24h): {len(new_mentions)}
   Total mentions: {total_mentions:,}

📬 NEWSLETTER
   New subscribers (24h): {len(new_subs)}
   Total subscribers: {total_subs:,}

🌐 SYSTEMS
   Site: {site_status}
   Workflows: {wf_health}

🔗 https://nyspotlightreport.com/command/"""

    pushover(briefing)
    log.info("Briefing sent:\n%s", briefing)

if __name__ == "__main__":
    run()
