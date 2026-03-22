#!/usr/bin/env python3
"""
bots/seven_touch_close_sequence_bot.py
ENGINE 1: Apollo Cold Email — 7-touch sequence at scale
200 emails/day × 30 days = 6,000 contacts/month
1% close rate = 60 new clients/month = $58K+ MRR
All 7 touches automated. Day 1 curiosity → Day 30 win-back.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("7touch")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [7-TOUCH] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
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
    except Exception as e: log.debug(f"Supa: {e}"); return None

def ai(prompt, max_tokens=250):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "system":"You are a B2B cold email copywriter. 3-sentence max per email. No fluff. High curiosity, low pitch.",
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,
                 "anthropic-version":"2023-06-01","anthropic-beta":"prompt-caching-2024-07-31"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

# 7-touch sequence config
SEQUENCE = [
    {"day":1,  "type":"curiosity",    "subject":"Built something for [niche]",
     "prompt":"Write a 3-sentence cold email. Pain point specific to [industry] → 1 proof point → CTA to watch 4-min Loom at https://nyspotlightreport.com/webinar/. No pitch. No pricing. High curiosity."},
    {"day":3,  "type":"followup",     "subject":"Making sure this didn't get buried",
     "prompt":"2-sentence follow-up. Reference the Loom showing specific result in first 30 days. Link to https://nyspotlightreport.com/proflow/"},
    {"day":5,  "type":"social_proof", "subject":"What 30 days looks like",
     "prompt":"1-line intro + forward a testimonial. This is what 30 days looks like for [similar company]. Keep under 60 words."},
    {"day":7,  "type":"soft_breakup", "subject":"Last email from me",
     "prompt":"Last email — won't follow up again. Free AI audit at https://nyspotlightreport.com/audit/ — no strings. 2 sentences."},
    {"day":14, "type":"value",        "subject":"Thought this was relevant to you",
     "prompt":"Share a relevant insight or blog post. Zero pitch. Pure value. 2 sentences max."},
    {"day":21, "type":"breakup",      "subject":"Closing your file",
     "prompt":"Final close email. Closing their file. If timing ever right: [Stripe link]. 2 sentences."},
    {"day":30, "type":"winback",      "subject":"Noticed you looked at this a few weeks ago",
     "prompt":"Win-back for anyone who opened but never clicked. Reference what changed since then. New result or new offer. 2 sentences."},
]

def advance_sequences():
    """Move every active sequence to its next touch based on timing."""
    active = supa("GET","outreach_sequences","",
        "?status=eq.active&select=*&limit=100") or []
    advanced = 0; sent = 0

    for seq in (active if isinstance(active,list) else []):
        step       = seq.get("current_step",0) or 0
        sequence_name = seq.get("sequence_name","")
        
        # Only process 7-touch cold sequences
        if "7-Touch" not in sequence_name and "Cold" not in sequence_name:
            continue
        if step >= len(SEQUENCE): continue

        # Check if it's time for next touch
        last_touch = seq.get("last_touch_at") or seq.get("created_at","")
        if not last_touch: continue
        try:
            last_dt = datetime.datetime.fromisoformat(last_touch.replace("Z","+00:00"))
            days_since = (now.replace(tzinfo=datetime.timezone.utc) - last_dt.replace(tzinfo=datetime.timezone.utc)).days
            touch = SEQUENCE[step]
            if days_since < touch["day"] - (SEQUENCE[step-1]["day"] if step > 0 else 0):
                continue
        except: continue

        # Get contact
        contact = supa("GET","contacts","",f"?id=eq.{seq.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact,list) else contact)

        # Generate personalized email
        industry = c.get("industry","business") or "business"
        name     = c.get("name","") or ""
        company  = c.get("company","") or ""
        
        prompt = SEQUENCE[step]["prompt"].replace("[industry]",industry).replace("[niche]",industry)
        if company: prompt += f" Company: {company}."
        
        body = ai(prompt)
        if not body: continue

        # Log to conversation
        supa("POST","conversation_log",{
            "contact_id":c["id"],"channel":"email","direction":"outbound",
            "body":body,"intent":f"cold_sequence_touch_{step+1}",
            "agent_name":"7-Touch Close Bot"})

        # Advance sequence
        supa("PATCH","outreach_sequences",{
            "current_step":step+1,
            "last_touch_at":now.isoformat(),
            "status":"active" if step+1 < len(SEQUENCE) else "completed",
            "next_touch_at":(now + datetime.timedelta(days=SEQUENCE[min(step+1,len(SEQUENCE)-1)]["day"] - touch["day"])).isoformat()
        },f"?id=eq.{seq['id']}")
        
        sent += 1

    log.info(f"7-Touch Engine: {sent} emails sent across {len(active if isinstance(active,list) else [])} sequences")
    return sent

def enroll_new_cold_leads():
    """Enroll all new COLD contacts in 7-touch sequence."""
    cold = supa("GET","contacts","","?stage=eq.COLD&select=id,tags&limit=50") or []
    enrolled = 0
    
    campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
    cid = (campaign[0] if isinstance(campaign,list) and campaign else {}).get("id")

    for c in (cold if isinstance(cold,list) else []):
        tags = c.get("tags",[]) or []
        if "7touch-enrolled" in tags: continue
        
        # Check no existing sequence
        existing = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{c['id']}&status=eq.active&limit=1&select=id")
        if existing: continue

        supa("POST","outreach_sequences",{
            "campaign_id":cid,"contact_id":c["id"],
            "sequence_name":"7-Touch Cold Close Sequence",
            "current_step":0,"total_steps":7,"status":"active","channel":"email",
            "next_touch_at":now.isoformat()
        })
        new_tags = list(set(tags + ["7touch-enrolled"]))
        supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
        enrolled += 1
    
    return enrolled

def update_engine_stats(sent, enrolled):
    supa("PATCH","closing_engines",{
        "last_run":now.isoformat(),
        "total_closes__add":0
    },"?engine_key=eq.cold_outreach")
    supa("POST","agent_run_logs",{"org_id":"sales_corp","agent_name":"seven_touch_engine",
        "run_type":"sequence_advance","status":"success",
        "metrics":{"sent":sent,"enrolled":enrolled}})

def run():
    log.info("ENGINE 1: 7-Touch Cold Outreach — Advancing all sequences")
    sent     = advance_sequences()
    enrolled = enroll_new_cold_leads()
    update_engine_stats(sent, enrolled)
    log.info(f"Complete: {sent} touches sent | {enrolled} new leads enrolled")

if __name__ == "__main__": run()
