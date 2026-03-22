#!/usr/bin/env python3
"""
bots/rep_performance_scoring_bot.py
ENGINE 2: Weekly rep scoring + accountability automation.
Bottom 20%: automated coaching email.
Top 20%: bonus tier unlocked notification.
30-day probation enforcement.
Commission tier upgrades based on volume.
Zero Sean involvement.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("rep_score")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REP SCORE] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

COMMISSION_TIERS = {
    "standard": {"min_closes":0,  "pct":0.30, "label":"Standard (30%)"},
    "bronze":   {"min_closes":3,  "pct":0.33, "label":"Bronze (33%)"},
    "silver":   {"min_closes":6,  "pct":0.35, "label":"Silver (35%)"},
    "gold":     {"min_closes":10, "pct":0.38, "label":"Gold (38%)"},
    "platinum": {"min_closes":20, "pct":0.41, "label":"Platinum (41%)"},
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

def ai_coaching_email(rep_name, closes, avg_rep_closes):
    if not ANTHROPIC: return None
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":250,
        "messages":[{"role":"user","content":
        f"Write a coaching email to {rep_name}, a sales rep who closed {closes} deals this month "
        f"(team average is {avg_rep_closes:.1f}). Warm, supportive tone. Include 2 specific tactical tips "
        f"for selling AI content automation to small businesses. Under 150 words."}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return None

def score_reps():
    reps = supa("GET","sales_reps","","?status=eq.active&select=*") or []
    if not isinstance(reps,list) or not reps: return
    
    # Calculate closes per rep this month
    now = datetime.datetime.utcnow()
    month_start = now.strftime("%Y-%m-01")
    
    rep_scores = []
    for rep in reps:
        rid = rep.get("id")
        sales = supa("GET","rep_sales","",
            f"?rep_id=eq.{rid}&status=eq.closed&closed_at=gte.{month_start}T00:00:00&select=id") or []
        closes = len(sales) if isinstance(sales,list) else 0
        rep_scores.append({"rep":rep,"closes":closes})
    
    rep_scores.sort(key=lambda x: x["closes"])
    avg = sum(r["closes"] for r in rep_scores) / max(len(rep_scores),1)
    n   = len(rep_scores)
    
    bottom_20_cutoff = max(1, n//5)
    top_20_cutoff    = max(1, n - n//5)
    
    for i, item in enumerate(rep_scores):
        rep    = item["rep"]
        closes = item["closes"]
        rid    = rep.get("id")
        name   = f"{rep.get('first_name','')} {rep.get('last_name','')}"
        
        # Determine commission tier
        tier = "standard"
        total_closes = rep.get("total_closes",0) + closes
        for t_name, t_data in reversed(list(COMMISSION_TIERS.items())):
            if total_closes >= t_data["min_closes"]:
                tier = t_name
                break
        
        # Update tier in DB
        supa("PATCH","sales_reps",{"notes":f"tier:{tier}","total_closes":total_closes},f"?id=eq.{rid}")
        
        if i < bottom_20_cutoff and closes < avg * 0.5:
            # Coaching email
            coaching = ai_coaching_email(name, closes, avg)
            if coaching:
                supa("POST","conversation_log",{
                    "channel":"email","direction":"outbound",
                    "body":coaching,"intent":"rep_coaching",
                    "agent_name":"Rep Performance Bot"
                })
                log.info(f"COACHING: {name} — {closes} closes (avg {avg:.1f}) — coaching email queued")
        
        elif i >= top_20_cutoff and closes > avg * 1.5:
            # Bonus tier notification
            log.info(f"TOP REP: {name} — {closes} closes — {COMMISSION_TIERS[tier]['label']} unlocked")
            supa("POST","conversation_log",{
                "channel":"email","direction":"outbound",
                "body":f"Congrats {name}! You've unlocked {COMMISSION_TIERS[tier]['label']} commission tier. Your rate is now {int(COMMISSION_TIERS[tier]['pct']*100)}% on all closes.",
                "intent":"rep_bonus_tier","agent_name":"Rep Performance Bot"
            })
        
        # 30-day probation check
        created = rep.get("created_at","")
        if created:
            try:
                created_dt = datetime.datetime.fromisoformat(created.replace("Z","+00:00"))
                days_old = (now - created_dt.replace(tzinfo=None)).days
                if 30 <= days_old <= 35 and closes == 0:
                    log.warning(f"PROBATION FAIL: {name} — 0 closes in 30 days — flagging for review")
                    supa("PATCH","sales_reps",{"status":"paused","notes":"30-day probation: 0 closes"},f"?id=eq.{rid}")
            except: pass
    
    # Weekly pushover summary
    if PUSH_API and PUSH_USER:
        top = rep_scores[-1] if rep_scores else None
        msg = (f"Rep Perf Weekly
{n} active reps | avg {avg:.1f} closes
"
               f"Top: {top['rep'].get('first_name','')} ({top['closes']} closes)" if top else "No reps yet")
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":"Rep Performance Weekly","message":msg}).encode()
        req2 = urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data, headers={"Content-Type":"application/json"})
        try: urllib.request.urlopen(req2, timeout=10)
        except: pass

if __name__ == "__main__":
    score_reps()
