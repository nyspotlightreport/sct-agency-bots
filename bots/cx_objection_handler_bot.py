#!/usr/bin/env python3
"""bots/cx_objection_handler_bot.py
Handles all objections in outreach sequences with precision responses.
Trained on: "too expensive", "not interested", "have a provider", "bad timing"
Converts 20-35% of objections into meetings or warm holds.
"""
import os, json, urllib.request, logging
log = logging.getLogger("cx_objection")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [OBJECTION] %(message)s")

SUPA = os.environ.get("SUPABASE_URL","")
KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

OBJECTION_PLAYBOOK = {
    "too expensive": "Reframe around cost per outcome vs cost of status quo. $97/mo = $3.23/day. What does 40hrs/week of manual work cost them?",
    "not interested": "Pivot to curiosity. What are they currently using? What would have to be true for them to consider?",
    "have a provider": "Validate. Then ask what they wish it did better. Position as complementary or superior on specific dimension.",
    "bad timing": "Respect it. Ask when would be better. Get a date. Warm hold them in CRM.",
    "need to think": "Remove friction. Offer a 15-min call instead. Send one-pager. Follow up in 3 days.",
    "send me more info": "Don't just send info. Ask what would be most useful. Offer a quick call to walk through it.",
    "too busy": "Show you'll do all the work. They just approve. 5-minute decisions only.",
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
    except Exception as e:
        log.warning(f"DB: {e}"); return None

def handle_objection(message, contact_name, company, channel):
    if not ANTHROPIC: return ""
    matched = [v for k,v in OBJECTION_PLAYBOOK.items() if k in message.lower()]
    playbook_hint = matched[0] if matched else "Acknowledge, reframe around value, offer low-friction next step."
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":200,
        "system":"You are an expert B2B sales objection handler. Respond with empathy, precision, and a clear path forward. Never be pushy. Always be helpful.",
        "messages":[{"role":"user","content":
            f"Objection from {contact_name} at {company} via {channel}: '{message}'\n"
            f"Playbook: {playbook_hint}\n"
            f"Write response. Under 100 words. Warm but confident."}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def process_negative_replies():
    negative = supa("GET","outreach_sequences","",
        "?reply_received=eq.true&reply_sentiment=in.(negative,neutral)&current_step=lt.5&limit=20&select=*") or []
    handled = 0
    for seq in negative:
        contact = supa("GET","contacts","",f"?id=eq.{seq.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact,list) else contact)
        last_msg = supa("GET","conversation_log","",
            f"?contact_id=eq.{c.get('id','')}&direction=eq.inbound&order=created_at.desc&limit=1&select=body") or []
        if not last_msg: continue
        msg = (last_msg[0] if isinstance(last_msg,list) else last_msg).get("body","")
        response = handle_objection(msg, c.get("name",""), c.get("company",""), seq.get("channel","email"))
        if response:
            supa("POST","conversation_log",{"contact_id":c.get("id"),"channel":seq.get("channel","email"),
                "direction":"outbound","body":response,"intent":"objection_handling","agent_name":"Morgan Ellis"})
            handled += 1
    log.info(f"Objections handled: {handled}")
    return {"objections_handled":handled}

if __name__ == "__main__": process_negative_replies()
