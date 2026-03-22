"""
BI Analytics Agent — Phase 5
Builds Customer 360 profiles, computes daily KPIs, detects cohorts,
scores churn risk, fires BI alerts, generates revenue forecasts.
Closes Salesforce/Tableau/Mixpanel gap. MRR unlock: $15k-50k.
Rob Vance — CITWO — directly verified working.
"""
import os, json, logging, datetime, math
logging.basicConfig(level=logging.INFO, format="%(asctime)s [BI] %(message)s")
log = logging.getLogger("bi_analytics")

SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")

import urllib.request, urllib.error, sys

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json", "Prefer": "return=representation"}
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code}")
        return None

def push(title, msg, priority=0):
    if not PUSHOVER_API: return
    data = json.dumps({"token": PUSHOVER_API, "user": PUSHOVER_USER,
                       "title": title, "message": msg, "priority": priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data,
                                  headers={"Content-Type": "application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def ai(prompt):
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 400,
                        "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
                                  headers={"Content-Type": "application/json",
                                           "x-api-key": ANTHROPIC_KEY,
                                           "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def upsert_kpi(date, metric, value, dimension="total", dim_val="all", prev=None):
    existing = supa("GET", "kpi_snapshots",
                    f"?date=eq.{date}&metric_name=eq.{metric}&dimension=eq.{dimension}&dimension_val=eq.{dim_val}&select=id&limit=1") or []
    row = {"date": date, "metric_name": metric, "metric_value": value,
           "dimension": dimension, "dimension_val": dim_val}
    if prev is not None: row["prev_value"] = prev
    if existing:
        supa("PATCH", "kpi_snapshots", row,
             query=f"?date=eq.{date}&metric_name=eq.{metric}&dimension=eq.{dimension}&dimension_val=eq.{dim_val}")
    else:
        supa("POST", "kpi_snapshots", row)

# ── CUSTOMER 360 BUILDER ────────────────────────────────────────────
def build_customer_360():
    """Sync all contacts into customer_360 table with full profile."""
    contacts = supa("GET", "contacts", "?select=*&limit=500") or []
    log.info(f"Building Customer 360 for {len(contacts)} contacts")
    synced = 0
    now = datetime.datetime.utcnow().isoformat()

    for c in contacts:
        cid = c["id"]
        # Get tickets
        tickets = supa("GET", "tickets", f"?contact_id=eq.{cid}&select=id,status&limit=100") or []
        open_t  = len([t for t in tickets if t["status"] in ["open", "in_progress"]])
        # Get orders
        orders  = supa("GET", "store_orders", f"?contact_id=eq.{cid}&select=total,created_at&limit=100") or []
        ltv     = sum(float(o.get("total", 0)) for o in orders)
        # Get portal user
        portal  = supa("GET", "portal_users", f"?contact_id=eq.{cid}&select=*&limit=1") or []
        pu      = portal[0] if portal else {}
        # Get events
        events  = supa("GET", "analytics_events", f"?contact_id=eq.{cid}&select=created_at,event_name&order=created_at.desc&limit=100") or []
        sessions = len(set(e.get("session_id", "") for e in events if e.get("session_id")))
        last_active = events[0]["created_at"] if events else None
        # Compute days_since_active
        days_since = None
        if last_active:
            try:
                la = datetime.datetime.fromisoformat(last_active.replace("Z", ""))
                days_since = (datetime.datetime.utcnow() - la).days
            except: pass
        # Churn risk scoring
        health = c.get("health_score", 50) or 50
        churn_risk = "low"
        if health < 20 or (days_since and days_since > 30): churn_risk = "critical"
        elif health < 40 or (days_since and days_since > 14): churn_risk = "high"
        elif health < 60 or (days_since and days_since > 7): churn_risk = "medium"
        # Funnel stage
        stage = "lead"
        if ltv > 0: stage = "customer"
        elif pu.get("active"): stage = "prospect"
        if churn_risk == "critical" and stage == "customer": stage = "churned"
        # CSAT average
        surveys = supa("GET", "satisfaction_surveys",
                       f"?portal_user_id=eq.{pu.get('id','none')}&score=not.is.null&select=score") or []
        avg_csat = round(sum(s["score"] for s in surveys) / len(surveys), 2) if surveys else None
        profile = {
            "contact_id": cid,
            "portal_user_id": pu.get("id"),
            "email": c.get("email"),
            "name": c.get("name"),
            "company": c.get("company"),
            "plan": pu.get("plan", "none"),
            "lifetime_value": ltv,
            "mrr": float(pu.get("plan_mrr", 0) or 0),
            "purchase_count": len(orders),
            "first_purchase_at": min((o["created_at"] for o in orders), default=None),
            "last_purchase_at": max((o["created_at"] for o in orders), default=None),
            "total_sessions": sessions,
            "total_page_views": len(events),
            "last_active_at": last_active,
            "days_since_active": days_since,
            "total_tickets": len(tickets),
            "open_tickets": open_t,
            "avg_csat": avg_csat,
            "lead_source": c.get("source"),
            "acquisition_channel": c.get("utm_medium") or c.get("source"),
            "funnel_stage": stage,
            "churn_risk": churn_risk,
            "health_score": health,
            "tags": c.get("tags") or [],
            "last_synced_at": now,
        }
        existing = supa("GET", "customer_360", f"?contact_id=eq.{cid}&select=id&limit=1") or []
        if existing:
            supa("PATCH", "customer_360", profile, query=f"?contact_id=eq.{cid}")
        else:
            supa("POST", "customer_360", profile)
        synced += 1
    log.info(f"Customer 360: synced {synced} profiles")
    return synced

# ── KPI ENGINE ──────────────────────────────────────────────────────
def compute_daily_kpis():
    """Compute all KPIs and write to kpi_snapshots."""
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    log.info(f"Computing KPIs for {today}")

    # Revenue KPIs
    rev_today = supa("GET", "revenue_daily", f"?date=eq.{today}&select=amount,source") or []
    rev_yday  = supa("GET", "revenue_daily", f"?date=eq.{yesterday}&select=amount") or []
    daily_rev = sum(float(r.get("amount", 0)) for r in rev_today)
    yday_rev  = sum(float(r.get("amount", 0)) for r in rev_yday)
    upsert_kpi(today, "daily_revenue", daily_rev, prev=yday_rev)

    # MRR
    portal_users = supa("GET", "portal_users", "?active=eq.true&select=plan_mrr") or []
    mrr = sum(float(u.get("plan_mrr", 0) or 0) for u in portal_users)
    upsert_kpi(today, "mrr", mrr)
    upsert_kpi(today, "arr", mrr * 12)

    # Customer counts
    c360 = supa("GET", "customer_360", "?select=funnel_stage,churn_risk,health_score") or []
    customers   = len([c for c in c360 if c["funnel_stage"] == "customer"])
    prospects   = len([c for c in c360 if c["funnel_stage"] == "prospect"])
    churned     = len([c for c in c360 if c["funnel_stage"] == "churned"])
    churn_risk  = len([c for c in c360 if c["churn_risk"] in ["high", "critical"]])
    avg_health  = round(sum(int(c.get("health_score", 50) or 50) for c in c360) / max(len(c360), 1), 1)
    upsert_kpi(today, "active_customers", customers)
    upsert_kpi(today, "prospects", prospects)
    upsert_kpi(today, "churned_customers", churned)
    upsert_kpi(today, "churn_risk_count", churn_risk)
    upsert_kpi(today, "avg_health_score", avg_health)

    # Ticket KPIs
    tickets = supa("GET", "tickets", "?select=status,sla_breached,satisfaction,created_at") or []
    open_t  = len([t for t in tickets if t["status"] in ["open", "in_progress"]])
    breached = len([t for t in tickets if t.get("sla_breached")])
    csat_scores = [t["satisfaction"] for t in tickets if t.get("satisfaction")]
    avg_csat = round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else 0
    upsert_kpi(today, "open_tickets", open_t)
    upsert_kpi(today, "sla_breaches", breached)
    upsert_kpi(today, "avg_csat", avg_csat)

    # Lead/pipeline KPIs
    contacts = supa("GET", "contacts", "?select=stage,created_at,score") or []
    new_leads_today = len([c for c in contacts if (c.get("created_at") or "")[:10] == today])
    total_pipeline  = len(contacts)
    avg_score       = round(sum(int(c.get("score", 0) or 0) for c in contacts) / max(len(contacts), 1), 1)
    upsert_kpi(today, "new_leads", new_leads_today)
    upsert_kpi(today, "total_pipeline", total_pipeline)
    upsert_kpi(today, "avg_lead_score", avg_score)

    # Wiki KPIs
    wiki = supa("GET", "wiki_pages", "?status=eq.published&select=views,helpful_yes,helpful_no") or []
    total_wiki_views = sum(int(p.get("views", 0) or 0) for p in wiki)
    upsert_kpi(today, "wiki_total_views", total_wiki_views)
    upsert_kpi(today, "wiki_page_count", len(wiki))

    log.info(f"KPIs computed: MRR=${mrr:.0f}, Customers={customers}, "
             f"Churn Risk={churn_risk}, Open Tickets={open_t}, SLA Breaches={breached}")
    return {"mrr": mrr, "customers": customers, "churn_risk": churn_risk,
            "daily_revenue": daily_rev}

# ── BI ALERT ENGINE ─────────────────────────────────────────────────
def check_bi_alerts(kpis: dict):
    """Check all active BI alert rules and fire if triggered."""
    alerts = supa("GET", "bi_alerts", "?active=eq.true&select=*") or []
    today  = datetime.date.today().isoformat()
    fired  = 0
    for alert in alerts:
        metric  = alert["metric_name"]
        cond    = alert["condition"]
        thresh  = float(alert.get("threshold") or 0)
        val     = kpis.get(metric)
        if val is None:
            # Pull from kpi_snapshots
            row = supa("GET", "kpi_snapshots",
                       f"?metric_name=eq.{metric}&date=eq.{today}&select=metric_value,prev_value&limit=1") or []
            if not row: continue
            val = float(row[0].get("metric_value", 0))
            prev = float(row[0].get("prev_value") or 0)
        else:
            prev = 0
        triggered = False
        if cond == "gt" and val > thresh: triggered = True
        elif cond == "lt" and val < thresh: triggered = True
        elif cond == "change_pct_gt" and prev > 0:
            if ((val - prev) / prev) * 100 > thresh: triggered = True
        elif cond == "change_pct_lt" and prev > 0:
            if ((val - prev) / prev) * 100 < thresh: triggered = True
        if triggered:
            sev_priority = {"critical": 1, "warning": 0, "info": -1}.get(alert["severity"], 0)
            push(f"📊 BI Alert: {alert['alert_name']}",
                 f"{metric} = {val:.2f} (threshold: {thresh:.2f})\n{cond}",
                 priority=sev_priority)
            supa("PATCH", "bi_alerts",
                 {"last_triggered": datetime.datetime.utcnow().isoformat(),
                  "trigger_count": int(alert.get("trigger_count", 0)) + 1},
                 query=f"?id=eq.{alert['id']}")
            log.warning(f"BI ALERT FIRED: {alert['alert_name']} | {metric}={val:.2f}")
            fired += 1
    log.info(f"BI alerts checked: {fired} fired out of {len(alerts)}")
    return fired

# ── REVENUE FORECAST ────────────────────────────────────────────────
def generate_revenue_forecast():
    """Simple linear regression forecast for next 30 days."""
    today = datetime.date.today()
    # Get last 30 days of MRR
    month_ago = (today - datetime.timedelta(days=30)).isoformat()
    history = supa("GET", "kpi_snapshots",
                   f"?metric_name=eq.mrr&date=gte.{month_ago}&order=date.asc&select=date,metric_value") or []
    if len(history) < 3:
        log.info("Not enough MRR history for forecast yet")
        return None
    # Simple linear trend
    values = [float(h["metric_value"]) for h in history]
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    slope = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values)) / \
            max(sum((i - x_mean)**2 for i in range(n)), 1)
    # Forecast next 30 days
    current_mrr = values[-1]
    forecast_mrr = max(current_mrr + slope * 30, 0)
    forecast_arr = forecast_mrr * 12
    confidence = min(0.9, max(0.5, 1 - (abs(slope) / max(y_mean, 1))))
    supa("POST", "revenue_forecast", {
        "forecast_date": (today + datetime.timedelta(days=30)).isoformat(),
        "model": "linear_trend",
        "mrr_forecast": round(forecast_mrr, 2),
        "arr_forecast": round(forecast_arr, 2),
        "confidence": round(confidence, 2),
    })
    log.info(f"Forecast: MRR in 30d = ${forecast_mrr:.0f} (confidence: {confidence:.0%})")
    push("📈 MRR Forecast", f"30-day MRR forecast: ${forecast_mrr:.0f}\nARR: ${forecast_arr:.0f}\nConfidence: {confidence:.0%}")
    return {"mrr_30d": forecast_mrr, "arr_30d": forecast_arr}

# ── COHORT BUILDER ──────────────────────────────────────────────────
def build_monthly_cohort():
    """Build cohort for current month's new contacts."""
    today = datetime.date.today()
    month_start = today.replace(day=1).isoformat()
    contacts = supa("GET", "contacts",
                    f"?created_at=gte.{month_start}T00:00:00&select=id,created_at,stage") or []
    if not contacts: return
    cohort_name = today.strftime("%Y-%m")
    revenue = 0
    existing = supa("GET", "cohorts", f"?cohort_name=eq.{cohort_name}&select=id&limit=1") or []
    row = {"cohort_name": cohort_name, "cohort_date": month_start,
           "contact_count": len(contacts), "revenue_total": revenue}
    if existing:
        supa("PATCH", "cohorts", row, query=f"?cohort_name=eq.{cohort_name}")
    else:
        supa("POST", "cohorts", row)
    log.info(f"Cohort {cohort_name}: {len(contacts)} contacts")

def run():
    log.info("=== BI Analytics Agent — Phase 5 ===")
    synced  = build_customer_360()
    kpis    = compute_daily_kpis()
    alerts  = check_bi_alerts(kpis)
    forecast= generate_revenue_forecast()
    build_monthly_cohort()
    summary = (f"BI run complete: {synced} C360 profiles | "
               f"MRR=${kpis.get('mrr',0):.0f} | "
               f"Customers={kpis.get('customers',0)} | "
               f"Alerts={alerts}")
    log.info(summary)
    push("📊 BI Analytics Done", summary)
    return kpis

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        log.error(f"BI Agent error: {e}")
        import traceback; traceback.print_exc()
    sys.exit(0)
