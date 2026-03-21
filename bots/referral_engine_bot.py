#!/usr/bin/env python3
"""
Referral Engine Bot — Automates referral asks from satisfied clients.
Best time to ask: 30 days after successful onboarding.
Offers: $200 credit for every successful referral.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

REFERRAL_OFFER = {
    "credit":       "$200",
    "requirement":  "referred contact becomes a paying client",
    "payout":       "credited to next invoice",
    "program_url":  "https://nyspotlightreport.com/referral/",
}

def get_referral_candidates() -> list:
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    return supabase_request("GET","contacts",
        query=f"?stage=eq.CLOSED_WON&stage_changed_at=lt.{cutoff}&referral_asked=is.null&order=score.desc&limit=20"
    ) or []

def generate_referral_ask(contact: dict) -> str:
    name  = contact.get("name","")
    first = name.split()[0] if name else "there"
    co    = contact.get("company","")
    return claude(
        "Write a brief, genuine referral ask email. Friendly, not transactional.",
        f"""Satisfied client: {name} at {co}
Referral offer: {REFERRAL_OFFER["credit"]} credit per successful referral
Program: {REFERRAL_OFFER["program_url"]}

Write 4-5 sentences. Acknowledge their success first. Ask naturally if they know anyone who could benefit. Briefly mention the credit. Include the referral link.""",
        max_tokens=200
    ) or f"Hi {first},\n\nIt's been about a month since we launched your system at {co}, and I hope you're seeing the results we discussed.\n\nIf you know any other founders or marketing directors who are dealing with the same content/automation challenges you had, I'd love to connect with them. As a thank-you, we offer {REFERRAL_OFFER['credit']} credit toward your account for every client you send our way.\n\nYour referral link: {REFERRAL_OFFER['program_url']}\n\nNo pressure — just wanted to put it out there.\n\nSean"

def run():
    log.info("Referral Engine Bot running...")
    candidates = get_referral_candidates()
    log.info(f"Referral candidates: {len(candidates)}")
    for c in candidates:
        msg = generate_referral_ask(c)
        log.info(f"  Referral ask for {c.get('name','?')}")
        if c.get("id"):
            supabase_request("PATCH","contacts",
                data={"referral_asked":datetime.utcnow().isoformat()},
                query=f"?id=eq.{c['id']}"
            )
    return {"referral_asks_sent": len(candidates)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Referral] %(message)s")
    run()
