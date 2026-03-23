#!/usr/bin/env python3
"""Sales Call Script Bot — Generates custom call scripts for every stage and ICP.
Discovery calls, demo scripts, closing calls, QBR formats."""
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

CALL_FRAMEWORKS = {
    "discovery": {
        "duration": "20-30 min",
        "goal": "Understand pain, qualify BANT, book demo",
        "structure": ["Rapport (2min)","Their world (5min)","Pain excavation (10min)","Qualification (5min)","Next step (3min)"],
    },
    "demo": {
        "duration": "30-45 min",
        "goal": "Show value, handle objections, advance to proposal",
        "structure": ["Recap discovery (3min)","Demo focused on their pain (20min)","Q&A (10min)","Next steps (5min)"],
    },
    "closing": {
        "duration": "20-30 min",
        "goal": "Remove final objections, get signature/payment",
        "structure": ["Summary (5min)","Objection handling (10min)","Decision (5min)","Onboarding preview (5min)"],
    },
    "qbr": {
        "duration": "45-60 min",
        "goal": "Review results, expand account, lock in renewal",
        "structure": ["Results review (15min)","Expansion opportunities (15min)","Product roadmap (10min)","Next 90 days plan (10min)"],
    },
}

def generate_call_script(contact: dict, call_type: str = "discovery") -> str:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","the company")
    title   = contact.get("title","")
    framework = CALL_FRAMEWORKS.get(call_type, CALL_FRAMEWORKS["discovery"])

    script = claude(
        f"""You are Sloane Pierce, VP Sales. Write a complete {call_type} call script for this prospect.
Include: exact opening lines, key questions to ask, what to say at each transition, how to handle pushback.
Structure: {" → ".join(framework["structure"])}
Goal: {framework["goal"]}
Duration: {framework["duration"]}
Be specific and word-for-word where possible. This is a working script.""",
        f"Prospect: {name}, {title} at {company}. ICP: {contact.get('icp','dfy_agency')}. Pain: {contact.get('pain_points','content production and lead gen')}",
        max_tokens=1000
    ) or f"""DISCOVERY CALL SCRIPT — {name} @ {company}

OPEN: "Hi {name}, thanks for taking the time. I want to make sure I use your time well, so I'd like to start by learning about {company}. Is that okay?"

RAPPORT: [Comment on something specific about their company/recent news]

DISCOVERY QUESTIONS:
1. "Tell me about how you currently handle content production at {company}?"
2. "What's the biggest challenge with your current approach?"
3. "If you could wave a magic wand, what would content look like in 6 months?"
4. "What would solving this mean for the business?"
5. "Who else cares about this problem?"
6. "What's your timeline for making a change?"

TRANSITION: "Based on everything you've shared, I think there might be a really strong fit. Let me show you specifically how we solve [their pain]..."

CLOSE: "What would need to be true for you to move forward this week?"
"""
    return script

def run():
    contact = {"name":"Alex Chen","company":"ContentCo","title":"CEO","icp":"proflow_ai"}
    for call_type in ["discovery","demo","closing"]:
        script = generate_call_script(contact, call_type)
        log.info(f"
{'='*50}
{call_type.upper()} CALL SCRIPT
{script[:200]}...
")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
