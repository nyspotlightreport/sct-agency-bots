#!/usr/bin/env python3
"""
bots/annual_prepay_offer_bot.py
Offers annual prepay (15-20% discount) to active monthly subscribers.
Immediate cash flow + locked retention for 12 months.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("annual_prepay")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ANNUAL] %(message)s")

SUPA = os.environ.get("SUPABASE_URL","")
KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

ANNUAL_DISCOUNTS = {
    "proflow_ai":    {"monthly":97,  "annual":982,  "save":182},
    "proflow_growth":{"monthly":297, "annual":2997, "save":567},
    "proflow_elite": {"monthly":797, "annual":7970, "save":1434},
}

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

def ai(prompt, max_tokens=200):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def offer_annual_prepay():
    # Find monthly subscribers not yet offered annual
    monthly = supa("GET","contacts","",
        "?stage=eq.CLOSED_WON&select=*&limit=30") or []
    offered = 0
    for c in monthly:
        tags = c.get("tags",[]) or []
        if "annual-offered" in tags: continue
        tier = next((t for t in ANNUAL_DISCOUNTS if t.replace("_","-") in " ".join(tags)), None)
        if not tier: continue

        disc = ANNUAL_DISCOUNTS[tier]
        msg = ai(
            f"Write an annual prepay offer email for {c.get('name')}.\n"
            f"They pay ${disc['monthly']}/mo. Annual is ${disc['annual']}/yr — saves ${disc['save']}.\n"
            f"Highlight: immediate savings, locked rate, no price increases.\n"
            f"Include a direct upgrade link placeholder: [ANNUAL_UPGRADE_LINK]\n"
            f"Under 80 words. Direct and confident.",
            max_tokens=120)

        if msg:
            supa("POST","conversation_log",{"contact_id":c["id"],"channel":"email",
                "direction":"outbound","body":msg,"intent":"annual_upsell","agent_name":"Annual Prepay Bot"})
            supa("POST","annual_prepay",{"contact_id":c["id"],"tier_key":tier,
                "monthly_price":disc["monthly"],"annual_price":disc["annual"],
                "savings_amount":disc["save"],"savings_pct":15.0,"status":"offered"})
            new_tags = list(set(tags + ["annual-offered"]))
            supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
            offered += 1
    log.info(f"Annual prepay offered: {offered}")
    return offered

if __name__ == "__main__": offer_annual_prepay()
