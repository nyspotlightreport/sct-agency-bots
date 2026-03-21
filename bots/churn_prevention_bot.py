#!/usr/bin/env python3
"""Churn Prevention Bot — Detects churn signals and auto-intervenes.
Health scoring, risk segmentation, personalized save campaigns."""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

CHURN_SIGNALS = {
    "no_login_7d":       {"weight":25, "severity":"HIGH",   "action":"immediate_outreach"},
    "support_ticket":    {"weight":15, "severity":"MEDIUM", "action":"proactive_call"},
    "missed_payment":    {"weight":40, "severity":"CRITICAL","action":"immediate_save"},
    "downgrade_attempt": {"weight":35, "severity":"HIGH",   "action":"retention_offer"},
    "cancellation_visit":{"weight":50, "severity":"CRITICAL","action":"immediate_intervention"},
    "low_usage_30d":     {"weight":20, "severity":"MEDIUM", "action":"success_coaching"},
    "complaint_email":   {"weight":20, "severity":"HIGH",   "action":"executive_outreach"},
    "competitor_mention":{"weight":15, "severity":"MEDIUM", "action":"battle_card"},
}

RETENTION_OFFERS = {
    "CRITICAL": ["2 months free", "1 month credit", "free upgrade for 60 days", "DFY setup included"],
    "HIGH":     ["1 month credit", "free strategy call", "feature unlock", "priority support"],
    "MEDIUM":   ["success coaching session", "feature tutorial", "check-in call"],
}

def calculate_health_score(customer: dict) -> dict:
    score  = 100
    signals = []
    last_login = customer.get("last_login_days", 0)
    usage_score = customer.get("usage_score", 100)
    payment_ok  = customer.get("payment_current", True)
    support_open = customer.get("open_tickets", 0)
    months_active = customer.get("months_active", 1)

    if last_login > 7:
        score -= CHURN_SIGNALS["no_login_7d"]["weight"]
        signals.append("no_login_7d")
    if not payment_ok:
        score -= CHURN_SIGNALS["missed_payment"]["weight"]
        signals.append("missed_payment")
    if usage_score < 30:
        score -= CHURN_SIGNALS["low_usage_30d"]["weight"]
        signals.append("low_usage_30d")
    if support_open > 0:
        score -= CHURN_SIGNALS["support_ticket"]["weight"] * min(support_open,3)
        signals.append("support_ticket")

    score = max(0, score)
    risk  = "CRITICAL" if score < 30 else "HIGH" if score < 55 else "MEDIUM" if score < 75 else "HEALTHY"

    return {
        "health_score": score,
        "risk_level": risk,
        "churn_signals": signals,
        "recommended_action": CHURN_SIGNALS.get(signals[0],{}).get("action","check_in") if signals else "maintain",
        "retention_offers": RETENTION_OFFERS.get(risk, []),
    }

def generate_save_campaign(customer: dict, health: dict) -> dict:
    name    = (customer.get("name","") or "").split()[0] or "there"
    company = customer.get("company","your company")
    risk    = health.get("risk_level","MEDIUM")
    offer   = health.get("retention_offers",[""])[0] if health.get("retention_offers") else "free strategy session"

    subject = {
        "CRITICAL": f"Is everything okay with your NYSR account, {name}?",
        "HIGH":     f"Quick check-in — {company}",
        "MEDIUM":   f"Getting the most from NYSR — {name}",
    }.get(risk, f"Checking in — {company}")

    body = claude(
        f"Write a {'urgent' if risk == 'CRITICAL' else 'warm'} customer success email. Focus on their success. Offer: {offer}. Under 100 words.",
        f"Customer {name} at {company} is at {risk} churn risk. Signals: {health.get('churn_signals',[])}",
        max_tokens=180
    ) or f"Hi {name},

Wanted to reach out personally and make sure {company} is getting full value from the platform.

I'd love to offer you a {offer} — no strings attached.

Can we schedule 20 minutes this week?

S.C. Thomas"

    return {"subject": subject, "body": body, "risk": risk, "offer": offer}

def run():
    customers = [
        {"name":"Mike Ross","company":"ShopFast","last_login_days":12,"usage_score":25,"payment_current":True,"open_tickets":1},
        {"name":"Lisa Park","company":"MediaCo","last_login_days":2,"usage_score":85,"payment_current":True,"open_tickets":0},
        {"name":"Tom Brown","company":"StartupX","last_login_days":0,"usage_score":60,"payment_current":False,"open_tickets":0},
    ]
    for c in customers:
        health = calculate_health_score(c)
        log.info(f"{c['name']} @ {c['company']}: {health['risk_level']} ({health['health_score']}/100) — {health['recommended_action']}")
        if health["risk_level"] in ["HIGH","CRITICAL"]:
            campaign = generate_save_campaign(c, health)
            log.info(f"  Save campaign: {campaign['subject']}")
    return [calculate_health_score(c) for c in customers]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()


import os as _os, json as _json, urllib.request as _ureq

def _supa(method, table, data=None, query=""):
    """Standalone Supabase helper - no import dependency."""
    url  = _os.environ.get("SUPABASE_URL","")
    key  = _os.environ.get("SUPABASE_KEY") or _os.environ.get("SUPABASE_ANON_KEY","")
    if not url or not key: return None
    req  = _ureq.Request(f"{url}/rest/v1/{table}{query}",
        data=_json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":key,"Authorization":f"Bearer {key}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with _ureq.urlopen(req, timeout=15) as r:
            body=r.read(); return _json.loads(body) if body else {}
    except Exception as e:
        import logging; logging.getLogger(__name__).warning(f"Supa {method} {table}: {e}")
        return None

def supabase_request(method, table, data=None, query="", **kwargs):
    return _supa(method, table, data, query)
