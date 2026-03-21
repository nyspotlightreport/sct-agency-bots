#!/usr/bin/env python3
# Intent Signal Bot - Detects buying signals: job posts, funding, tech stack changes.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude_json
    from agents.crm_core_agent import supabase_request
except:
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

INTENT_SIGNALS = {
    "hiring_marketing":   {"score_boost":15,"message":"They're scaling marketing - need content automation"},
    "series_a_funding":   {"score_boost":20,"message":"Fresh capital = budget for tools"},
    "hiring_content":     {"score_boost":25,"message":"Content team growing - perfect timing"},
    "new_website":        {"score_boost":10,"message":"Website refresh = content priority"},
    "competitor_leaving": {"score_boost":30,"message":"Direct competitor just churned from rival"},
    "job_change":         {"score_boost":20,"message":"New decision maker - fresh start"},
    "social_engagement":  {"score_boost":5,"message":"Engaging with our content"},
}

def detect_signals_from_apollo(contact):
    signals = []
    title_lower = contact.get("title","").lower()
    company_growth = contact.get("employees",0) or 0
    if any(k in title_lower for k in ["chief","vp","director"]) and company_growth > 50:
        signals.append("hiring_marketing")
    if contact.get("source") == "linkedin_engaged":
        signals.append("social_engagement")
    return signals

def process_signals(contact):
    signals = detect_signals_from_apollo(contact)
    total_boost = sum(INTENT_SIGNALS.get(s,{}).get("score_boost",0) for s in signals)
    if total_boost > 0:
        current_score = contact.get("score",50)
        new_score = min(100, current_score + total_boost)
        supabase_request("PATCH","contacts",data={"score":new_score},query=f"?id=eq.{contact.get('id','')}")
        log.info(f"Intent signals for {contact.get('name','?')} @ {contact.get('company','?')} +{total_boost} pts")
    return signals

def run():
    contacts = supabase_request("GET","contacts",query="?stage=in.(LEAD,PROSPECT)&limit=50") or []
    total_signals = 0
    for c in contacts:
        sigs = process_signals(c)
        total_signals += len(sigs)
    log.info(f"Intent signals processed: {total_signals} signals across {len(contacts)} contacts")
    return total_signals

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()


import os as _os, json as _json, urllib.request as _ureq

def _supa(method, table, data=None, query=""):
    """Standalone Supabase helper - no import dependency."""
    url  = _os.environ.get("SUPABASE_URL","")
    key  = _os.environ.get("SUPABASE_KEY") or _os.environ.get("SUPABASE_ANON_KEY","")
    if not url or not key: return None
    req  = _ureq.Request(f"{url}/rest/v1/{table}{query}",
        data=_json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":key,"Authorization":f"Bearer {key}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with _ureq.urlopen(req, timeout=15) as r:
            body=r.read(); return _json.loads(body) if body else {}
    except Exception as e:
        import logging; logging.getLogger(__name__).warning(f"Supa {method} {table}: {e}")
        return None

def supabase_request(method, table, data=None, query="", **kwargs):
    return _supa(method, table, data, query)
