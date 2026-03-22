#!/usr/bin/env python3
"""
bots/alert_intelligence_brain.py
Unified alert system — monitors everything, fires only when broken.
Silence = system healthy. Alert = specific problem + cause + fix.
Sean gets zero noise. Gets actionable intelligence when needed.
Runs every 30 minutes.
"""
import os, json, logging, datetime, urllib.request, urllib.error
log = logging.getLogger("alert_brain")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ALERT BRAIN] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
GH_TOKEN  = os.environ.get("GH_PAT","")
REPO      = "nyspotlightreport/sct-agency-bots"
now       = datetime.datetime.utcnow()
today     = datetime.date.today().isoformat()

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e:
        log.debug(f"Supa {method} {table}: {str(e)[:40]}"); return None

def push_alert(title, msg, priority=0):
    if not PUSH_API: return
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,
                        "message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def log_alert(key, category, severity, title, msg, cause, fix, auto_fixed=False):
    """Log alert to Supabase and push to Chairman if needed."""
    # Check if already alerted in last 4 hours (don't spam)
    four_hrs_ago = (now - datetime.timedelta(hours=4)).isoformat()
    existing = supa("GET","system_alerts","",
        f"?alert_key=eq.{key}&resolved_at=is.null&created_at=gte.{four_hrs_ago}&select=id&limit=1")
    if existing: return  # Already alerted

    supa("POST","system_alerts",{"alert_key":key,"alert_category":category,
        "severity":severity,"title":title,"message":msg,"cause":cause,
        "suggested_fix":fix,"auto_fixed":auto_fixed,"pushover_sent":bool(PUSH_API)})

    if severity in ("critical","warning") and PUSH_API:
        icon = "🚨" if severity=="critical" else "⚠️"
        push_msg = f"{icon} {title}\nCause: {cause}\nFix: {fix}"
        push_alert(f"NYSR {severity.upper()}", push_msg, priority=1 if severity=="critical" else 0)

# ── REVENUE CHECKS ────────────────────────────────────────
def check_revenue():
    revenue_today = supa("GET","revenue_daily","",f"?date=eq.{today}&select=amount") or []
    total = sum(float(r.get("amount",0) or 0) for r in revenue_today) if isinstance(revenue_today,list) else 0

    if total == 0:
        # Check if it's been more than 24 hours since any revenue
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        prev = supa("GET","revenue_daily","",f"?date=eq.{yesterday}&select=amount") or []
        prev_total = sum(float(r.get("amount",0) or 0) for r in prev) if isinstance(prev,list) else 0
        if prev_total == 0:
            log_alert("no_revenue_48h","revenue","warning",
                "No revenue in 48 hours",
                "Store live, PayPal connected, but no sales recorded",
                "Store has been live 0 days — outreach sequences need more time, OR check Ticket Tailor payment configuration",
                "Verify PayPal is fully linked at tickettailor.com → Settings → Payment systems. Check outreach sequence firing.")

    log.info(f"Revenue check: ${total:.2f} today")

# ── PIPELINE HEALTH CHECKS ────────────────────────────────
def check_pipeline():
    contacts = supa("GET","contacts","","?select=stage,score,created_at") or []
    hot   = [c for c in contacts if c.get("stage") in ["HOT","DEMO","PROPOSAL"]]
    leads = [c for c in contacts if c.get("stage") in ["LEAD","PROSPECT","WARM","QUALIFIED"]]

    if len(contacts) < 5:
        log_alert("pipeline_sparse","sales","warning",
            f"Pipeline nearly empty ({len(contacts)} contacts total)",
            "Apollo outreach may not be running or contacts not being added",
            "Check cx_intelligence_bot.py running — it pulls Apollo prospects every cycle. Verify APOLLO_API_KEY is valid.")

    if len(hot) == 0 and len(contacts) > 3:
        log_alert("no_hot_leads","sales","warning",
            "No hot leads in pipeline",
            "All contacts are below 80 lead score threshold",
            "Master sales agent scores leads every 3hrs. Check if webinar registrants are being tagged. Add trigger signals.")

    # Check for stalled proposals (5+ days no response)
    five_days_ago = (now - datetime.timedelta(days=5)).isoformat()
    stalled = supa("GET","appointments","",
        f"?appointment_type=eq.proposal&status=eq.pending&created_at=lt.{five_days_ago}&select=id") or []
    if stalled:
        log_alert("stalled_proposals","sales","warning",
            f"{len(stalled)} proposals stalled 5+ days",
            "Proposals sent but no response — follow-up sequence may not be firing",
            "Master sales agent handles stalled deals — check if close_sequences() is running. High-ticket deals need Sean authority email.")

    log.info(f"Pipeline: {len(contacts)} total | {len(hot)} hot | {len(leads)} warm/cold")

# ── CONTENT CADENCE CHECKS ────────────────────────────────
def check_content():
    today_start = f"{today}T00:00:00"
    events = supa("GET","analytics_events","",
        f"?event_category=eq.content&created_at=gte.{today_start}&select=id") or []

    if len(events) == 0:
        # Check if it's past 10am
        if now.hour >= 10:
            log_alert("no_content_today","content","warning",
                "No content published today",
                "Social scheduler and blog bots may not have fired",
                "Check phase1_daily.yml and sales_daily.yml ran. WordPress bot and Twitter bot should fire at 8am.")

    log.info(f"Content: {len(events)} pieces today")

# ── AUTH TOKEN CHECKS ─────────────────────────────────────
def check_tokens():
    tokens = supa("GET","oauth_tokens","","?select=*") or []
    for token in (tokens if isinstance(tokens,list) else []):
        service = token.get("service","")
        status  = token.get("status","")
        expires = token.get("expires_at")
        refresh = token.get("refresh_at")

        if status == "expired":
            log_alert(f"token_expired_{service}","auth","critical",
                f"{service.upper()} token EXPIRED",
                f"OAuth token for {service} has expired — all automations using it are failing",
                f"Run token_refresh workflow for {service} or manually re-authenticate at nyspotlightreport.com/tokens/",
                False)
        elif expires and refresh:
            try:
                exp = datetime.datetime.fromisoformat(expires.replace("Z","+00:00"))
                days_left = (exp.replace(tzinfo=datetime.timezone.utc) - now.replace(tzinfo=datetime.timezone.utc)).days
                if days_left <= 7:
                    log_alert(f"token_expiring_{service}","auth","warning",
                        f"{service.upper()} token expiring in {days_left} days",
                        f"OAuth token expires {exp.date().isoformat()}",
                        f"Auto-refresh workflow should handle this. If it fails, re-authenticate at /tokens/")
            except: pass

    log.info(f"Token check: {len(tokens if isinstance(tokens,list) else [])} services monitored")

# ── SYSTEM HEALTH CHECKS ──────────────────────────────────
def check_system_health():
    # Check agent runs in last 6 hours
    six_hrs_ago = (now - datetime.timedelta(hours=6)).isoformat()
    runs = supa("GET","agent_run_logs","",f"?started_at=gte.{six_hrs_ago}&select=id") or []

    if len(runs) == 0:
        log_alert("no_agent_runs_6h","system","warning",
            "No agent runs logged in 6+ hours",
            "GitHub Actions workflows may be failing or rate limited",
            "Check github.com/nyspotlightreport/sct-agency-bots/actions for failed runs. Check GH_PAT rate limits.")

    # Check for SLA breaches in CX
    breached = supa("GET","tickets","","?sla_breached=eq.true&resolved_at=is.null&select=id") or []
    if breached:
        log_alert("sla_breach_active","cx","critical",
            f"{len(breached)} tickets with SLA breach unresolved",
            "CX tickets exceeded response time SLA and are still open",
            "cx_director_agent.py handles tickets — check cx_outreach_corp.yml ran successfully.",
            False)

    # Check churn risks
    churn_risks = supa("GET","contacts","","?health_risk=eq.HIGH&stage=eq.CLOSED_WON&select=id,name,lifetime_value") or []
    high_value_churn = [c for c in (churn_risks if isinstance(churn_risks,list) else [])
                       if float(c.get("lifetime_value",0) or 0) >= 500]
    if high_value_churn:
        names = ", ".join(c.get("name","?") for c in high_value_churn[:3])
        log_alert("high_value_churn_risk","retention","critical",
            f"{len(high_value_churn)} high-value clients at churn risk",
            f"Clients {names} have health_risk=HIGH and LTV >= $500",
            "Churn prevention autopilot should have fired. Check customer_health_score_bot.py ran. These clients need immediate attention.",
            False)

    log.info(f"System: {len(runs)} agent runs in 6hrs | {len(breached)} SLA breaches | {len(high_value_churn)} churn risks")

# ── RESOLVE OLD ALERTS ────────────────────────────────────
def resolve_stale_alerts():
    """Auto-resolve alerts older than 24 hours that haven't been re-triggered."""
    day_ago = (now - datetime.timedelta(hours=24)).isoformat()
    resolved = supa("PATCH","system_alerts",
        {"resolved_at":now.isoformat()},
        f"?resolved_at=is.null&created_at=lt.{day_ago}")

# ── MORNING DIGEST ────────────────────────────────────────
def morning_digest():
    """Send 6:55am digest if it hasn't been sent today."""
    if now.hour != 6 or now.minute > 30: return

    contacts  = supa("GET","contacts","","?select=stage") or []
    hot       = len([c for c in contacts if c.get("stage") in ["HOT","DEMO","PROPOSAL"]])
    rev_today = supa("GET","revenue_daily","",f"?date=eq.{today}&select=amount") or []
    total_rev = sum(float(r.get("amount",0) or 0) for r in (rev_today if isinstance(rev_today,list) else []))
    sequences = supa("GET","outreach_sequences","","?status=eq.active&select=id") or []
    tickets   = supa("GET","tickets","","?status=eq.open&select=id") or []

    # Check if digest already sent today
    sent_today = supa("GET","system_alerts","",
        f"?alert_key=eq.morning_digest&created_at=gte.{today}T00:00:00&select=id&limit=1")
    if sent_today: return

    # Get any open critical alerts
    open_alerts = supa("GET","system_alerts","",
        "?resolved_at=is.null&severity=eq.critical&select=title&limit=3") or []
    alert_lines = "\n".join(f"  ⚠️ {a.get('title','?')}" for a in (open_alerts if isinstance(open_alerts,list) else []))

    digest = (f"Good morning, Chairman\n"
              f"Revenue today: ${total_rev:.2f}\n"
              f"Hot leads: {hot} | Active sequences: {len(sequences)}\n"
              f"Open tickets: {len(tickets)}\n"
              + (f"\nNeeds attention:\n{alert_lines}" if alert_lines else "\nAll systems green ✅"))

    push_alert("NYSR Morning Digest", digest, priority=0)
    supa("POST","system_alerts",{"alert_key":"morning_digest","alert_category":"system",
        "severity":"info","title":"Morning Digest Sent",
        "message":digest,"cause":"Scheduled","suggested_fix":"N/A","auto_fixed":True})

# ── MAIN ──────────────────────────────────────────────────
def run():
    log.info("=" * 50)
    log.info("ALERT INTELLIGENCE BRAIN — All Systems Check")
    log.info("Silence = Healthy. Alert = Actionable intelligence.")
    log.info("=" * 50)

    try: check_revenue()
    except Exception as e: log.error(f"Revenue check: {e}")
    try: check_pipeline()
    except Exception as e: log.error(f"Pipeline check: {e}")
    try: check_content()
    except Exception as e: log.error(f"Content check: {e}")
    try: check_tokens()
    except Exception as e: log.error(f"Token check: {e}")
    try: check_system_health()
    except Exception as e: log.error(f"System check: {e}")
    try: resolve_stale_alerts()
    except Exception as e: log.error(f"Resolve stale: {e}")
    try: morning_digest()
    except Exception as e: log.error(f"Morning digest: {e}")

    # Count active unresolved alerts
    open_alerts = supa("GET","system_alerts","","?resolved_at=is.null&select=severity") or []
    critical = len([a for a in (open_alerts if isinstance(open_alerts,list) else []) if a.get("severity")=="critical"])
    warning  = len([a for a in (open_alerts if isinstance(open_alerts,list) else []) if a.get("severity")=="warning"])
    log.info(f"Alert status: {critical} critical | {warning} warnings | System running")

if __name__ == "__main__": run()
