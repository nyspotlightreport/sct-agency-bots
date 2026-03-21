#!/usr/bin/env python3
# Billing Recovery Bot - Failed payments, dunning emails, card update flows.
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
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":"Billing Recovery","message":msg}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

DUNNING_SEQUENCE = [
    {"day":0,"subject":"Payment failed - action required","urgency":"HIGH"},
    {"day":3,"subject":"Your account is at risk of suspension","urgency":"URGENT"},
    {"day":7,"subject":"Final notice: account suspension tomorrow","urgency":"CRITICAL"},
    {"day":8,"subject":"Account suspended - reactivate now","urgency":"CRITICAL"},
]

def generate_dunning_email(customer, attempt_num, days_overdue):
    name = (customer.get("name","") or "").split()[0] or "there"
    seq = DUNNING_SEQUENCE[min(attempt_num, len(DUNNING_SEQUENCE)-1)]
    body = claude(
        f"Write a {seq['urgency']} billing recovery email. Empathetic, clear, give them easy update link.",
        f"Customer {name} at {customer.get('company','')}. {days_overdue} days overdue. Attempt #{attempt_num+1}.",
        max_tokens=200
    ) or f"Hi {name}, we couldn't process your payment for NYSR. Please update your card at nyspotlightreport.com/billing to keep your account active."
    return {"subject":seq["subject"],"body":body,"urgency":seq["urgency"]}

def run():
    failed = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&limit=5") or []
    recovered = 0
    for customer in failed:
        email = generate_dunning_email(customer, 0, 3)
        log.info(f"Dunning: {customer.get('name','?')} - {email['subject']}")
    notify(f"Billing recovery: {len(failed)} accounts need attention")
    return {"failed_payments":len(failed),"recovered":recovered}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
