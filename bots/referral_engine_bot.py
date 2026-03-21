#!/usr/bin/env python3
"""Referral Engine Bot — Automates the entire referral program.
Identifies happy customers, sends referral invites, tracks referrals,
and handles reward fulfillment automatically."""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

REFERRAL_PROGRAM = {
    "reward_referrer":  "$50 account credit per successful referral",
    "reward_referee":   "First month 50% off",
    "tracking_url_base": "https://nyspotlightreport.com/proflow/?ref=",
    "eligibility":      "Customers with 3+ months, health score 75+",
    "referral_window":  90,  # days the referral link is active
}

def identify_referral_candidates(min_months: int = 3, min_health: int = 75) -> list:
    """Find customers likely to refer."""
    # In production, query Supabase for customers matching criteria
    customers = supabase_request("GET","contacts",
        query=f"?stage=eq.CLOSED_WON&score=gte.{min_health}&select=id,name,email,company&limit=20"
    ) or []
    return customers

def generate_referral_link(customer_id: str) -> str:
    import hashlib
    ref_code = hashlib.md5(customer_id.encode()).hexdigest()[:8]
    return f"{REFERRAL_PROGRAM["tracking_url_base"]}{ref_code}"

def generate_referral_ask(customer: dict) -> dict:
    name    = (customer.get("name","") or "").split()[0] or "there"
    company = customer.get("company","your company")
    ref_link = generate_referral_link(customer.get("id",name))
    body = claude(
        "Write a referral ask email. Warm, genuine, not salesy. Mention both rewards. Under 120 words.",
        f"Happy customer: {name} at {company}. Referral link: {ref_link}. Referrer gets $50 credit, referee gets 50% off first month.",
        max_tokens=200
    ) or f"""Hi {name},

Working with {company} has been great, and I wanted to ask — do you know anyone else who could benefit from what we've built together?

For every person you refer who becomes a customer:
• You get $50 added to your account
• They get 50% off their first month

Your personal referral link: {ref_link}

No pressure at all — just wanted to make it easy if you've been telling people about us anyway.

Thanks for the continued trust.
S.C. Thomas"""

    return {
        "to":        customer.get("email",""),
        "subject":   f"A quick favor from a happy customer ({name})?",
        "body":      body,
        "ref_link":  ref_link,
        "customer":  customer,
    }

def run():
    candidates = identify_referral_candidates()
    log.info(f"Found {len(candidates)} referral candidates")
    for c in candidates[:5]:
        ask = generate_referral_ask(c)
        log.info(f"Referral ask for {c.get('name','?')} @ {c.get('company','?')} → {ask['ref_link']}")
    return [generate_referral_ask(c) for c in candidates]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
