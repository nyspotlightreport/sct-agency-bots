#!/usr/bin/env python3
"""
bots/rep_performance_scorer_bot.py
ENGINE 2: 1099 Rep Performance Scoring + Auto-Coaching.
Runs weekly. Ranks all reps. Bottom 20% get coaching email.
Top 20% get bonus tier unlock email. Creates competition + accountability.
Zero Sean involvement.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("rep_scorer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REP SCORER] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
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

def score_reps():
    """Weekly rep performance scoring + tiering."""
    week_of = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
    week_str = week_of.isoformat()
    
    reps = supa("GET","sales_reps","","?status=eq.active&select=*") or []
    if not isinstance(reps, list) or not reps:
        log.info("No active reps yet — check back after recruiting")
        return []
    
    # Get this week's sales per rep
    week_start = week_of.isoformat()
    week_end   = (week_of + datetime.timedelta(days=7)).isoformat()
    
    scored = []
    for rep in reps:
        rep_id = rep.get("id")
        sales  = supa("GET","rep_sales","",
            f"?rep_id=eq.{rep_id}&status=eq.closed&closed_at=gte.{week_start}T00:00:00&closed_at=lt.{week_end}T00:00:00&select=*") or []
        
        closes = len(sales if isinstance(sales,list) else [])
        revenue = sum(float(s.get("deal_value",0) or 0) for s in (sales if isinstance(sales,list) else []))
        commission = sum(float(s.get("commission_earned",0) or 0) for s in (sales if isinstance(sales,list) else []))
        
        # Upsert weekly performance
        supa("POST","rep_performance_weekly",{
            "week_of":week_str,"rep_id":rep_id,
            "closes":closes,"revenue_gen":revenue,"commission_earned":commission
        })
        
        scored.append({"rep":rep, "closes":closes, "revenue":revenue, "commission":commission})
    
    # Rank and tier
    scored.sort(key=lambda x: x["closes"], reverse=True)
    n = len(scored)
    
    for i, item in enumerate(scored):
        pct = (i+1) / n
        tier = "top20" if pct <= 0.2 else ("bottom20" if pct >= 0.8 else "mid60")
        rank = i + 1
        
        supa("PATCH","rep_performance_weekly",{
            "rank":rank,"tier":tier
        },f"?week_of=eq.{week_str}&rep_id=eq.{item['rep']['id']}")
        
        item["tier"] = tier
        item["rank"] = rank
    
    return scored

def send_performance_emails(scored):
    """Auto-coaching for bottom 20%. Bonus unlock for top 20%."""
    if not ANTHROPIC: return
    
    for item in scored:
        rep   = item["rep"]
        tier  = item.get("tier","mid60")
        name  = f"{rep.get('first_name','')} {rep.get('last_name','')}"
        email = rep.get("email","")
        closes = item["closes"]
        
        week_of = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
        
        if tier == "bottom20":
            msg = f"""Write a coaching email for {name}, an underperforming sales rep.
This week: {closes} closes.
Tone: supportive and encouraging, not harsh.
Include: 1 specific script improvement tip, 1 objection handling reminder, encouragement to keep going.
Under 150 words. First-person from NYSR."""
        elif tier == "top20":
            msg = f"""Write a reward email for {name}, a top-performing rep.
This week: {closes} closes. Rank #{item.get('rank',1)}.
Announce: They are now eligible for the 35% commission tier upgrade (from standard 30%).
Tone: celebratory and motivating.
Under 100 words. First-person from NYSR."""
        else:
            continue  # mid60 gets no email
        
        email_body = __import__("urllib.request", fromlist=["urlopen"])
        # Use the ANTHROPIC to generate
        d = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":200,
            "messages":[{"role":"user","content":msg}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=d,
            headers={"Content-Type":"application/json","x-api-key":os.environ.get("ANTHROPIC_API_KEY",""),
                     "anthropic-version":"2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read())["content"][0]["text"]
        except: continue
        
        supa("POST","conversation_log",{"contact_id":None,"channel":"email",
            "direction":"outbound","body":body,
            "intent":"rep_coaching" if tier=="bottom20" else "rep_bonus_unlock",
            "agent_name":"Rep Performance Scorer"})
        
        # Mark as sent
        week_str = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).isoformat()
        flag = "coaching_sent" if tier=="bottom20" else "bonus_sent"
        supa("PATCH","rep_performance_weekly",{flag:True},
             f"?week_of=eq.{week_str}&rep_id=eq.{rep.get('id','')}")

def run():
    log.info("ENGINE 2: Rep Performance Scorer")
    scored = score_reps()
    if scored:
        send_performance_emails(scored)
        log.info(f"Scored {len(scored)} reps. Bottom 20% coached. Top 20% rewarded.")
    else:
        log.info("No active reps yet — recruiting pipeline is the priority")
    supa("PATCH","closing_engines",{"last_run":now.isoformat()},"?engine_key=eq.reps_1099")

if __name__ == "__main__": run()
