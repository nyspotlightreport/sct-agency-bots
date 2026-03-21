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
