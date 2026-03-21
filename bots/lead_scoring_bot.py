#!/usr/bin/env python3
# Lead Scoring Bot - Real-time lead scoring from multiple signals.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import score_contact, supabase_request, ICPS
except:
    def score_contact(c,i): return {"total":50,"grade":"B","priority":"MEDIUM"}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

SIGNAL_WEIGHTS = {
    "opened_email": 5, "clicked_link": 10, "visited_pricing": 20,
    "started_trial": 30, "demo_requested": 25, "referral": 20,
    "viewed_case_study": 8, "linkedin_engaged": 5, "replied_email": 15,
}

def apply_behavioral_signals(base_score, signals):
    bonus = sum(SIGNAL_WEIGHTS.get(s,0) for s in signals)
    return min(100, base_score + bonus)

def score_and_route(contact, signals=None):
    base = score_contact(contact, "dfy_agency")
    total = apply_behavioral_signals(base["total"], signals or [])
    route = "AE" if total >= 70 else "SDR" if total >= 45 else "NURTURE"
    supabase_request("PATCH","contacts",data={"score":total},query=f"?email=eq.{contact.get('email','')}")
    return {"score":total,"route":route,"grade":base["grade"]}

def run():
    contacts = supabase_request("GET","contacts",query="?stage=eq.LEAD&limit=50") or []
    for c in contacts:
        result = score_and_route(c)
        if result["route"] == "AE":
            log.info(f"Hot lead: {c.get('name','?')} - Score {result['score']} -> {result['route']}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
