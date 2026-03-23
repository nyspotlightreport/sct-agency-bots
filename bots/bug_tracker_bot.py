#!/usr/bin/env python3
# Bug Tracker Bot - Classifies, triages, and tracks bugs from multiple sources.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude_json
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

SEVERITY_MAP = {
    "data_loss":       {"severity":"P0","response":"1 hour","escalate":True},
    "security":        {"severity":"P0","response":"2 hours","escalate":True},
    "payment_broken":  {"severity":"P1","response":"4 hours","escalate":True},
    "feature_broken":  {"severity":"P2","response":"24 hours","escalate":False},
    "ui_glitch":       {"severity":"P3","response":"1 week","escalate":False},
    "enhancement":     {"severity":"P4","response":"backlog","escalate":False},
}

def classify_bug(description):
    result = claude_json(
        "Classify this bug. Return JSON: {category, severity, component, reproducible, suggested_fix}",
        f"Bug: {description}",
        max_tokens=200
    ) or {"category":"feature_broken","severity":"P2","component":"unknown","reproducible":True}
    severity_info = SEVERITY_MAP.get(result.get("category","feature_broken"), SEVERITY_MAP["feature_broken"])
    return {**result,**severity_info,"id":f"BUG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}","created_at":datetime.utcnow().isoformat()}

def log_bug(description, reporter="system"):
    bug = classify_bug(description)
    supabase_request("POST","bugs",data={"id":bug["id"],"description":description,"severity":bug["severity"],"category":bug.get("category",""),"reporter":reporter,"status":"open","created_at":bug["created_at"]})
    log.info(f"Bug {bug['id']}: {bug['severity']} - {bug.get('category','')} - respond by {bug.get('response','?')}")
    return bug

def run():
    bugs = ["Users can't login after password reset","Payment returns 500 for AMEX cards","Download button misaligned on mobile"]
    for desc in bugs:
        bug = log_bug(desc)
        log.info(f"  {bug['id']}: {bug['severity']} - {bug.get('response','?')}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
