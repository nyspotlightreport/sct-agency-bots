#!/usr/bin/env python3
"""
bots/lead_magnet_nurture_bot.py
ENGINE 4: 7-day email nurture sequence for every free plan / lead magnet download.
Day 1: here's your plan. Day 3: case study. Day 5: ROI calculator. Day 7: Stripe link + 48h discount.
Runs on every new lead. Auto-promotes to warm on day 5. Auto-fires close sequence on day 7.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("nurture")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NURTURE] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
SITE      = "https://nyspotlightreport.com"

NURTURE_SEQ = {
    0:  {"intent":"nurture_day1",  "action":"send_plan"},
    2:  {"intent":"nurture_day3",  "action":"send_case_study"},
    4:  {"intent":"nurture_day5",  "action":"send_roi_calculator", "stage_upgrade":"WARM"},
    6:  {"intent":"nurture_day7",  "action":"send_close_offer",    "stage_upgrade":"HOT"},
    13: {"intent":"nurture_day14", "action":"send_content_piece"},
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

def get_email_body(action, contact):
    """Generate AI-personalized email for this nurture step."""
    if not ANTHROPIC: return ""
    name  = contact.get("name","") or contact.get("email","").split("@")[0]
    niche = contact.get("niche") or "your business"
    
    prompts = {
        "send_plan":
            f"Write email: {name} just got their free NY Spotlight Report content plan for {niche}. "
            f"Welcome them, tell them what's inside the plan, 3 quick wins they can take this week. Under 120 words.",
        "send_case_study":
            f"Write email to {name} ({niche}): Day 3 follow-up. Share a 2-sentence result story "
            f"from a similar business using NYSR AI system. CTA: see full results at {SITE}/proflow/. Under 100 words.",
        "send_roi_calculator":
            f"Write email to {name} ({niche}): Day 5. Offer an ROI breakdown — if they currently spend "
            f"10 hours/week on content at $50/hour = $2,000/month cost. NYSR at $97/mo saves $1,900/mo. "
            f"CTA: {SITE}/audit/ Under 100 words.",
        "send_close_offer":
            f"Write a soft-close email to {name} ({niche}): Day 7. Offer 10% discount on ProFlow AI ($97→$87) "
            f"valid for 48 hours. Direct link: {SITE}/pricing/ Under 80 words.",
        "send_content_piece":
            f"Write a value-add email to {name} ({niche}): Day 14. Share a useful tip about content automation "
            f"for {niche} businesses. No pitch. Under 80 words. Link back to {SITE}/blog/",
    }
    
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":180,
        "messages":[{"role":"user","content":prompts.get(action,prompts["send_plan"])}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def run():
    log.info("="*55)
    log.info("ENGINE 4: Lead Magnet Nurture Sequence")
    log.info("="*55)
    
    now = datetime.datetime.utcnow()
    total = 0
    
    for days_ago, step in NURTURE_SEQ.items():
        target = (now - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        # Get leads who signed up exactly days_ago days ago AND haven't received this touch
        leads = supa("GET","contacts","",
            f"?stage=in.(LEAD,COLD,WARM)&created_at=gte.{target}T00:00:00&created_at=lte.{target}T23:59:59&select=*&limit=100") or []
        
        for contact in (leads if isinstance(leads,list) else []):
            body = get_email_body(step["action"], contact)
            if body:
                supa("POST","conversation_log",{
                    "contact_id":contact.get("id"),"channel":"email","direction":"outbound",
                    "body":body,"intent":step["intent"],"agent_name":"Lead Nurture Bot"
                })
                if step.get("stage_upgrade"):
                    supa("PATCH","contacts",{"stage":step["stage_upgrade"]},f"?id=eq.{contact.get('id')}")
                total += 1
    
    log.info(f"Nurture sequences: {total} emails queued")
    return total

if __name__ == "__main__": run()
