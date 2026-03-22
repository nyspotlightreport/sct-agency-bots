#!/usr/bin/env python3
"""Webinar Sales Bot — Automates webinar funnels as a sales channel.
Creates webinar outlines, manages registrations, follow-up sequences."""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

WEBINAR_TOPICS = [
    {"title":"How to 10× Content Output Without Hiring", "target":"proflow_ai", "duration":45},
    {"title":"AI Lead Generation: From 0 to 200 Leads/Month", "target":"lead_gen", "duration":45},
    {"title":"Done-For-You AI Setup: Live Demo + Q&A", "target":"dfy_agency", "duration":60},
    {"title":"The $100K Agency Stack: Tools We Use Internally", "target":"all", "duration":60},
]

def generate_webinar_funnel(topic: dict) -> dict:
    title    = topic["title"]
    target   = topic["target"]
    date     = (datetime.utcnow() + timedelta(days=7)).strftime("%A, %B %d at 2:00 PM EST")

    # Registration page copy
    reg_headline = claude("Write a webinar registration page headline. Power word + specific benefit. Under 12 words.",
        f"Webinar: {title}", max_tokens=30) or title
    reg_body = claude("Write 3-bullet registration page copy. Specific. Results-focused. Under 30 words each bullet.",
        f"Webinar: {title}. Target: {target} audience.", max_tokens=150) or f"• Learn exactly how to {title.lower()}
• Real examples and live demo
• Q&A with implementation expert"

    # Reminder sequence
    reminder_24h = f"Tomorrow at 2pm EST: {title} — here's what we'll cover..."
    reminder_1h  = f"Starting in 1 hour: {title}. Join link below."
    reminder_now = f"We're LIVE right now! Join: [ZOOM_LINK]"

    # Follow-up sequence
    followup_1 = claude("Write webinar follow-up email for attendees. Recap value, CTA to book call. 80 words.",
        f"Webinar: {title}", max_tokens=150) or f"Thanks for joining {title}! Here's the recording plus my direct calendar link to take next steps..."
    followup_no_show = f"Sorry I missed you on {title}! Recording here: [LINK]. Worth watching — especially the ROI demo at minute 22."

    return {
        "title":       title,
        "date":        date,
        "target":      target,
        "reg_headline": reg_headline,
        "reg_body":    reg_body,
        "reminders":   {"24h": reminder_24h, "1h": reminder_1h, "live": reminder_now},
        "followups":   {"attended": followup_1, "no_show": followup_no_show},
        "expected_registrations": 50,
        "expected_attendees":     25,
        "expected_demos_booked":  5,
    }

def run():
    for topic in WEBINAR_TOPICS[:2]:
        funnel = generate_webinar_funnel(topic)
        log.info(f"Webinar funnel: {funnel['title']} | {funnel['date']} | Expected demos: {funnel['expected_demos_booked']}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
