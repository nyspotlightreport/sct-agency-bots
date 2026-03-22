#!/usr/bin/env python3
# Sales Leaderboard Bot - Gamifies sales with daily/weekly/monthly rankings.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import supabase_request, get_pipeline_stats
except:
    def supabase_request(m,t,**k): return None
    def get_pipeline_stats(): return {}
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg,title="Leaderboard"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def calculate_leaderboard():
    stats = get_pipeline_stats()
    won   = stats.get("CLOSED_WON",{}).get("count",0)
    total = sum(v.get("count",0) for v in stats.values())
    active= total - won - stats.get("CLOSED_LOST",{}).get("count",0)
    points = won * 100 + active * 5
    return {
        "chairman_sc_thomas": {
            "deals_won": won,
            "pipeline_active": active,
            "points": points,
            "rank": 1,
            "streak": "🔥" if won > 0 else "⬜",
        }
    }

def send_leaderboard():
    lb = calculate_leaderboard()
    entry = lb.get("chairman_sc_thomas",{})
    msg = f"LEADERBOARD - {datetime.utcnow().strftime('%b %d')}
1. S.C. Thomas {entry.get('streak','')}
   Won: {entry.get('deals_won',0)} | Active: {entry.get('pipeline_active',0)} | Pts: {entry.get('points',0)}"
    notify(msg,"Daily Leaderboard")
    log.info(msg)
    return lb

def run():
    return send_leaderboard()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
