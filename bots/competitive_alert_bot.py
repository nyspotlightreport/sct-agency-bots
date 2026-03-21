#!/usr/bin/env python3
# Competitive Alert Bot - Monitors competitor pricing, features, and PR for battle card updates.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.competitor_intelligence_agent import COMPETITORS
except:
    def claude(s,u,**k): return ""
    COMPETITORS = {}
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg,title="Competitive Intel"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def monitor_competitor_pricing(competitor):
    # In production: scrape pricing pages
    return {"competitor":competitor,"price_changed":False,"last_checked":__import__("datetime").datetime.utcnow().isoformat()}

def generate_competitive_alert(competitor, change_type, details):
    return claude(
        "Write a 2-sentence internal sales alert about a competitive change. What it means for us.",
        f"Competitor: {competitor}. Change: {change_type}. Details: {details}",
        max_tokens=100
    ) or f"Alert: {competitor} {change_type}. Review battle card and update talking points."

def run():
    alerts = []
    for comp_key, comp in COMPETITORS.items():
        status = monitor_competitor_pricing(comp["name"])
        if status.get("price_changed"):
            alert = generate_competitive_alert(comp["name"],"pricing change",status)
            alerts.append(alert)
            notify(alert,"Competitive Alert")
    log.info(f"Competitive monitoring: {len(COMPETITORS)} competitors watched | {len(alerts)} alerts")
    return alerts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
