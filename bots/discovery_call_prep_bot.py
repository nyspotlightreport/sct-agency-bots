#!/usr/bin/env python3
"""
bots/discovery_call_prep_bot.py
Generates discovery call prep packets for every booked call.
Framework: Their Agenda → Pain Excavation → Solution Framing → Close → Next Step Lock
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("discovery_prep")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DISCOVERY] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
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
    except: return None

def ai(prompt, max_tokens=600):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def prep_discovery_calls():
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    calls = supa("GET","appointments","",
        f"?appointment_type=eq.discovery&status=eq.confirmed&scheduled_at=gte.{tomorrow}T00:00:00&select=*") or []
    prepped = 0
    for call in calls:
        if call.get("prep_notes"): continue
        contact = supa("GET","contacts","",f"?id=eq.{call.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact,list) else contact)

        prep = ai(
            f"Generate a discovery call prep packet for: {c.get('name')} | {c.get('title')} at {c.get('company')}\n"
            f"Industry: {c.get('industry')} | Score: {c.get('score')} | Source: {c.get('source')}\n"
            f"Notes: {c.get('notes','')}\n\n"
            f"NYSR Discovery Call Framework (20 min):\n"
            f"Min 1-3: Their agenda — open with 'What made you take this call today?'\n"
            f"Min 4-8: Pain excavation — How long? What tried? Cost of NOT fixing?\n"
            f"Min 9-14: Solution framing — Reflect pain in their words, case study\n"
            f"Min 15-18: Close attempt #1 — ROI calc, recommended product\n"
            f"Min 19-20: Next step lock — NEVER end without committed next step\n\n"
            f"Generate:\n"
            f"1. 3 discovery questions specific to their industry/situation\n"
            f"2. Likely pain points based on their profile\n"
            f"3. Best product to recommend with ROI estimate\n"
            f"4. 2 objections likely to come up + how to handle each\n"
            f"5. Proposed next step to close with\n"
            f"Format as structured notes. Under 400 words.",
            max_tokens=500)

        if prep:
            supa("PATCH","appointments",{"prep_notes":prep},f"?id=eq.{call['id']}")
            if PUSH_API and PUSH_USER:
                data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
                    "title":f"Call Tomorrow: {c.get('name')}",
                    "message":f"{c.get('title')} at {c.get('company')}\nScore: {c.get('score')}\nPrep packet ready."}).encode()
                req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                    data=data, headers={"Content-Type":"application/json"})
                try: urllib.request.urlopen(req, timeout=10)
                except: pass
            prepped += 1
    log.info(f"Discovery calls prepped: {prepped}")
    return prepped

if __name__ == "__main__": prep_discovery_calls()
