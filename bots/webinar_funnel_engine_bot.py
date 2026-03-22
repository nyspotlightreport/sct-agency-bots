#!/usr/bin/env python3
"""
bots/webinar_funnel_engine_bot.py
ENGINE 3: Automated Webinar Funnel 24/7.
Pre-recorded 45-min ElevenLabs presentation → registration page → 
automated follow-up → pilot close at $997.
Sean records/generates once. Never touched again.
EverWebinar handles automated scheduling. 5-15% of viewers convert.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("webinar_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WEBINAR] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
now       = datetime.datetime.utcnow()

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

def ai(prompt, max_tokens=300):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def process_webinar_registrants():
    """Find webinar registrants and enroll in post-webinar close sequence."""
    registrants = supa("GET","contacts","",
        "?tags=cs.{webinar-registrant}&tags=not.cs.{webinar-sequence-enrolled}&select=*&limit=30") or []
    
    enrolled = 0
    for c in (registrants if isinstance(registrants, list) else []):
        tags = c.get("tags", []) or []
        
        # Get webinar config
        cfg = supa("GET","webinar_funnel_config","","?config_key=eq.main_webinar&select=*&limit=1") or []
        offer_price = (cfg[0] if isinstance(cfg,list) and cfg else {}).get("offer_price", 997)
        
        # Enroll in 5-step webinar follow-up sequence
        for i, (days, intent, subject) in enumerate([
            (0,  "webinar_immediate",  "Your webinar access + 3 exclusive bonuses"),
            (1,  "webinar_dfy_offer",  "The exact system I showed you — yours in 24 hours"),
            (3,  "webinar_question",   "Quick question about your business"),
            (5,  "webinar_roi",        "I ran the numbers for your business"),
            (7,  "webinar_final",      "Last chance — bonuses expire tonight"),
        ]):
            msg = ai(
                f"Write email {i+1}/5 for webinar follow-up.\n"
                f"Contact: {c.get('name')} at {c.get('company')}.\n"
                f"Intent: {intent}. Subject: {subject}.\n"
                f"Pilot offer: ${offer_price}. Full DFY: $1,497. Applies toward full.\n"
                f"Day {days} after webinar. Under 120 words. Direct and conversational.",
                max_tokens=180)
            
            if msg:
                send_at = (now + datetime.timedelta(days=days)).isoformat()
                supa("POST","conversation_log",{
                    "contact_id":c["id"],"channel":"email","direction":"outbound",
                    "body":msg,"intent":intent,"agent_name":"Webinar Engine Bot"
                })
        
        # Tag as enrolled
        new_tags = list(set(tags + ["webinar-sequence-enrolled"]))
        supa("PATCH","contacts",{"tags":new_tags,"stage":"HOT","score":85},f"?id=eq.{c['id']}")
        enrolled += 1
    
    return enrolled

def drive_traffic_to_webinar():
    """Generate social/email copy pointing to webinar registration."""
    webinar_url = "https://nyspotlightreport.com/webinar/"
    
    traffic_copy = ai(
        f"Write 3 short social posts (Twitter/LinkedIn) promoting a free live demo webinar:\n"
        f"Title: How NY Businesses Are Saving 20+ Hours/Week with AI\n"
        f"URL: {webinar_url}\n"
        f"Offer: Free to attend. $997 pilot for live attendees only.\n"
        f"Each post under 250 chars. Different angles. Include URL.",
        max_tokens=300)
    
    if traffic_copy:
        supa("POST","content_qa_queue",{
            "content_type":"linkedin","title":"Webinar Promotion Posts",
            "content":traffic_copy,"platform":"social","status":"pending"
        })
    
    log.info("Webinar traffic copy queued for publication")

def generate_webinar_script():
    """Generate the 45-minute webinar script for ElevenLabs voice generation."""
    cfg = supa("GET","webinar_funnel_config","","?config_key=eq.main_webinar&select=*&limit=1") or []
    c = (cfg[0] if isinstance(cfg,list) and cfg else {})
    
    if c.get("status") != "building": return
    
    script = ai(
        f"Write a 45-minute webinar script outline for:\n"
        f"Title: {c.get('title','')}\n"
        f"Format: 30 min value content + 15 min live demo + offer at end.\n"
        f"Offer: {c.get('offer_at_end','')} at ${c.get('offer_price',997)}\n"
        f"Structure: Hook (5 min) → Problem (5 min) → Solution framework (10 min) → Live demo (10 min) → Results/proof (5 min) → Offer (10 min)\n"
        f"Voice: S.C. Thomas, Chairman of NY Spotlight Report. Confident, direct, practical.\n"
        f"Write the actual script with speaking notes. Under 1500 words.",
        max_tokens=1200)
    
    if script:
        supa("PATCH","webinar_funnel_config",{
            "status":"script_ready"
        },"?config_key=eq.main_webinar")
        
        # Save to content queue for review
        supa("POST","content_qa_queue",{
            "content_type":"webinar_script","title":"Main Webinar 45-min Script",
            "content":script,"platform":"elevenlabs","status":"pending",
            "qa_score":5
        })
        log.info("Webinar script generated and queued for ElevenLabs voice generation")

def run():
    log.info("ENGINE 3: Automated Webinar Funnel 24/7")
    enrolled = process_webinar_registrants()
    drive_traffic_to_webinar()
    generate_webinar_script()
    supa("PATCH","closing_engines",{"last_run":now.isoformat(),"status":"active"},
         "?engine_key=eq.webinar_funnel")
    log.info(f"Webinar engine: {enrolled} registrants enrolled in close sequence")

if __name__ == "__main__": run()
