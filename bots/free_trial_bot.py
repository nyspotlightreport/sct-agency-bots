#!/usr/bin/env python3
# Free Trial Bot - Trial activation, usage monitoring, conversion optimization.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

TRIAL_DAYS = 14
TRIAL_CHECKPOINTS = {
    1:  "activation",
    3:  "first_value",
    7:  "habit",
    11: "pre_expiry_nudge",
    13: "final_push",
    14: "convert_or_lose",
}

def generate_trial_email(trial_day, customer, usage=None):
    name = (customer.get("name","") or "").split()[0] or "there"
    checkpoint = TRIAL_CHECKPOINTS.get(trial_day,"follow_up")
    return {
        "subject": {
            1:  f"Your NYSR trial is live - first step, {name}",
            3:  f"Have you published your first article yet?",
            7:  f"Week 1 down - here's what's working",
            11: f"3 days left on your trial",
            13: f"Tomorrow is your last day",
            14: f"Your trial ends today - lock in your spot",
        }.get(trial_day, f"Day {trial_day} check-in"),
        "checkpoint": checkpoint,
        "trial_day": trial_day,
    }

def monitor_trial_health(customer):
    usage = customer.get("usage_pct", 0)
    days_in = customer.get("days_in_trial", 0)
    if usage < 20 and days_in > 3:
        return {"status":"AT_RISK","action":"intervention","urgency":"HIGH"}
    elif usage > 60:
        return {"status":"HEALTHY","action":"upsell_nudge","urgency":"LOW"}
    return {"status":"NORMAL","action":"standard_sequence","urgency":"MEDIUM"}

def run():
    trials = supabase_request("GET","contacts",query="?stage=eq.PROSPECT&icp=eq.proflow_ai&limit=20") or []
    log.info(f"Active trials: {len(trials)}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
