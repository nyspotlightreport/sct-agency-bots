#!/usr/bin/env python3
"""
bots/referral_engine_bot.py  (UPGRADED — Engine 6)
Automated referral at Day 7, Day 30, Day 60 for every paying client.
Highest-margin close possible: $0 CAC. High trust. Faster close cycle.
At 50 clients, 1 referral/quarter each = 12-13 additional closes/week.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("referral_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REFERRAL] %(message)s")

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

REFERRAL_TOUCHPOINTS = [7, 30, 60]  # Days after conversion to ask

def fire_referral_asks():
    """Fire referral ask at exactly day 7, 30, 60 post-conversion."""
    clients = supa("GET","contacts","","?stage=eq.CLOSED_WON&select=*&limit=50") or []
    fired = 0

    for c in (clients if isinstance(clients,list) else []):
        conv_at = c.get("converted_at")
        if not conv_at: continue
        
        try:
            conv_date = datetime.datetime.fromisoformat(conv_at.replace("Z","+00:00"))
            days_since = (now.replace(tzinfo=datetime.timezone.utc) - conv_date.replace(tzinfo=datetime.timezone.utc)).days
        except: continue
        
        tags = c.get("tags",[]) or []
        
        for touchday in REFERRAL_TOUCHPOINTS:
            tag_key = f"referral-day{touchday}-sent"
            if tag_key in tags: continue
            
            # Fire within ±1 day window
            if abs(days_since - touchday) > 1: continue
            
            # Tier-specific reward
            tier = next((t for t in ["dfy-agency","dfy-setup","proflow-elite","proflow-growth","proflow-ai"]
                        if t in " ".join(tags)), "proflow-ai")
            rewards = {"dfy-agency":"$500 + 10% first year","dfy-setup":"$297 cash",
                      "proflow-elite":"$250 cash","proflow-growth":"$150 cash","proflow-ai":"1 free month"}
            reward = rewards.get(tier, "$97 credit")
            
            # Personalize by day
            if touchday == 7:
                context = f"They just completed their first week with us at day {days_since}. Ask casually — they have just seen initial results."
            elif touchday == 30:
                context = f"They have been using the system for a month. They have seen measurable results. Natural time to ask."
            else:
                context = f"They are a 60-day client. Loyal and seeing ongoing value. They definitely know people who need this."
            
            msg = ai(
                f"Write a referral ask email for {c.get('name')} (Day {touchday} touchpoint).\n"
                f"Context: {context}\n"
                f"Reward if they refer someone: {reward}.\n"
                f"Include placeholder: [YOUR_REFERRAL_LINK].\n"
                f"Tone: casual and grateful. Not pushy. Under 80 words.",
                max_tokens=120)
            
            if msg:
                supa("POST","conversation_log",{
                    "contact_id":c["id"],"channel":"email","direction":"outbound",
                    "body":msg,"intent":f"referral_ask_day{touchday}",
                    "agent_name":"Referral Engine"})
                supa("POST","referral_requests_log",{
                    "contact_id":c["id"],"request_channel":"email"})
                new_tags = list(set(tags + [tag_key, "referral-requested"]))
                supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
                fired += 1
                break  # Only one touchpoint per run

    supa("PATCH","closing_engines",{"last_run":now.isoformat(),"status":"active"},
         "?engine_key=eq.referral")
    log.info(f"Referral Engine: {fired} asks fired (Day 7/30/60 touchpoints)")
    return fired

if __name__ == "__main__": fire_referral_asks()
