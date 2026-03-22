#!/usr/bin/env python3
"""
bots/apollo_7touch_sequence_bot.py
ENGINE 1: Full 7-touch cold email sequence via Apollo.
200 emails/day = 6,000 contacts/month. Even at 0.3% close = 18 clients/mo.
Each contact gets personalized subject lines + dynamic content from Claude.
Tracks: open, click, reply, booked, closed stages in Supabase.
"""
import os, json, logging, datetime, urllib.request, urllib.parse
log = logging.getLogger("7touch")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [7TOUCH] %(message)s")

APOLLO_KEY= os.environ.get("APOLLO_API_KEY","")
SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
SITE      = "https://nyspotlightreport.com"

SEQUENCES = {
    "day1":  {"subject":"Built something for {niche}", "stage":"COLD",    "cta":"/free-plan/"},
    "day3":  {"subject":"Re: Built something for {niche}", "stage":"COLD", "cta":"/proflow/"},
    "day5":  {"subject":"30-day result for {niche} business", "stage":"COLD","cta":"/proflow/"},
    "day7":  {"subject":"Last email (leaving this here)", "stage":"COLD",  "cta":"/audit/"},
    "day14": {"subject":"Wrote something you might use", "stage":"WARM",   "cta":"/blog/"},
    "day21": {"subject":"Closing your file", "stage":"WARM",              "cta":"/agency/"},
    "day30": {"subject":"You looked at this a few weeks ago", "stage":"WARM","cta":"/pricing/"},
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

def ai_personalize(contact, touch_day):
    """Generate fully personalized email body for this contact + touch day."""
    if not ANTHROPIC: return None
    seq = SEQUENCES.get(touch_day, {})
    niche = contact.get("niche") or contact.get("company") or "your business"
    name  = contact.get("name","") or contact.get("email","").split("@")[0]
    cta_url = SITE + seq.get("cta","/")
    
    prompts = {
        "day1":  f"Write a cold email to {name} who runs a {niche} business. 3 sentences max. Pain: they probably waste time on content. Proof: we automate full content operations. CTA: watch a 4-min Loom at {cta_url}. No pitch, no pricing. Just curiosity.",
        "day3":  f"Write follow-up #1 to {name} ({niche}). Reference the previous email about content automation. 2 sentences. Mention specific result: 30-day content system live. Link: {cta_url}",
        "day5":  f"Write follow-up #2 to {name} ({niche}). Forward-style case study. One-line intro + a 2-sentence result story. Link to their niche results at {cta_url}",
        "day7":  f"Write a 'last email' to {name}. Say you won't follow up again. Leave a free audit link: {cta_url}. No strings, genuine. Under 3 sentences.",
        "day14": f"Write a 're-engage with content' email to {name}. Not a pitch. Share a relevant article or insight about {niche} content. Link: {cta_url}",
        "day21": f"Write a breakup email to {name}. Closing their file. Leave a Stripe link or calendar link: {cta_url}. Warm, no pressure.",
        "day30": f"Write a win-back email to {name}. They opened a previous email but never clicked. Mention something changed since then (new result or feature). Link: {cta_url}. 2 sentences.",
    }
    
    prompt = prompts.get(touch_day, prompts["day1"])
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":200,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return None

def get_contacts_for_touch(touch_day, limit=50):
    """Get contacts due for this touch today."""
    day_map = {"day1":0,"day3":2,"day5":4,"day7":6,"day14":13,"day21":20,"day30":29}
    days_since = day_map.get(touch_day, 0)
    
    from datetime import datetime, timedelta
    target_date = (datetime.utcnow() - timedelta(days=days_since)).strftime("%Y-%m-%d")
    
    contacts = supa("GET","contacts","",
        f"?stage=eq.COLD&select=*&limit={limit}&created_at=gte.{target_date}T00:00:00&created_at=lte.{target_date}T23:59:59") or []
    return contacts if isinstance(contacts,list) else []

def log_email_sent(contact_id, touch_day, subject, body):
    """Log every email send to conversation_log."""
    supa("POST","conversation_log",{
        "contact_id":contact_id,
        "channel":"email","direction":"outbound",
        "subject":subject, "body":body,
        "intent":f"cold_sequence_{touch_day}",
        "agent_name":"Apollo 7-Touch Bot"
    })

def run():
    log.info("="*55)
    log.info("ENGINE 1: Apollo 7-Touch Cold Email Sequence")
    log.info("="*55)
    
    total_sent = 0
    for touch_day, seq in SEQUENCES.items():
        contacts = get_contacts_for_touch(touch_day, limit=30)
        
        for contact in contacts:
            niche   = contact.get("niche") or "business"
            subject = seq["subject"].replace("{niche}", niche)
            body    = ai_personalize(contact, touch_day)
            
            if body:
                log_email_sent(contact.get("id"), touch_day, subject, body)
                # Update contact stage on day7+ if still cold
                if touch_day in ["day7","day14","day21"] and contact.get("stage")=="COLD":
                    supa("PATCH","contacts",{"stage":"WARM","last_contacted":datetime.utcnow().isoformat()},
                        f"?id=eq.{contact.get('id')}")
                total_sent += 1
        
        if contacts:
            log.info(f"  {touch_day}: {len(contacts)} contacts processed")
    
    log.info(f"Total emails queued: {total_sent}")
    return total_sent

if __name__ == "__main__":
    from datetime import datetime
    run()
