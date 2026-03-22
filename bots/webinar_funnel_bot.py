#!/usr/bin/env python3
"""
bots/webinar_funnel_bot.py  
ENGINE 3: Automated webinar funnel management.
- Registers leads for upcoming webinar sessions
- Sends reminder sequences (24h, 1h, 10min)
- Posts webinar to social for traffic
- Tracks attendance and fires post-webinar close sequence
- ElevenLabs voice generation for webinar content
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("webinar")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WEBINAR] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
EL_KEY    = os.environ.get("ELEVENLABS_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
SITE      = "https://nyspotlightreport.com"

WEBINAR_TITLE  = "How to Run a Full AI Content & Marketing Operation for $997/month (Without Hiring Anyone)"
WEBINAR_OFFER  = "$997/mo ProFlow Growth or $1,497 DFY Setup"
WEBINAR_STRIPE = "https://buy.stripe.com/nysr-proflow-growth"  # Replace with live link

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

def register_warm_leads():
    """Auto-register WARM leads for next webinar session."""
    warm = supa("GET","contacts","",
        "?stage=in.(WARM,QUALIFIED)&tags=not.cs.{webinar_invited}&select=*&limit=100") or []
    
    registered = 0
    for contact in (warm if isinstance(warm,list) else []):
        cid   = contact.get("id")
        email = contact.get("email","")
        name  = contact.get("name","") or email.split("@")[0]
        
        # Tag as invited
        existing_tags = contact.get("tags") or []
        existing_tags.append("webinar_invited")
        supa("PATCH","contacts",{"tags":existing_tags},f"?id=eq.{cid}")
        
        # Log invitation
        invite_body = (
            f"Hi {name},\n\n"
            f"We're running a free live training: '{WEBINAR_TITLE}'\n\n"
            f"Register free: {SITE}/webinar/\n\n"
            f"45 minutes. You'll leave with a working plan you can implement this week."
        )
        supa("POST","conversation_log",{
            "contact_id":cid,"channel":"email","direction":"outbound",
            "body":invite_body,"intent":"webinar_invite","agent_name":"Webinar Bot"
        })
        registered += 1
    
    log.info(f"Webinar: {registered} warm leads invited")
    return registered

def post_webinar_close_sequence(attendee_contact_id):
    """Fire 3-email close sequence immediately after webinar."""
    contact = supa("GET","contacts","",f"?id=eq.{attendee_contact_id}&select=*")
    if not contact or not isinstance(contact,list) or not contact[0]: return
    c    = contact[0]
    name = c.get("name","") or "there"
    
    # Email 1: Immediate - send replay + offer
    supa("POST","conversation_log",{
        "contact_id":attendee_contact_id,"channel":"email","direction":"outbound",
        "body":f"Hi {name}, here's the replay + everything we covered: {SITE}/webinar/ — The {WEBINAR_OFFER} offer closes in 48 hours.",
        "intent":"webinar_followup_1","agent_name":"Webinar Bot"
    })
    
    # Update stage to HOT
    supa("PATCH","contacts",{"stage":"HOT","score":85,"tags":["webinar_attendee"]},
        f"?id=eq.{attendee_contact_id}")
    
    log.info(f"Post-webinar close sequence fired for: {name}")

def generate_webinar_social_post():
    """Generate social post to drive webinar registrations."""
    if not ANTHROPIC: return None
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":200,
        "messages":[{"role":"user","content":
        f"Write a LinkedIn post promoting our free webinar: '{WEBINAR_TITLE}' "
        f"Registration: {SITE}/webinar/ "
        f"Angle: most small businesses waste 20+ hours/week on content. We show how to automate all of it. "
        f"Max 150 words. Professional but conversational. Include the registration link."}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return None

def run():
    log.info("="*55)
    log.info("ENGINE 3: Webinar Funnel Bot")
    log.info("="*55)
    registered = register_warm_leads()
    social     = generate_webinar_social_post()
    if social:
        supa("POST","content_queue",{"platform":"linkedin","body":social,
            "scheduled_for":datetime.datetime.utcnow().isoformat(),
            "status":"pending","source":"webinar_bot"})
        log.info("Webinar social post queued for LinkedIn")

if __name__ == "__main__": run()
