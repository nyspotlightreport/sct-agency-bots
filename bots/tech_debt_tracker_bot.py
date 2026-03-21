#!/usr/bin/env python3
# Tech Debt Tracker Bot - Identifies, prioritizes, and tracks technical debt.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

DEBT_CATEGORIES = {
    "code":         {"description":"Poor code quality, complexity, duplication","priority_weight":2},
    "architecture": {"description":"Wrong patterns, tight coupling, scalability issues","priority_weight":3},
    "dependencies": {"description":"Outdated libraries, security vulnerabilities","priority_weight":3},
    "testing":      {"description":"Missing tests, flaky tests, low coverage","priority_weight":2},
    "documentation":{"description":"Missing docs, outdated comments","priority_weight":1},
    "performance":  {"description":"Slow queries, memory leaks, N+1 problems","priority_weight":2},
    "security":     {"description":"Auth issues, data exposure, injection risks","priority_weight":4},
}

def log_debt_item(title, category, description, effort_days=1, impact="MEDIUM"):
    item = {
        "title": title,
        "category": category,
        "description": description,
        "effort_days": effort_days,
        "impact": impact,
        "priority": DEBT_CATEGORIES.get(category,{}).get("priority_weight",1) * (3 if impact=="HIGH" else 2 if impact=="MEDIUM" else 1),
        "status": "open",
        "logged_at": datetime.utcnow().isoformat(),
    }
    supabase_request("POST","tech_debt",data=item)
    return item

def prioritize_debt():
    items = supabase_request("GET","tech_debt",query="?status=eq.open&order=priority.desc&limit=10") or []
    return items

def estimate_debt_cost(items):
    total_days = sum(i.get("effort_days",1) for i in items)
    hourly_rate = 150
    return {"total_items":len(items),"total_days":total_days,"estimated_cost":total_days*8*hourly_rate,"recommendation":f"Address top {min(3,len(items))} items this sprint"}

def run():
    items = prioritize_debt()
    if items:
        cost = estimate_debt_cost(items)
        log.info(f"Tech debt: {cost['total_items']} items | {cost['total_days']} days | ${cost['estimated_cost']:,}")
    else:
        log.info("Tech debt tracker: no items in database yet")
    return items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
