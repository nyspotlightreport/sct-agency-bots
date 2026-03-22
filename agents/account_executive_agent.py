#!/usr/bin/env python3
# Account Executive Agent - Mid/bottom funnel: demos, proposals, closing.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, advance_stage
    from agents.proposal_generator_agent import generate_proposal, generate_quick_proposal
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
    def advance_stage(cid,s,r=""): return True
    def generate_proposal(c,p,n=""): return "Proposal"
    def generate_quick_proposal(c): return "Quick pitch"
log = logging.getLogger(__name__)

PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse
def notify(msg,title="AE Alert"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def run_demo(contact):
    name = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","")
    brief = claude(
        "Write a 5-point demo script outline. Each point is one sentence. Focus on their pain.",
        f"Demo for {name} at {company}. ICP: {contact.get('icp','dfy_agency')}",
        max_tokens=200
    ) or "1. Recap pain\n2. Show quick win\n3. Live demo\n4. ROI calc\n5. Next steps"
    return {"contact":contact,"brief":brief,"demo_date":datetime.utcnow().isoformat()}

def send_proposal(contact, product_key="dfy_growth"):
    proposal = generate_proposal(contact, product_key)
    advance_stage(contact.get("id",""), "PROPOSAL", "Proposal sent by AE")
    notify(f"Proposal sent: {contact.get('name','?')} @ {contact.get('company','?')} - {product_key}", "AE: Proposal")
    return proposal

def close_deal(contact, deal_value, product):
    advance_stage(contact.get("id",""), "CLOSED_WON", f"Closed by AE - {product} at ${deal_value}")
    notify(f"DEAL CLOSED: {contact.get('company','?')} - ${deal_value:,} - {product}", "DEAL CLOSED")
    supabase_request("POST","deals",data={
        "contact_id": contact.get("id"),
        "title": f"{product} - {contact.get('company','')}",
        "product": product,
        "value": deal_value,
        "stage": "CLOSED_WON",
        "actual_close": datetime.utcnow().date().isoformat(),
    })
    return True

def get_active_deals():
    return supabase_request("GET","contacts",
        query="?stage=in.(QUALIFIED,PROPOSAL,NEGOTIATION)&order=score.desc&limit=20") or []

def run():
    deals = get_active_deals()
    log.info(f"AE: {len(deals)} active deals to work")
    return deals

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()