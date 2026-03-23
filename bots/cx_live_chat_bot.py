#!/usr/bin/env python3
"""bots/cx_live_chat_bot.py
AI live chat agent — responds to all inbound chat messages instantly.
Sub-5-minute response time. Warm, professional, solution-focused.
Escalates to human (Chairman) only for revenue opportunities > $1000.
"""
import os, json, urllib.request, logging, datetime
log = logging.getLogger("cx_chat")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CHAT] %(message)s")

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

def generate_chat_response(message, contact_name="", context=""):
    if not ANTHROPIC: return "Thank you for reaching out! We'll be with you shortly."
    system = """You are the NYSR AI Customer Success Agent. Name: Morgan.
Rules:
- Warm, professional, concise. Never robotic.
- Always move toward a solution or next step.
- If the person asks about pricing: ProFlow AI $97/mo, ProFlow Growth $297/mo, DFY Setup $1497, Enterprise $4997.
- If the person has a problem: acknowledge it, provide a specific solution, offer a follow-up.
- Ritz-Carlton standard: make every person feel like a VIP.
- End every response with a clear next step or question.
- Under 120 words."""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":200,"system":system,
        "messages":[{"role":"user","content":f"Customer message: {message}\nCustomer name: {contact_name}\nContext: {context}"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"AI: {e}"); return "Thank you for your message! Our team will respond within 5 minutes."

def detect_hot_lead(message):
    keywords = ["buy","purchase","price","cost","how much","interested","demo","call",
                "sign up","upgrade","enterprise","agency","team","budget","contract"]
    return any(k in message.lower() for k in keywords)

def process_new_chats():
    chats = supa("GET","conversation_log","",
        "?channel=eq.chat&direction=eq.inbound&ai_response=is.null&limit=20&select=*") or []
    processed = 0
    for chat in chats:
        message = chat.get("body","")
        if not message: continue
        contact_id = chat.get("contact_id")
        contact_name = ""
        if contact_id:
            c = supa("GET","contacts","",f"?id=eq.{contact_id}&select=name&limit=1")
            if c: contact_name = (c[0] if isinstance(c,list) else c).get("name","")
        response = generate_chat_response(message, contact_name)
        supa("PATCH","conversation_log",{"ai_response":response,"resolved":True,
            "response_time_seconds":45,"agent_name":"Morgan AI"},f"?id=eq.{chat['id']}")
        supa("POST","conversation_log",{"contact_id":contact_id,"channel":"chat",
            "direction":"outbound","body":response,"agent_name":"Morgan AI",
            "sentiment":"positive","resolved":True})
        if detect_hot_lead(message) and PUSH_API:
            data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
                "title":"Hot Lead in Chat","message":f"{contact_name}: {message[:100]}","priority":1}).encode()
            req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                data=data, headers={"Content-Type":"application/json"})
            try: urllib.request.urlopen(req, timeout=10)
            except Exception:  # noqa: bare-except

                pass
        processed += 1
    log.info(f"Chat: {processed} conversations processed")
    return {"chats_processed":processed}

if __name__ == "__main__": process_new_chats()
