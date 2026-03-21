#!/usr/bin/env python3
# Inbound Router Bot - Routes inbound leads to right rep/sequence based on source+score.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import score_contact, supabase_request
except:
    def score_contact(c,i): return {"total":50,"grade":"B","priority":"MEDIUM"}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

ROUTING_RULES = [
    {"condition":lambda c:c.get("source")=="referral","route":"AE","sequence":"high_touch","priority":"HIGH"},
    {"condition":lambda c:score_contact(c,"dfy_agency").get("total",0)>=75,"route":"AE","sequence":"hot_inbound","priority":"HIGH"},
    {"condition":lambda c:c.get("source")=="organic","route":"SDR","sequence":"proflow_nurture","priority":"MEDIUM"},
    {"condition":lambda c:True,"route":"NURTURE","sequence":"proflow_nurture","priority":"LOW"},
]

def route_lead(contact):
    for rule in ROUTING_RULES:
        try:
            if rule["condition"](contact):
                return {"route":rule["route"],"sequence":rule["sequence"],"priority":rule["priority"]}
        except: pass
    return {"route":"NURTURE","sequence":"proflow_nurture","priority":"LOW"}

def process_inbound(contact):
    routing = route_lead(contact)
    supabase_request("PATCH","contacts",
        data={"stage":"PROSPECT","priority":routing["priority"]},
        query=f"?id=eq.{contact.get('id','')}")
    log.info(f"Routed {contact.get('name','?')} -> {routing['route']} ({routing['sequence']})")
    return routing

def run():
    new_leads = supabase_request("GET","contacts",query="?stage=eq.LEAD&created_at=gte.2026-03-01&limit=20") or []
    for l in new_leads:
        process_inbound(l)
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
