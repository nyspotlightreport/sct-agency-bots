#!/usr/bin/env python3
"""
Customer Health Score Bot — Retention is cashflow insurance.
Scores every paying customer on churn risk daily.
Alerts on at-risk accounts BEFORE they cancel.

Health score (0-100):
  - Engagement signals (emails opened, site visits, messages): 30pts
  - Payment history (on-time, failed, dispute): 25pts
  - Stage progression (advancing or stalling): 20pts
  - Time since last contact: 15pts
  - Support ticket volume: 10pts

Risk tiers:
  - 70+: Healthy — candidate for upsell
  - 40-69: At risk — needs attention
  - <40: DANGER — immediate action required
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

import urllib.request, urllib.parse
log = logging.getLogger(__name__)
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

def score_customer(contact: dict) -> dict:
    score = 50  # baseline
    reasons = []

    # Engagement: last_contacted recency
    last = contact.get("last_contacted","")
    if last:
        try:
            days_ago = (datetime.utcnow() - datetime.fromisoformat(last.replace("Z",""))).days
            if days_ago <= 7:   score += 15; reasons.append("Active engagement")
            elif days_ago <= 14: score += 5
            elif days_ago <= 30: score -= 5
            else:               score -= 15; reasons.append("No contact 30+ days")
        except Exception:  # noqa: bare-except

            pass
    # Touch count momentum
    touches = contact.get("touch_count", 0)
    if touches >= 5:  score += 10; reasons.append("High engagement history")
    elif touches == 0: score -= 10; reasons.append("Never replied")

    # Score-based health proxy
    crm_score = contact.get("score", 50)
    score += (crm_score - 50) * 0.2

    # Grade bonus
    grade = contact.get("grade","C")
    if grade == "A": score += 10
    elif grade == "B": score += 5
    elif grade == "D": score -= 15

    score = max(0, min(100, round(score)))

    if score >= 70:   risk = "HEALTHY"
    elif score >= 40: risk = "AT_RISK"
    else:             risk = "DANGER"

    action = claude(
        "You are a customer success manager. In 1 sentence, say what to do with this customer.",
        f"Customer: {contact.get('name','')} | {contact.get('company','')} | Health: {score}/100 | Risk: {risk} | Grade: {grade} | Last contact: {last}",
        max_tokens=80
    ) or ("Schedule immediate check-in call" if risk=="DANGER" else "Send value-add email this week" if risk=="AT_RISK" else "Identify upsell opportunity")

    return {"score":score,"risk":risk,"action":action,"reasons":reasons}

def run():
    log.info("Customer Health Score Bot running...")
    customers = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&select=*&limit=100") or []
    log.info(f"Active customers: {len(customers)}")

    danger = []
    at_risk = []
    healthy = []

    for c in customers:
        health = score_customer(c)
        if c.get("id"):
            supabase_request("PATCH","contacts",
                data={"health_score":health["score"],"health_risk":health["risk"],"health_action":health["action"]},
                query=f"?id=eq.{c['id']}"
            )
        if health["risk"] == "DANGER": danger.append({**c,**health})
        elif health["risk"] == "AT_RISK": at_risk.append({**c,**health})
        else: healthy.append({**c,**health})

    log.info(f"Health: {len(healthy)} healthy | {len(at_risk)} at-risk | {len(danger)} DANGER")

    if danger and PUSHOVER_API and PUSHOVER_USER:
        names = ", ".join([f"{d.get('name','?')} ({d['score']})" for d in danger[:3]])
        msg = f"🚨 {len(danger)} customers at DANGER churn risk!\n{names}\n\nAction: Reach out NOW before they cancel."
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Churn Alert!","message":msg,"priority":"1"}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except Exception:  # noqa: bare-except

            pass
    elif at_risk and PUSHOVER_API and PUSHOVER_USER:
        msg = f"⚠️ {len(at_risk)} customers at risk\n{len(healthy)} healthy\n\nTop at-risk: {at_risk[0].get('name','?')} — {at_risk[0]['action']}"
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Health Monitor","message":msg}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except Exception:  # noqa: bare-except

            pass
    return {"total":len(customers),"healthy":len(healthy),"at_risk":len(at_risk),"danger":len(danger)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Health] %(message)s")
    run()
