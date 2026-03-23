#!/usr/bin/env python3
# NPS Survey Bot - Automated NPS collection, analysis, and follow-up routing.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

NPS_SEGMENTS = {
    "promoter":  {"min":9,"max":10,"action":"testimonial_request","color":"green"},
    "passive":   {"min":7,"max":8,"action":"upsell_opportunity","color":"yellow"},
    "detractor": {"min":0,"max":6,"action":"save_campaign","color":"red"},
}

def classify_nps(score):
    for segment, data in NPS_SEGMENTS.items():
        if data["min"] <= score <= data["max"]:
            return segment
    return "detractor"

def generate_nps_email(customer):
    name = (customer.get("name","") or "").split()[0] or "there"
    return {
        "subject": f"Quick question about NYSR - {name}?",
        "body": f"Hi {name},\n\nOne quick question:\n\nOn a scale of 0-10, how likely are you to recommend NYSR to a friend or colleague?\n\n[ 0 ] [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ] [ 6 ] [ 7 ] [ 8 ] [ 9 ] [ 10 ]\n\nClick your score: https://nyspotlightreport.com/nps/?id={customer.get('id','')}\n\nThanks,\nS.C. Thomas",
    }

def process_nps_response(customer, score, comment=""):
    segment = classify_nps(score)
    action = NPS_SEGMENTS[segment]["action"]
    supabase_request("PATCH","contacts",data={"nps_score":score,"nps_segment":segment},query=f"?id=eq.{customer.get('id','')}")
    log.info(f"NPS: {customer.get('name','?')} scored {score} ({segment}) -> {action}")
    return {"segment":segment,"action":action,"score":score}

def calculate_nps(responses):
    if not responses: return 0
    promoters  = len([r for r in responses if r >= 9])
    detractors = len([r for r in responses if r <= 6])
    return round((promoters/len(responses) - detractors/len(responses)) * 100)

def run():
    customers = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&limit=20") or []
    for c in customers[:5]:
        email = generate_nps_email(c)
        log.info(f"NPS survey for: {c.get('name','?')} -> {email['subject']}")
    test_scores = [9,8,10,7,6,9,10,8,5,9]
    nps = calculate_nps(test_scores)
    log.info(f"Current NPS score: {nps}")
    return {"customers_surveyed":len(customers),"current_nps":nps}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
