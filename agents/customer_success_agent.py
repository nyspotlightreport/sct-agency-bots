#!/usr/bin/env python3
# Customer Success Agent - Onboarding, retention, expansion, NPS.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

ONBOARDING_MILESTONES = {
    "day_1":  ["Account created","First content generated","API keys configured"],
    "day_3":  ["First publish","Social integration connected","Weekly schedule set"],
    "day_7":  ["10 articles published","Analytics dashboard reviewed","Team invited"],
    "day_30": ["100 articles published","First SEO ranking","ROI calculated"],
}

def generate_onboarding_email(customer, day=1):
    name = (customer.get("name","") or "").split()[0] or "there"
    milestones = ONBOARDING_MILESTONES.get(f"day_{day}", [])
    return {
        "subject": f"Day {day}: Your NYSR setup checklist",
        "body": claude(
            "Write a warm onboarding email. Celebrate progress. Give 3 specific action items. Under 100 words.",
            f"Customer: {name}. Day {day} of onboarding. Milestones to hit: {milestones}",
            max_tokens=200
        ) or f"Hi {name}, welcome to day {day}! Here are your next steps: {chr(10).join(milestones)}"
    }

def calculate_health_score(customer):
    score = 100
    if customer.get("last_login_days",0) > 7: score -= 25
    if customer.get("usage_pct",100) < 30: score -= 20
    if not customer.get("payment_current",True): score -= 40
    if customer.get("open_tickets",0) > 0: score -= 15
    risk = "CRITICAL" if score < 30 else "HIGH" if score < 55 else "MEDIUM" if score < 75 else "HEALTHY"
    return {"score": max(0,score), "risk": risk}

def run_cs_daily():
    customers = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&limit=50") or []
    at_risk = []
    for c in customers:
        health = calculate_health_score(c)
        if health["risk"] in ["HIGH","CRITICAL"]:
            at_risk.append({**c,"health":health})
    log.info(f"CS: {len(customers)} active customers | {len(at_risk)} at risk")
    return {"total":len(customers),"at_risk":at_risk}

def run():
    return run_cs_daily()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()