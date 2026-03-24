#!/usr/bin/env python3
"""Cold Email Personalization Bot — Generates hyper-personalized cold emails at scale.
Each email is unique, researched, and designed to get a reply, not a delete."""
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

EMAIL_FRAMEWORKS = {
    "AIDA": "Attention → Interest → Desire → Action",
    "PAS":  "Problem → Agitate → Solution",
    "PPP":  "Praise → Picture → Push",
    "QVC":  "Question → Value → Call-to-action",
}

def personalize_email(contact: dict, framework: str = "PAS", sequence_step: int = 1) -> dict:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","your company")
    title   = contact.get("title","")
    industry = contact.get("industry","")

    step_context = {
        1: "first cold outreach — no prior contact",
        2: "first follow-up — 3 days after email 1, no reply",
        3: "second follow-up — value-add, share resource",
        4: "breakup email — last touch, create urgency",
        5: "re-engagement — 30 days later",
    }.get(sequence_step, "follow-up")

    subject, body = "", ""

    if sequence_step == 1:
        subject = claude("Write a cold email subject line. 6-8 words. Curiosity-based. No spam words. Just the subject, nothing else.",
            f"Prospect: {name}, {title} at {company} ({industry})", max_tokens=30) or f"Quick question about {company}"
        body = claude(
            f"""Write a {framework} cold email. Under 100 words. First sentence must be about them, not us.
End with ONE easy yes/no question. No generic openers. No "I hope this email finds you well."
Sign as: S.C. Thomas, NY Spotlight Report""",
            f"To: {name}, {title} at {company}. Their industry: {industry}. Selling: AI content automation starting at $97/mo.",
            max_tokens=200
        ) or f"Hi {name},\n\nI noticed {company} is growing fast — content production usually becomes a bottleneck around your stage.\n\nWe help {industry} companies automate content creation and lead gen with AI bots. Most clients 10× output in 30 days.\n\nWorth a 15-min call this week?\n\nS.C. Thomas\nNY Spotlight Report"

    elif sequence_step == 2:
        subject = f"Re: {company} — still relevant?"
        body = claude("Write a 3-sentence follow-up email. Acknowledge no reply. Add one new insight. Ask if timing is off.",
            f"Following up with {name} at {company}", max_tokens=120
        ) or f"Hi {name},\n\nWanted to follow up — I know things get busy.\n\nI put together a quick analysis showing how 3 companies in {industry} cut content costs by 60% with our system.\n\nIs this even on your radar right now?\n\nS.C."

    elif sequence_step == 3:
        subject = f"Something useful for {company}"
        body = f"Hi {name},\n\nSharing this because it's directly relevant to {company}:\n\n→ [Quick case study: How a {industry} company went from 5 to 50 articles/week in 30 days]\n\nNo ask. Just thought it might be useful.\n\nS.C. Thomas"

    elif sequence_step == 4:
        subject = f"Closing the loop — {company}"
        body = claude("Write a 2-sentence breakup email. Graceful. Leave door open. Create mild FOMO.",
            f"Last email to {name} at {company}", max_tokens=80
        ) or f"Hi {name},\n\nI won't keep filling your inbox — if AI content automation isn't a priority at {company} right now, totally understood.\n\nIf things change, you know where to find us.\n\nS.C."

    return {
        "to":      contact.get("email",""),
        "name":    name,
        "company": company,
        "subject": subject,
        "body":    body,
        "sequence_step": sequence_step,
        "framework":     framework,
    }

def generate_full_sequence(contact: dict) -> list:
    return [personalize_email(contact, step=i) for i in range(1,6)]

def run():
    test = {"name":"Alex Chen","company":"ContentCo","title":"CEO","industry":"marketing","email":"alex@contentco.com"}
    seq = [personalize_email(test, sequence_step=i) for i in [1,2,3,4]]
    for e in seq:
        log.info(f"Step {e['sequence_step']} — Subject: {e['subject']}")
    return seq

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
