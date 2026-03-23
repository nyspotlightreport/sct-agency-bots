#!/usr/bin/env python3
"""Win-Back Bot — Re-engages lost deals and churned customers.
Timing-based re-engagement sequences with fresh angles."""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

WIN_BACK_TIMING = {
    "lost_deal_30d":   "Re-engage at 30 days with new angle or offer",
    "lost_deal_90d":   "Re-engage at 90 days — circumstances may have changed",
    "churned_60d":     "Win-back at 60 days — offer to return with incentive",
    "churned_180d":    "Long-term win-back — show what's new and improved",
    "ghosted_prospect": "Reactivate contacts who went dark",
}

WIN_BACK_ANGLES = [
    "new_feature",     # We shipped something that solves their specific objection
    "case_study",      # New social proof from a similar company
    "pricing_change",  # Limited time offer or pricing adjustment
    "circumstance_check", # "Things may have changed since we last spoke"
    "competitor_news", # Competitor had a bad day/raised prices/got acquired
    "referral",        # Mutual connection suggested I reach back out
]

def identify_winback_candidates() -> list:
    """Find lost deals and churned customers ripe for re-engagement."""
    cutoff_30 = (datetime.utcnow() - timedelta(days=30)).isoformat()
    cutoff_90 = (datetime.utcnow() - timedelta(days=90)).isoformat()

    lost = supabase_request("GET","contacts",
        query=f"?stage=eq.CLOSED_LOST&updated_at=lt.{cutoff_30}&updated_at=gt.{cutoff_90}&limit=20"
    ) or []
    return lost

def generate_winback_email(contact: dict, angle: str = "circumstance_check") -> dict:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","your company")
    reason_lost = contact.get("stage_reason","the timing wasn't right")

    angle_context = {
        "new_feature": "We just shipped [feature] that directly addresses the concern you had",
        "case_study":  "A company just like yours achieved [result] — thought you'd want to see it",
        "pricing_change": "We restructured pricing — now more accessible for companies your size",
        "circumstance_check": "Things change — wanted to check if this is still relevant",
        "competitor_news": "One of your competitors just went all-in on AI content — wanted to loop back",
        "referral": "A mutual contact suggested I reach out again",
    }.get(angle, "circumstances may have changed")

    body = claude(
        "Write a win-back email. Acknowledge previous conversation. New angle. Humble. Under 80 words.",
        f"Re-engaging {name} at {company}. Last contact reason/status: {reason_lost}. New angle: {angle_context}",
        max_tokens=160
    ) or f"""Hi {name},

Hope {company} has been doing well.

We spoke a while back and the timing wasn't quite right. Things have changed on our end — {angle_context}.

Worth a quick catch-up?

S.C. Thomas"""

    return {
        "to":      contact.get("email",""),
        "subject": f"{company} — things have changed",
        "body":    body,
        "angle":   angle,
        "contact": contact,
    }

def run():
    candidates = identify_winback_candidates()
    log.info(f"Win-back candidates: {len(candidates)}")
    for c in candidates[:5]:
        email = generate_winback_email(c, "circumstance_check")
        log.info(f"Win-back: {c.get('name','?')} @ {c.get('company','?')} — {email['subject']}")
    return [generate_winback_email(c) for c in candidates]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
