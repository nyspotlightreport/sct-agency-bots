#!/usr/bin/env python3
"""
Win/Loss Analyzer Bot — Revenue intelligence from closed deals.
Analyzes patterns in won/lost deals to improve future outreach and offers.
Generates weekly insights report for Chairman.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None

import urllib.request, urllib.parse
log = logging.getLogger(__name__)

PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

def analyze_won_deals() -> dict:
    won = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&select=*&limit=100") or []
    if not won: return {}
    avg_score    = round(sum(c.get("score",0) for c in won)/len(won))
    top_icps     = {}
    top_titles   = {}
    top_industries = {}
    for c in won:
        icp = c.get("icp","unknown"); top_icps[icp] = top_icps.get(icp,0)+1
        title = (c.get("title") or "unknown").lower().split()[0]; top_titles[title] = top_titles.get(title,0)+1
        ind = c.get("industry","unknown"); top_industries[ind] = top_industries.get(ind,0)+1
    return {
        "total":   len(won),
        "avg_score": avg_score,
        "top_icp": max(top_icps, key=top_icps.get) if top_icps else "unknown",
        "top_title": max(top_titles, key=top_titles.get) if top_titles else "unknown",
        "top_industry": max(top_industries, key=top_industries.get) if top_industries else "unknown",
        "icp_breakdown": top_icps,
        "title_breakdown": top_titles,
    }

def analyze_lost_deals() -> dict:
    lost = supabase_request("GET","contacts",query="?stage=eq.CLOSED_LOST&select=*&limit=100") or []
    if not lost: return {}
    avg_score = round(sum(c.get("score",0) for c in lost)/len(lost))
    reasons = {}
    for c in lost:
        reason = c.get("stage_reason","unknown"); reasons[reason] = reasons.get(reason,0)+1
    return {
        "total":      len(lost),
        "avg_score":  avg_score,
        "top_reason": max(reasons, key=reasons.get) if reasons else "unknown",
        "reasons":    reasons,
    }

def generate_insights_report() -> str:
    won  = analyze_won_deals()
    lost = analyze_lost_deals()
    total_contacts = supabase_request("GET","contacts",query="?select=id") or []

    context = f"""
Won deals: {json.dumps(won, indent=2)}
Lost deals: {json.dumps(lost, indent=2)}
Total contacts in system: {len(total_contacts)}
"""
    return claude(
        "You are a revenue intelligence analyst. Generate a concise weekly win/loss report with 3-5 actionable recommendations.",
        f"Analyze this sales data and provide insights:\n{context}\n\nProvide: win rate, top winning patterns, main loss reasons, and 3 specific actions to improve conversion this week.",
        max_tokens=400
    ) or f"Win/Loss Report\n\nWon: {won.get('total',0)} | Lost: {lost.get('total',0)}\nTop winning ICP: {won.get('top_icp','?')}\nMain loss reason: {lost.get('top_reason','?')}\n\nAction: Focus outreach on {won.get('top_title','founders')} in {won.get('top_industry','your best industry')}."

def run():
    log.info("Win/Loss Analyzer running...")
    report = generate_insights_report()
    log.info(f"Report generated: {len(report)} chars")
    if PUSHOVER_API and PUSHOVER_USER:
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Win/Loss Weekly","message":report[:1000]}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except: pass
    return {"report_generated": True, "length": len(report)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [WinLoss] %(message)s")
    run()
