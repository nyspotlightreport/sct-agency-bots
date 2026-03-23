#!/usr/bin/env python3
"""
Follow-Up Bot — Automated multi-touch follow-up engine
Never lets a hot lead go cold. Monitors sequence progress and sends
AI-written follow-ups at the right time via Apollo.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
    from agents.cold_outreach_agent import write_cold_email, select_offer
except Exception as e:
    print(f"Import partial: {e}")
    def supabase_request(m,t,**k): return None
    def write_cold_email(c,o,t,a): return {}
    def select_offer(c): return {}

import urllib.request, urllib.parse

log = logging.getLogger(__name__)
APOLLO_KEY    = os.environ.get("APOLLO_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

FOLLOW_UP_RULES = {
    "LEAD":        {"days_before_follow_up": 2,  "max_touches": 7, "escalate_to": "PROSPECT"},
    "PROSPECT":    {"days_before_follow_up": 3,  "max_touches": 5, "escalate_to": "QUALIFIED"},
    "QUALIFIED":   {"days_before_follow_up": 2,  "max_touches": 3, "escalate_to": None},
    "PROPOSAL":    {"days_before_follow_up": 1,  "max_touches": 4, "escalate_to": None},
    "NEGOTIATION": {"days_before_follow_up": 1,  "max_touches": 5, "escalate_to": None},
}

def get_contacts_needing_follow_up() -> list:
    """Find contacts that need a follow-up today."""
    results = []
    for stage, rules in FOLLOW_UP_RULES.items():
        cutoff = (datetime.utcnow() - timedelta(days=rules["days_before_follow_up"])).isoformat()
        contacts = supabase_request("GET", "contacts",
            query=f"?stage=eq.{stage}&last_contacted=lt.{cutoff}&score=gte.40&order=score.desc&limit=20"
        )
        for c in (contacts or []):
            results.append({"contact": c, "rules": rules, "stage": stage})
    return sorted(results, key=lambda x: x["contact"].get("score",0), reverse=True)

def log_activity(contact_id: str, activity_type: str, subject: str, body: str):
    """Log an outreach activity to Supabase."""
    supabase_request("POST", "activities", {
        "contact_id": contact_id,
        "type":       activity_type,
        "subject":    subject,
        "body":       body[:2000],
        "created_at": datetime.utcnow().isoformat(),
    })
    # Update last_contacted timestamp
    supabase_request("PATCH", "contacts",
        data={"last_contacted": datetime.utcnow().isoformat()},
        query=f"?id=eq.{contact_id}"
    )

def run():
    log.info("Follow-Up Bot running...")
    needs_follow_up = get_contacts_needing_follow_up()
    log.info(f"Contacts needing follow-up: {len(needs_follow_up)}")

    sent = 0
    for item in needs_follow_up[:20]:
        contact = item["contact"]
        stage   = item["stage"]
        offer   = select_offer(contact)
        touch   = contact.get("touch_count", 1) + 1
        angle   = "value_add" if touch == 2 else "case_study" if touch == 3 else "breakup_almost" if touch >= 5 else "follow_up"

        email = write_cold_email(contact, offer, touch, angle)
        if contact.get("id"):
            log_activity(
                contact["id"], "email_sent",
                email.get("subject","Follow-up"),
                email.get("body","")
            )
            # Increment touch count
            supabase_request("PATCH", "contacts",
                data={"touch_count": touch},
                query=f"?id=eq.{contact['id']}"
            )
        sent += 1
        log.info(f"  Follow-up #{touch} → {contact.get('name','')} ({stage}): {email.get('subject','')}")

    log.info(f"Follow-ups queued: {sent}")

    if sent > 0:
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,
                "title":"Follow-Up Bot","message":f"📧 {sent} follow-ups queued for today"}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
        except Exception:  # noqa: bare-except

            pass
    return {"follow_ups_sent": sent, "contacts_checked": len(needs_follow_up)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [FollowUp] %(message)s")
    run()
