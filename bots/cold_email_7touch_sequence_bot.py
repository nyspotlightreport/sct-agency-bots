#!/usr/bin/env python3
"""
bots/cold_email_7touch_sequence_bot.py
ENGINE 1: Apollo cold email 200/day + full 7-touch 30-day sequence.
Day 1 curiosity → Day 3 reinforce → Day 5 case study → Day 7 soft CTA
→ Day 14 value content → Day 21 breakup → Day 30 win-back trigger.
Zero pitch until day 7. Never spams. Always delivers value first.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("cold_7touch")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [7-TOUCH] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
now       = datetime.datetime.utcnow()
today     = datetime.date.today()

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
        "system":"You are a world-class B2B copywriter. Write emails that feel human, personalized, and genuinely helpful. Never salesy before day 7. Always lead with value.",
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,
                 "anthropic-version":"2023-06-01","anthropic-beta":"prompt-caching-2024-07-31"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def get_sequence_config():
    cfg = supa("GET","email_sequences_config","",
        "?sequence_key=eq.cold_7_touch_30d&select=touches&limit=1") or []
    if isinstance(cfg, list) and cfg:
        return cfg[0].get("touches", [])
    # Fallback hardcoded
    return [
        {"day":1,"type":"cold_curiosity"},{"day":3,"type":"followup_loom"},
        {"day":5,"type":"case_study"},{"day":7,"type":"soft_cta"},
        {"day":14,"type":"value_content"},{"day":21,"type":"breakup"},
        {"day":30,"type":"winback"}
    ]

def advance_sequences():
    """Find contacts whose next touch is due today and fire it."""
    touches = get_sequence_config()
    due_sequences = supa("GET","outreach_sequences","",
        f"?sequence_name=like.*7-Touch*&status=eq.active&next_touch_at=lte.{now.isoformat()}&select=*&limit=50") or []
    
    if not isinstance(due_sequences, list): return 0
    fired = 0

    for seq in due_sequences:
        contact = supa("GET","contacts","",f"?id=eq.{seq.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact, list) else contact)
        
        step = seq.get("current_step", 0)
        touch = next((t for t in touches if t.get("day", 0) == step), None)
        if not touch: touch = touches[min(step, len(touches)-1)] if touches else {}
        
        touch_type = touch.get("type","cold_curiosity")
        industry   = c.get("industry","their industry")
        company    = c.get("company","your company")
        name       = c.get("name","there")
        
        # Generate email via AI based on touch type
        email_body = ai(
            f"Write email touch #{step+1} ({touch_type}) for {name} at {company} ({industry}).\n"
            f"Day {touch.get('day',step)} in the 7-touch 30-day cold sequence.\n"
            f"Rules: pitch_level={touch.get('pitch_level',0)}/3. Under 100 words. Human voice.\n"
            f"Touch type context: {touch_type}.\n"
            f"If pitch_level=0: pure value or insight. No mention of product.\n"
            f"If pitch_level=1: soft mention of a result we got for someone similar.\n"
            f"If pitch_level=2: mention the free audit at nyspotlightreport.com/audit/\n"
            f"If pitch_level=3: direct but respectful offer or breakup.\n"
            f"Output only the email body. No subject line.",
            max_tokens=150)

        if email_body:
            supa("POST","conversation_log",{
                "contact_id":c["id"],"channel":"email","direction":"outbound",
                "body":email_body,"intent":f"cold_sequence_day{touch.get('day',step)}",
                "agent_name":"7-Touch Cold Engine"})
            
            # Advance sequence to next touch
            next_touches = [t for t in touches if t.get("day",0) > touch.get("day",step)]
            if next_touches:
                days_ahead = next_touches[0]["day"] - touch.get("day",step)
                next_at = (now + datetime.timedelta(days=days_ahead)).isoformat()
                supa("PATCH","outreach_sequences",{
                    "current_step":step+1,"next_touch_at":next_at
                },f"?id=eq.{seq['id']}")
            else:
                supa("PATCH","outreach_sequences",{"status":"completed"},f"?id=eq.{seq['id']}")
            fired += 1

    log.info(f"7-Touch: {fired} sequence touches fired today")
    return fired

def enroll_new_leads():
    """Enroll new Apollo leads (score 40-79) into 7-touch sequence."""
    one_day_ago = (now - datetime.timedelta(hours=24)).isoformat()
    new_leads = supa("GET","contacts","",
        f"?score=gte.40&score=lt.80&stage=eq.LEAD&created_at=gte.{one_day_ago}&select=id,name,company&limit=50") or []
    
    enrolled = 0
    for c in (new_leads if isinstance(new_leads, list) else []):
        existing = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{c['id']}&sequence_name=like.*7-Touch*&select=id&limit=1")
        if existing: continue
        
        campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
        cid = (campaign[0] if isinstance(campaign,list) and campaign else {}).get("id")
        
        supa("POST","outreach_sequences",{
            "campaign_id":cid, "contact_id":c["id"],
            "sequence_name":"7-Touch 30-Day Cold Sequence",
            "current_step":0, "total_steps":7, "status":"active",
            "channel":"email", "next_touch_at":now.isoformat(),
            "notes":"Engine 1: Apollo cold email 7-touch sequence"
        })
        enrolled += 1
    
    log.info(f"7-Touch: {enrolled} new leads enrolled")
    return enrolled

def report_engine_stats():
    """Update closing_engines table with today's numbers."""
    seqs  = supa("GET","outreach_sequences","","?sequence_name=like.*7-Touch*&status=eq.active&select=id") or []
    won   = supa("GET","contacts","","?stage=eq.CLOSED_WON&tags=cs.{cold-email}&select=id") or []
    supa("PATCH","closing_engines",{
        "last_run":now.isoformat(),"total_closes":len(won if isinstance(won,list) else []),
        "status":"active"
    },"?engine_key=eq.cold_email")

def run():
    log.info("ENGINE 1: Cold Email 7-Touch 30-Day Sequence")
    enroll_new_leads()
    fired = advance_sequences()
    report_engine_stats()
    log.info(f"Engine 1 complete. {fired} touches fired today.")

if __name__ == "__main__": run()
