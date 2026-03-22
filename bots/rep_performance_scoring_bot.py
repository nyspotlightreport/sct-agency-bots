#!/usr/bin/env python3
"""
bots/rep_performance_scoring_bot.py
ENGINE 2 ENHANCEMENT: Rep Performance Scoring
Weekly scoring of all 1099 reps.
Bottom 20% → automated coaching email.
Top 20% → bonus tier unlocked.
30-day probation auto-enforced.
Creates competition with zero Sean involvement.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("rep_perf")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REP PERF] %(message)s")

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

# Commission tier ladder based on monthly volume
COMMISSION_TIERS = [
    (0,    1,  "starter",  30),  # 0-1 closes = 30%
    (2,    5,  "active",   33),  # 2-5 closes = 33%
    (6,   10,  "performer",35),  # 6-10 closes = 35%
    (11, 999,  "elite",    40),  # 11+ closes = 40%
]

def get_commission_tier(monthly_closes):
    for min_c, max_c, name, pct in COMMISSION_TIERS:
        if min_c <= monthly_closes <= max_c:
            return name, pct
    return "starter", 30

def score_all_reps():
    reps = supa("GET","sales_reps","","?status=eq.active&select=*") or []
    if not isinstance(reps, list) or not reps:
        log.info("No active reps yet. Recruiting needed.")
        return

    month_ago = (now - datetime.timedelta(days=30)).isoformat()
    
    scores = []
    for rep in reps:
        rep_id = rep["id"]
        
        # Get 30-day sales
        sales = supa("GET","rep_sales","",
            f"?rep_id=eq.{rep_id}&status=eq.closed&created_at=gte.{month_ago}&select=deal_value") or []
        
        monthly_closes = len(sales) if isinstance(sales,list) else 0
        monthly_rev    = sum(float(s.get("deal_value",0) or 0) for s in (sales if isinstance(sales,list) else []))
        tier_name, comm_pct = get_commission_tier(monthly_closes)
        
        scores.append({
            "rep": rep,
            "monthly_closes": monthly_closes,
            "monthly_rev": monthly_rev,
            "tier": tier_name,
            "comm_pct": comm_pct
        })

        # Update rep record
        supa("PATCH","sales_reps",{
            "total_closes": rep.get("total_closes",0) or 0,
            "total_revenue_gen": float(rep.get("total_revenue_gen",0) or 0) + monthly_rev
        },f"?id=eq.{rep_id}")

    if not scores: return
    
    # Sort by closes
    scores.sort(key=lambda x: -x["monthly_closes"])
    total = len(scores)
    top_20_count    = max(1, total // 5)
    bottom_20_count = max(1, total // 5)

    # Top 20% — bonus tier notification
    for s in scores[:top_20_count]:
        msg = ai(
            f"Write a short rep performance email for {s['rep'].get('first_name','')} who closed {s['monthly_closes']} deals this month.\n"
            f"They're top 20% — they've unlocked the {s['tier'].upper()} commission tier at {s['comm_pct']}%.\n"
            f"Congratulate them. Tell them their new rate. Motivate next month.\n"
            f"Under 60 words. Energetic.",max_tokens=90)
        if msg:
            supa("POST","conversation_log",{"channel":"email","direction":"outbound",
                "body":msg,"intent":"rep_bonus_notification","agent_name":"Rep Performance Bot"})

    # Bottom 20% — coaching email
    for s in scores[-(bottom_20_count):]:
        if s["monthly_closes"] > 0: continue  # If they closed anything, not bottom
        msg = ai(
            f"Write a coaching email for {s['rep'].get('first_name','')} who has 0 closes this month.\n"
            f"Tone: supportive, not punishing. Give 2 specific tactics to try this week.\n"
            f"Remind them of the objection scripts in the rep portal.\n"
            f"Under 60 words.",max_tokens=90)
        if msg:
            supa("POST","conversation_log",{"channel":"email","direction":"outbound",
                "body":msg,"intent":"rep_coaching","agent_name":"Rep Performance Bot"})

    # 30-day probation check
    thirty_days_ago = (now - datetime.timedelta(days=30)).isoformat()
    probation = supa("GET","sales_reps","",
        f"?status=eq.active&created_at=lt.{thirty_days_ago}&select=*") or []
    for rep in (probation if isinstance(probation,list) else []):
        rep_sales = supa("GET","rep_sales","",f"?rep_id=eq.{rep['id']}&select=id&limit=1") or []
        if not rep_sales:
            # Auto-deactivate — no close in 30 days
            supa("PATCH","sales_reps",{"status":"inactive","notes":"Auto-deactivated: 0 closes in 30-day probation"},
                 f"?id=eq.{rep['id']}")
            log.info(f"Deactivated {rep.get('first_name','')} {rep.get('last_name','')} — 0 closes in 30 days")

    log.info(f"Rep scoring: {len(scores)} reps scored | Top: {top_20_count} promoted | Bottom: {bottom_20_count} coached")

if __name__ == "__main__": score_all_reps()
