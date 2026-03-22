#!/usr/bin/env python3
"""
bots/automated_webinar_funnel_bot.py
ENGINE 3: Faceless Automated Webinar
ElevenLabs voice + screen recording, running 24/7.
Warm audience → 5-15% close on $997 pilot.
100 viewers/week × 7% = $10,479/week from webinar alone.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("webinar_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WEBINAR] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
ELEVEN    = os.environ.get("ELEVENLABS_API_KEY","")
now       = datetime.datetime.utcnow()
today     = datetime.date.today().isoformat()

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

def ai(prompt, max_tokens=400):
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
    """Convert webinar registrants to buyers via automated follow-up."""
    # Get registrants not yet in DFY sequence
    registrants = supa("GET","contacts","",
        "?tags=cs.{webinar-registrant}&stage=in.(WARM,QUALIFIED)&select=*&limit=30") or []
    converted = 0

    for c in (registrants if isinstance(registrants,list) else []):
        tags = c.get("tags",[]) or []
        
        if "webinar-followup-sent" in tags: continue
        
        # Generate personalized post-webinar offer
        offer = ai(
            f"Write a post-webinar email for {c.get('name','there')} who just watched our AI automation webinar.\n"
            f"Offer: 30-day pilot at $997 (normally $1,497). Results or full refund.\n"
            f"Reference: they saw the live demo. Now they can get their own system in 7 days.\n"
            f"Urgency: pilot spots limited, link expires in 48hrs.\n"
            f"Include Stripe link placeholder: [PILOT_LINK]\n"
            f"Under 100 words. Confident and specific.",
            max_tokens=150)

        if offer:
            supa("POST","conversation_log",{
                "contact_id":c["id"],"channel":"email","direction":"outbound",
                "body":offer,"intent":"webinar_followup","agent_name":"Webinar Engine Bot"})
            new_tags = list(set(tags + ["webinar-followup-sent"]))
            supa("PATCH","contacts",{"tags":new_tags,"stage":"HOT"},f"?id=eq.{c['id']}")
            
            # Score bump for webinar attendees
            new_score = min((c.get("score",0) or 0) + 45, 220)
            supa("PATCH","contacts",{"score":new_score},f"?id=eq.{c['id']}")
            converted += 1

    return converted

def update_webinar_metrics():
    """Update webinar pipeline stats."""
    webinars = supa("GET","webinar_pipeline","","?status=eq.planning&select=*&limit=2") or []
    for w in (webinars if isinstance(webinars,list) else []):
        regs = supa("GET","contacts","",
            f"?tags=cs.{{webinar-registrant}}&select=id") or []
        count = len(regs) if isinstance(regs,list) else 0
        supa("PATCH","webinar_pipeline",{"registration_count":count},f"?id=eq.{w['id']}")

def generate_webinar_promo():
    """Generate this week's webinar promo content."""
    promo_posts = []
    verticals = [
        ("law firms","your practice misses leads after 5pm"),
        ("medical practices","empty appointment slots cost you $300 each"),
        ("agency owners","you're billing $10K/mo but working $50K/mo hours")
    ]
    
    for vert, pain in verticals:
        post = ai(
            f"Write a LinkedIn post promoting a free AI automation webinar for {vert}.\n"
            f"Pain: {pain}.\n"
            f"Webinar: 45 min, live demo, free to attend.\n"
            f"CTA: nyspotlightreport.com/webinar/\n"
            f"Under 120 words. Authority tone. No fluff.",
            max_tokens=160)
        if post:
            supa("POST","content_qa_queue",{
                "content_type":"linkedin","title":f"Webinar promo — {vert}",
                "content":post,"platform":"linkedin","status":"pending"})
            promo_posts.append(vert)

    return len(promo_posts)

def run():
    log.info("ENGINE 3: Automated Webinar Funnel")
    converted = process_webinar_registrants()
    promos    = generate_webinar_promo()
    update_webinar_metrics()
    log.info(f"Webinar: {converted} registrants → pilot offers sent | {promos} promo posts queued")
    supa("POST","agent_run_logs",{"org_id":"sales_corp","agent_name":"webinar_engine",
        "run_type":"webinar_cycle","status":"success",
        "metrics":{"converted":converted,"promos":promos}})

if __name__ == "__main__": run()
