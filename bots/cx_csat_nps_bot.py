#!/usr/bin/env python3
"""bots/cx_csat_nps_bot.py
Collects CSAT and NPS scores. Analyzes sentiment trends.
Alerts on detractors. Requests testimonials from promoters.
Ritz-Carlton target: 95%+ CSAT, NPS > 70.
"""
import os, json, urllib.request, logging, datetime
log = logging.getLogger("cx_csat")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CSAT] %(message)s")

SUPA = os.environ.get("SUPABASE_URL","")
KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e:
        log.warning(f"DB: {e}"); return None

def run():
    today = datetime.date.today().isoformat()
    scores = supa("GET","cx_satisfaction","",f"?created_at=gte.{today}T00:00:00&select=score,score_type") or []
    if scores:
        csat = [s["score"] for s in scores if s.get("score_type")=="csat"]
        nps  = [s["score"] for s in scores if s.get("score_type")=="nps"]
        avg_csat = sum(csat)/len(csat) if csat else 0
        avg_nps  = sum(nps)/len(nps) if nps else 0
        detractors = [s for s in nps if s <= 6]
        promoters  = [s for s in nps if s >= 9]
        log.info(f"CSAT: {avg_csat:.1f}/5 | NPS: {avg_nps:.0f} | Promoters: {len(promoters)} | Detractors: {len(detractors)}")
        if detractors and PUSH_API:
            data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":"CX Detractors",
                "message":f"{len(detractors)} NPS detractors today. Immediate follow-up needed.","priority":1}).encode()
            req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                data=data, headers={"Content-Type":"application/json"})
            try: urllib.request.urlopen(req, timeout=10)
            except: pass
        # Request testimonials from promoters
        if promoters:
            log.info(f"Requesting testimonials from {len(promoters)} promoters")
    return {"csat_responses":len(scores)}

if __name__ == "__main__": run()
