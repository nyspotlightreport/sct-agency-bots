#!/usr/bin/env python3
"""
Sloane Pierce ΓÇö VP of Sales & Revenue
NYSR Internal Agency ΓÇö Sales Department Director

Sloane is a battle-tested enterprise sales director. Former VP Sales at 
two SaaS unicorns, 15 years closing 6-7 figure deals. She runs a tight ship: 
data-driven, high velocity, zero tolerance for slow pipelines.

Responsibilities:
  - Daily pipeline review and coaching
  - Quota setting and territory management
  - Sales playbook creation and enforcement
  - Win/loss analysis
  - Revenue forecasting (weekly/monthly/quarterly)
  - Hiring and onboarding sales talent
  - Compensation plan design
  - Competitive positioning and battle cards
  - Key account strategy

Under Sloane's leadership, NYSR Sales converts at 3├ù industry average
because every step is systematized, every message is personalized,
and every deal has a clear next action.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import get_pipeline_stats, get_high_priority_contacts, score_contact, ICPS, STAGES
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def get_pipeline_stats(): return {}
    def get_high_priority_contacts(n): return []

log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.parse

def notify(msg, title="Sloane Pierce ΓÇö Sales"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title[:50],"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except: pass

# ΓöÇΓöÇ QUOTA & TARGETS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
QUARTERLY_TARGETS = {
    "new_mrr":         5000,   # $5k new MRR per quarter
    "one_time_revenue": 20000, # $20k one-time deals per quarter
    "deals_closed":    15,     # 15 deals per quarter
    "pipeline_coverage": 3,    # 3├ù quota in pipeline
    "avg_deal_size":   1500,   # $1,500 avg
    "close_rate":      0.25,   # 25% of qualified leads close
}

# ΓöÇΓöÇ SALES PLAYBOOK ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
PLAYBOOK = {
    "prospecting": {
        "daily_outreach_target": 20,
        "channels": ["cold_email", "linkedin", "twitter_dm", "referral"],
        "best_times": ["Tue 10am", "Wed 2pm", "Thu 9am"],
        "subject_lines": [
            "Quick question about {company}'s content",
            "{first_name} ΓÇö saw you're hiring for {role}",
            "{mutual_connection} suggested I reach out",
            "How {competitor} is eating your lunch (and how to fight back)",
        ]
    },
    "discovery": {
        "key_questions": [
            "What's your biggest content production bottleneck right now?",
            "How many pieces of content does your team produce per week?",
            "What would it mean for your business if you could 10├ù that output?",
            "Who else is involved in decisions like this?",
            "What's your timeline for solving this?",
            "Have you tried other tools? What happened?",
        ],
        "pain_triggers": ["content backlog", "team too small", "falling behind competitors", "SEO rankings dropping"],
    },
    "proposal": {
        "structure": ["Executive Summary", "Their Specific Pain", "Our Solution", "ROI Calculation", "Pricing", "Next Steps", "Social Proof"],
        "urgency_levers": ["limited onboarding slots", "price increase Q2", "competitor already using us"],
        "payment_options": ["monthly", "annual (2 months free)", "quarterly"],
    },
    "objections": {
        "too expensive": "Let me show you the ROI calculation. At {price}/mo, you break even if we save your team just {hours} hours/month. What's an hour of your team's time worth?",
        "need to think": "Of course. What specific questions can I answer right now to help you decide? I'd hate for you to lose the onboarding slot while you're thinking.",
        "not right now": "I understand. When would be right? I ask because we have {n} companies on the waitlist and I want to hold your spot.",
        "using competitor": "Interesting ΓÇö what do you like about them? Most of our clients switched from {competitor} because {differentiator}.",
        "need approval": "Makes sense. Would it help if I put together an executive summary you could share with them? I've made it easy to forward.",
        "too busy": "That's exactly why this matters ΓÇö if you're too busy now, imagine how much faster you'd move with our system handling the content.",
    },
    "closing": {
        "trial_close": "Based on what we've discussed, does this seem like it could solve your {pain}?",
        "summary_close": "So we're solving {pain}, delivering {outcome}, at {price}/mo. Ready to get started?",
        "next_step_close": "The next step is simple ΓÇö I'll send over the agreement and onboarding link. You can be live by {date}. Does that work?",
        "urgency_close": "I'm holding your onboarding slot through {date}. After that, it goes to the next company on the waitlist. Should I lock it in?",
    }
}

# ΓöÇΓöÇ REVENUE FORECAST ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def generate_revenue_forecast(weeks: int = 12) -> Dict:
    """Build a bottoms-up revenue forecast based on current pipeline."""
    stats   = get_pipeline_stats()
    probs   = {"LEAD":0.05,"PROSPECT":0.15,"QUALIFIED":0.35,"PROPOSAL":0.60,"NEGOTIATION":0.85}
    avg_deal = 1500

    weekly_forecast = []
    cumulative = 0
    for w in range(1, weeks+1):
        weighted = sum(
            stats.get(stage,{}).get("count",0) * prob * avg_deal / weeks
            for stage, prob in probs.items()
        )
        cumulative += weighted
        weekly_forecast.append({
            "week": w,
            "date": (datetime.utcnow() + timedelta(weeks=w)).strftime("%Y-%m-%d"),
            "expected_revenue": round(weighted),
            "cumulative": round(cumulative),
        })

    return {
        "forecast": weekly_forecast,
        "total_12_week": round(cumulative),
        "monthly_run_rate": round(cumulative/3),
        "quota_attainment": round(cumulative / (QUARTERLY_TARGETS["new_mrr"] * 3 + QUARTERLY_TARGETS["one_time_revenue"]) * 100),
        "generated_at": datetime.utcnow().isoformat(),
    }

# ΓöÇΓöÇ WIN/LOSS ANALYSIS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def analyze_win_loss(deal: Dict) -> Dict:
    """AI-powered win/loss analysis to improve future performance."""
    return claude_json(
        """You are Sloane Pierce, VP of Sales. Analyze this deal outcome and extract lessons.
Return JSON: {
  "outcome": "won|lost",
  "primary_reason": "string",
  "key_factors": ["list"],
  "what_worked": ["list"],
  "what_to_improve": ["list"],
  "recommended_playbook_updates": ["list"],
  "similar_deal_guidance": "string"
}""",
        f"Deal: {json.dumps(deal, indent=2)[:2000]}",
        max_tokens=600
    ) or {}

# ΓöÇΓöÇ COACHING NOTES ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def generate_coaching_note(contact: Dict, stage: str) -> str:
    """Generate specific coaching note for a deal."""
    return claude(
        f"""You are Sloane Pierce, VP Sales. Write a 3-bullet coaching note for this deal.
Be specific. No fluff. Focus on the single biggest risk and the exact next action.""",
        f"Contact: {contact.get('name')} | {contact.get('title')} at {contact.get('company')} | Stage: {stage} | Score: {contact.get('score',{}).get('total',0)}/100",
        max_tokens=200
    ) or "ΓÇó Pull Apollo data on this company
ΓÇó Send personalized value prop
ΓÇó Follow up in 3 days"

# ΓöÇΓöÇ DAILY SALES BRIEFING ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def run_daily_briefing():
    """Sloane's daily sales briefing ΓÇö sent to Chairman every morning."""
    log.info("Sloane Pierce ΓÇö running daily sales briefing")

    stats    = get_pipeline_stats()
    forecast = generate_revenue_forecast(12)
    priority = get_high_priority_contacts(5)

    # Build pipeline summary
    active_stages = {k:v for k,v in stats.items() if v.get("count",0) > 0 and k not in ["CLOSED_WON","CLOSED_LOST"]}
    stage_str = " | ".join([f"{k}: {v['count']}" for k,v in active_stages.items()])

    # Build coaching notes for priority deals
    coaching = []
    for c in priority[:3]:
        note = generate_coaching_note(c, c.get("stage","LEAD"))
        coaching.append(f"ΓÇó {c.get('name','?')} @ {c.get('company','?')} ({c.get('stage','?')}): {note[:100]}")

    total_pipeline = sum(v.get("count",0) for v in stats.values())
    won_count = stats.get("CLOSED_WON",{}).get("count",0)

    briefing = f"""≡ƒôè SALES BRIEFING ΓÇö {datetime.utcnow().strftime('%a %b %d')}

PIPELINE: {stage_str}
Total: {total_pipeline} contacts | Won: {won_count}
12-week forecast: ${forecast['total_12_week']:,}
Quota attainment: {forecast['quota_attainment']}%

TOP DEALS:
{chr(10).join(coaching) if coaching else "ΓÇó No priority deals ΓÇö time to load the pipeline!"}

TODAY'S PRIORITY:
ΓåÆ {'Focus on NEGOTIATION deals ΓÇö highest close probability' if stats.get('NEGOTIATION',{}).get('count',0) > 0 else 'Move 3 prospects to QUALIFIED today'}"""

    log.info(briefing)
    notify(briefing, "Sloane ΓÇö Daily Sales Brief")
    return briefing

def run():
    return run_daily_briefing()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Sloane] %(message)s")
    run()
