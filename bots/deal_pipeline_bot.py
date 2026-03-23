#!/usr/bin/env python3
"""
Deal Pipeline Bot — Daily revenue intelligence
Runs daily. Analyzes the pipeline, identifies stuck deals,
sends action alerts, forecasts MRR, and moves contacts automatically.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import (
        get_pipeline_stats, get_high_priority_contacts,
        analyze_deal, supabase_request, STAGES
    )
except Exception as e:
    print(f"Import warning: {e}")
    def claude(s,u,**k): return ""
    def get_pipeline_stats(): return {}
    def get_high_priority_contacts(n): return []
    def analyze_deal(c,s): return {}
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.parse

def notify(msg, title="Pipeline Alert"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except Exception:  # noqa: bare-except

        pass
def find_stuck_deals() -> list:
    """Find deals that haven't moved in 7+ days."""
    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
    result = supabase_request("GET", "contacts",
        query=f"?stage=not.in.(CLOSED_WON,CLOSED_LOST,LEAD)&stage_changed_at=lt.{cutoff}&order=score.desc&limit=10"
    )
    return result or []

def forecast_mrr() -> dict:
    """Forecast MRR based on pipeline."""
    stats = get_pipeline_stats()
    
    # Probability by stage
    probs = {
        "LEAD": 0.05, "PROSPECT": 0.15, "QUALIFIED": 0.35,
        "PROPOSAL": 0.60, "NEGOTIATION": 0.85
    }
    
    # Average deal values
    deal_values = {
        "proflow_ai":        150,   # avg of $97-497
        "dfy_agency":        5000,  # avg DFY setup
        "enterprise_agency": 1200,  # avg $997-1997 MRR
    }
    avg_deal = sum(deal_values.values()) / len(deal_values)
    
    weighted_pipeline = 0
    for stage, data in stats.items():
        prob = probs.get(stage, 0)
        count = data.get("count", 0)
        weighted_pipeline += count * prob * avg_deal
    
    won_result = supabase_request("GET", "contacts",
        query="?stage=eq.CLOSED_WON&select=id"
    )
    
    return {
        "weighted_pipeline_value": round(weighted_pipeline),
        "expected_30d_revenue":    round(weighted_pipeline * 0.3),
        "total_pipeline_contacts": sum(d.get("count",0) for d in stats.values()),
        "closed_won_count":        len(won_result or []),
    }

def run():
    log.info("Deal Pipeline Bot running...")
    
    # 1. Get pipeline overview
    stats    = get_pipeline_stats()
    forecast = forecast_mrr()
    
    # 2. Find stuck deals
    stuck = find_stuck_deals()
    
    # 3. Get priority contacts needing action
    priority = get_high_priority_contacts(5)
    
    # 4. Build summary
    total = sum(s.get("count",0) for s in stats.values())
    log.info(f"Pipeline: {total} contacts | ${forecast['weighted_pipeline_value']:,} weighted | ${forecast['expected_30d_revenue']:,} expected 30d")
    log.info(f"Stuck deals: {len(stuck)} | Priority actions: {len(priority)}")
    
    # 5. Alert on stuck deals
    if stuck:
        stuck_names = ", ".join([f"{c.get('name','?')} ({c.get('stage','?')})" for c in stuck[:3]])
        notify(f"⚠️ {len(stuck)} stuck deals (7d+):\n{stuck_names}\n\nPipeline: {total} contacts | ${forecast['weighted_pipeline_value']:,} weighted value", "Pipeline: Stuck Deals")
    
    # 6. Daily pipeline summary to Chairman
    stage_summary = " | ".join([f"{k}: {v.get('count',0)}" for k,v in stats.items() if v.get('count',0) > 0])
    notify(
        f"📊 Daily Pipeline\n{stage_summary}\n\n💰 30d forecast: ${forecast['expected_30d_revenue']:,}\n🏆 Won: {forecast['closed_won_count']}",
        "Pipeline Daily"
    )
    
    return {
        "stats": stats,
        "forecast": forecast,
        "stuck_deals": len(stuck),
        "priority_actions": len(priority),
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Pipeline] %(message)s")
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
