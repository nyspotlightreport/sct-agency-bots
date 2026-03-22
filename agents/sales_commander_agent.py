#!/usr/bin/env python3
"""
Sales Commander Agent — NYSR Enterprise Sales Department Director
Orchestrates the entire sales operation. Manages pipeline progression,
sequences, proposals, and revenue targets.

Daily operations:
  1. Pull priority contacts needing action
  2. Dispatch outreach bots to contact leads
  3. Generate proposals for qualified leads
  4. Track and forecast revenue
  5. Alert Chairman on high-value opportunities
"""
import os, sys, json, logging, time
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import (
        get_high_priority_contacts, get_pipeline_stats, score_contact,
        supabase_request, advance_stage, analyze_deal, STAGES, ICPS
    )
except Exception as e:
    print(f"Import partial: {e}")
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def get_high_priority_contacts(n): return []
    def get_pipeline_stats(): return {}
    def supabase_request(m,t,**k): return None
    def advance_stage(i,s,r=""): return False
    def analyze_deal(c,s): return {}

log = logging.getLogger(__name__)

import urllib.request, urllib.parse

PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
APOLLO_KEY    = os.environ.get("APOLLO_API_KEY","")

DAILY_TARGETS = {
    "new_leads_pulled":     50,
    "outreach_sent":        20,
    "follow_ups_sent":      10,
    "proposals_generated":   3,
    "deals_advanced":        2,
}

REVENUE_TARGETS = {
    "daily_pipeline_add":  5000,
    "weekly_closed":       2000,
    "monthly_mrr_target": 10000,
}

def notify(msg, title="Sales Commander"):
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except: pass

def get_daily_briefing() -> str:
    """Generate AI daily sales briefing."""
    stats = get_pipeline_stats()
    priority = get_high_priority_contacts(10)

    context = f"""
Sales pipeline stats:
{json.dumps(stats, indent=2)}

Top priority contacts:
{json.dumps([{"name":c.get("name"),"company":c.get("company"),"stage":c.get("stage"),"score":c.get("score")} for c in priority], indent=2)}

Revenue targets:
- Daily pipeline add: ${REVENUE_TARGETS["daily_pipeline_add"]:,}
- Monthly MRR target: ${REVENUE_TARGETS["monthly_mrr_target"]:,}
"""
    return claude(
        "You are a senior sales director. Generate a concise daily briefing (5-7 bullets) covering: "
        "pipeline health, top 3 priority actions for today, revenue projection, and any risks. "
        "Be specific about WHO to contact and WHAT to say.",
        context, max_tokens=500
    ) or "Pipeline review needed. Run CRM sync first."

def auto_advance_warm_leads(contacts: list) -> int:
    """Use AI to determine if any leads should be auto-advanced."""
    advanced = 0
    for contact in contacts:
        stage = contact.get("stage","LEAD")
        if stage == "CLOSED_WON" or stage == "CLOSED_LOST":
            continue

        analysis = analyze_deal(contact, stage)
        prob = analysis.get("probability", 0)

        # Auto-advance from LEAD to PROSPECT if score > 70 and has email
        if stage == "LEAD" and contact.get("score", 0) > 70 and contact.get("email"):
            if advance_stage(contact["id"], "PROSPECT", "Auto-advanced: high score + email available"):
                advanced += 1
                log.info(f"Advanced {contact.get('name','')} → PROSPECT")

    return advanced

def identify_hot_opportunities() -> list:
    """Find contacts that are close to closing."""
    result = supabase_request("GET", "contacts",
        query="?stage=in.(QUALIFIED,PROPOSAL,NEGOTIATION)&score=gte.65&order=score.desc&limit=10"
    )
    opportunities = []
    for contact in (result or []):
        analysis = analyze_deal(contact, contact.get("stage","QUALIFIED"))
        if analysis.get("probability", 0) >= 0.50:
            opportunities.append({
                "contact":     contact.get("name",""),
                "company":     contact.get("company",""),
                "stage":       contact.get("stage",""),
                "score":       contact.get("score",0),
                "probability": analysis.get("probability",0),
                "next_action": analysis.get("next_action",""),
                "deal_size":   analysis.get("deal_size_estimate", ICPS.get("dfy_agency",{}).get("deal_size",1000)),
            })
    return sorted(opportunities, key=lambda x: x["deal_size"]*x["probability"], reverse=True)

def generate_daily_sequence_queue() -> list:
    """Build the outreach queue for today."""
    # Leads needing first contact
    leads_to_contact = supabase_request("GET", "contacts",
        query="?stage=eq.LEAD&score=gte.50&last_contacted=is.null&order=score.desc&limit=20"
    )
    # Leads needing follow-up (not contacted in 3+ days)
    cutoff = (datetime.utcnow() - timedelta(days=3)).isoformat()
    follow_ups = supabase_request("GET", "contacts",
        query=f"?stage=in.(PROSPECT,QUALIFIED)&last_contacted=lt.{cutoff}&order=score.desc&limit=10"
    )

    queue = []
    for c in (leads_to_contact or []):
        queue.append({"type":"first_contact", "contact":c, "priority": c.get("score",0)})
    for c in (follow_ups or []):
        queue.append({"type":"follow_up",    "contact":c, "priority": c.get("score",0)+20})

    return sorted(queue, key=lambda x: x["priority"], reverse=True)

def run():
    log.info("Sales Commander starting daily operations...")
    start = datetime.utcnow()

    # 1. Daily briefing
    briefing = get_daily_briefing()
    log.info(f"Briefing generated")

    # 2. Auto-advance warm leads
    priority = get_high_priority_contacts(20)
    advanced = auto_advance_warm_leads(priority)
    log.info(f"Auto-advanced: {advanced} leads")

    # 3. Identify hot opportunities
    hot = identify_hot_opportunities()
    log.info(f"Hot opportunities: {len(hot)}")

    # 4. Build outreach queue
    queue = generate_daily_sequence_queue()
    log.info(f"Outreach queue: {len(queue)} items")

    # 5. Get pipeline stats for reporting
    stats = get_pipeline_stats()
    total_pipeline = sum(s.get("total_pipeline_value",0) for s in stats.values())

    # 6. Alert Chairman with briefing
    if hot:
        hot_summary = "\n".join([f"  • {h['company']} ({h['stage']}) — ${h['deal_size']:,} at {int(h['probability']*100)}%" for h in hot[:3]])
        notify(
            f"🔥 {len(hot)} hot deals needing action:\n{hot_summary}\n\n{briefing[:400]}",
            "Sales: Hot Deals"
        )
    else:
        notify(f"📈 Sales Daily\n{briefing[:600]}", "Sales Commander")

    elapsed = (datetime.utcnow() - start).seconds
    log.info(f"Sales Commander complete in {elapsed}s")

    return {
        "leads_advanced":   advanced,
        "hot_deals":        len(hot),
        "outreach_queue":   len(queue),
        "pipeline_value":   total_pipeline,
        "daily_briefing":   briefing,
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [SalesCmd] %(message)s")
    run()
