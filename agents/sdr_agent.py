#!/usr/bin/env python3
# SDR Agent - Sales Development Rep. Top of funnel: prospecting, qualifying, booking.
import os, sys, json, logging
from datetime import datetime

# === MEMORY ENGINE (auto-wired) ===
import sys as _sys
_sys.path.insert(0, '/opt/nysr')
try:
    from agent_memory_engine import read_memory as _read_memory, write_memory as _write_memory
    _agent_name = __file__.split('/')[-1].replace('.py','')
    _prior_memory = _read_memory(_agent_name)
except:
    _read_memory = lambda x: {}
    _write_memory = lambda x, y: None
    _prior_memory = {}
# === END MEMORY ENGINE ===


sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import score_contact, ICPS, supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def score_contact(c,i): return {"total":50,"grade":"B","priority":"MEDIUM"}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

DAILY_TARGETS = {"outreach":20, "follow_ups":15, "meetings_booked":2, "demos_booked":1}

def qualify_lead(contact):
    score = score_contact(contact, "dfy_agency")
    bant = {
        "budget":    contact.get("employees",0) > 5,
        "authority": any(t in contact.get("title","").lower() for t in ["ceo","cto","founder","owner","vp","director"]),
        "need":      bool(contact.get("industry")),
        "timeline":  score["total"] > 60,
    }
    bant_score = sum(bant.values())
    return {"bant": bant, "bant_score": bant_score, "qualified": bant_score >= 3, "score": score}

def write_personalized_opener(contact):
    name = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","your company")
    title = contact.get("title","")
    return claude(
        "You are an SDR. Write a 2-sentence personalized cold email opener. First sentence about them. Second creates curiosity about AI automation. No selling.",
        f"Prospect: {name}, {title} at {company}. Industry: {contact.get('industry','')}",
        max_tokens=100
    ) or f"Saw {company} is growing fast - content and lead gen usually become bottlenecks around this stage. I have something specific that might help."

def book_meeting_email(contact):
    name = (contact.get("name","") or "").split()[0] or "there"
    return {
        "subject": f"15 min - {contact.get('company','')} x NYSR?",
        "body": f"Hi {name},\n\n{write_personalized_opener(contact)}\n\nWorth a 15-min call? Here: https://calendly.com/nyspotlightreport\n\nS.C. Thomas"
    }

def run_daily_sdr(leads):
    results = {"qualified":[],"disqualified":[],"meetings_booked":0}
    for lead in leads:
        qual = qualify_lead(lead)
        if qual["qualified"]:
            results["qualified"].append({**lead,"qualification":qual})
        else:
            results["disqualified"].append(lead)
    log.info(f"SDR daily: {len(results['qualified'])} qualified / {len(leads)} reviewed")
    return results

def run():
    test = [{"name":"Alex Chen","company":"ContentCo","title":"CEO","industry":"marketing","employees":15}]
    return run_daily_sdr(test)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()