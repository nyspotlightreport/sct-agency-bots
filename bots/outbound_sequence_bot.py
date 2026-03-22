#!/usr/bin/env python3
# Outbound Sequence Bot - Manages multi-touch outbound sequences across email+LinkedIn+phone.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

SEQUENCE_TEMPLATES = {
    "dfy_outbound": [
        {"day":0,"channel":"email","template":"cold_intro"},
        {"day":3,"channel":"linkedin","template":"connect_request"},
        {"day":5,"channel":"email","template":"value_add"},
        {"day":8,"channel":"linkedin","template":"dm_followup"},
        {"day":12,"channel":"email","template":"case_study"},
        {"day":15,"channel":"phone","template":"cold_call"},
        {"day":20,"channel":"email","template":"breakup"},
    ],
    "proflow_nurture": [
        {"day":0,"channel":"email","template":"welcome_content"},
        {"day":7,"channel":"email","template":"how_to_guide"},
        {"day":14,"channel":"email","template":"case_study"},
        {"day":21,"channel":"email","template":"soft_offer"},
        {"day":30,"channel":"email","template":"hard_offer"},
    ],
}

def enroll_in_sequence(contact, sequence_name="dfy_outbound"):
    seq = SEQUENCE_TEMPLATES.get(sequence_name,[])
    tasks = []
    for step in seq:
        due_date = (datetime.utcnow() + timedelta(days=step["day"])).date().isoformat()
        tasks.append({"contact_id":contact.get("id"),"channel":step["channel"],"template":step["template"],"due_date":due_date,"status":"pending"})
    supabase_request("POST","activities",data={"contact_id":contact.get("id"),"type":"email_sent","subject":f"Enrolled in {sequence_name}"})
    log.info(f"Enrolled {contact.get('name','?')} in {sequence_name}: {len(tasks)} touchpoints")
    return tasks

def run():
    leads = supabase_request("GET","contacts",query="?stage=eq.LEAD&score=gte.60&limit=10") or []
    for lead in leads:
        enroll_in_sequence(lead, "dfy_outbound")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
