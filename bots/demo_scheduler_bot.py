#!/usr/bin/env python3
"""Demo Scheduler Bot — Automates demo booking, confirmation, and prep.
Connects to Calendly, sends prep materials, and briefs the sales rep."""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

CALENDLY_LINK = "https://calendly.com/nyspotlightreport"
DEMO_PREP_QUESTIONS = [
    "What's your primary goal for this call?",
    "What tools are you currently using for content/marketing?",
    "How many pieces of content do you produce per week currently?",
    "What's your team size?",
    "What would a successful outcome look like in 90 days?",
]

def generate_booking_email(contact: dict) -> dict:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","your company")
    body = f"""Hi {name},

Great speaking with you! Based on what you've shared about {company}, I think a demo would be really valuable.

Here's my calendar — pick a 20-minute slot that works for you:
→ {CALENDLY_LINK}/demo-nysr

To make our time as valuable as possible, I'd love if you could answer these quick questions beforehand:

1. {DEMO_PREP_QUESTIONS[0]}
2. {DEMO_PREP_QUESTIONS[1]}
3. {DEMO_PREP_QUESTIONS[2]}

You can just reply here — takes 2 minutes.

Looking forward to it,
S.C. Thomas
NY Spotlight Report"""

    return {
        "to":      contact.get("email",""),
        "subject": f"Demo booking — {company} × NYSR",
        "body":    body,
        "calendly_link": CALENDLY_LINK,
    }

def generate_reminder(contact: dict, hours_before: int = 24) -> dict:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","")
    body = f"""Hi {name},

Just a reminder about our demo call {"tomorrow" if hours_before == 24 else "in a few hours"} — looking forward to showing you what we've built.

A few things to expect:
• 20 minutes, no fluff
• I'll show you specifically how this applies to {company}
• You'll leave with a clear picture of ROI and next steps

See you soon,
S.C."""

    return {
        "to":      contact.get("email",""),
        "subject": f"{'Tomorrow' if hours_before == 24 else 'Today'}: NYSR demo — {company}",
        "body":    body,
    }

def generate_demo_brief(contact: dict, prep_answers: dict = None) -> str:
    name    = contact.get("name","?")
    company = contact.get("company","?")
    brief = f"""DEMO BRIEF — {name} @ {company}
{'='*40}
Score:    {contact.get('score',{}).get('total',0)}/100 ({contact.get('score',{}).get('grade','?')})
ICP:      {contact.get('icp','?')}
Title:    {contact.get('title','?')}
Industry: {contact.get('industry','?')}

KEY FOCUS AREAS:
• Lead with their primary pain point
• Show ROI calculator specific to their company size
• Demo feature most relevant to their ICP

PREP ANSWERS: {json.dumps(prep_answers or {}, indent=2)}

OBJECTIONS TO PREP FOR:
• Price (have ROI calc ready)
• "We're using [tool]" (have competitor card ready)
• Timeline (have onboarding timeline ready)

TARGET OUTCOME: Move to PROPOSAL stage
NEXT ACTION: Send proposal within 24h of demo
"""
    return brief

def run():
    contact = {"name":"Alex Chen","company":"ContentCo","title":"CEO","score":{"total":82,"grade":"A"},"icp":"proflow_ai"}
    booking = generate_booking_email(contact)
    reminder = generate_reminder(contact, 24)
    brief = generate_demo_brief(contact)
    log.info(f"Demo booking email ready for {contact['name']} @ {contact['company']}")
    log.info(f"Brief:
{brief}")
    return {"booking": booking, "reminder": reminder, "brief": brief}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
