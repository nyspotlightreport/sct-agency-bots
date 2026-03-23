#!/usr/bin/env python3
"""
Upsell Engine Bot — Identifies upsell and cross-sell opportunities from won clients.
Monitors usage patterns and engagement signals to trigger upsell sequences.
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, ICPS
    from agents.cold_outreach_agent import NYSR_OFFERS
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
    ICPS = {}
    NYSR_OFFERS = {}

import urllib.request, urllib.parse
log = logging.getLogger(__name__)
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

UPGRADE_PATHS = {
    "proflow_starter":  ["proflow_growth", "dfy_essential"],
    "proflow_growth":   ["dfy_agency"],
    "dfy_essential":    ["dfy_agency", "proflow_growth"],
    "lead_gen_starter": ["lead_gen_growth", "proflow_growth"],
}

def find_upsell_opportunities() -> list:
    """Find closed-won clients eligible for upsell."""
    won_clients = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&select=*") or []
    opps = []
    for c in won_clients:
        current_pkg = c.get("icp","proflow_starter")
        upgrades    = UPGRADE_PATHS.get(current_pkg,[])
        if upgrades:
            opps.append({"contact":c,"current_package":current_pkg,"upgrade_options":upgrades})
    return opps

def generate_upsell_email(contact: dict, current_pkg: str, upgrade_pkg: str) -> dict:
    name   = contact.get("name","")
    first  = name.split()[0] if name else "there"
    co     = contact.get("company","your company")
    return claude_json(
        "Write a customer upsell email. Warm, value-focused, brief.",
        f"""Current customer: {name} at {co}
Currently on: {current_pkg}
Upgrading to: {upgrade_pkg}
Relationship: existing paying customer

Write email acknowledging their success with current package, then naturally introduce upgrade.
Return JSON: {{"subject":"...", "body":"...", "key_value_prop":"..."}}""",
        max_tokens=400
    ) or {
        "subject": f"What's working at {co} — and what's next",
        "body": f"Hi {first},\n\nHope things are going well at {co}.\n\nBased on how you've been using {current_pkg}, I wanted to reach out about an upgrade that a few of our clients in your situation have found really valuable.\n\nWorth a quick 10-minute call to walk through it?\n\nBest,\nSean",
        "key_value_prop": "Natural upgrade from proven results",
    }

def run():
    log.info("Upsell Engine scanning for opportunities...")
    opps = find_upsell_opportunities()
    log.info(f"Upsell opportunities: {len(opps)}")
    for opp in opps[:5]:
        email = generate_upsell_email(opp["contact"], opp["current_package"], opp["upgrade_options"][0])
        log.info(f"  Upsell: {opp['contact'].get('name','')} | {opp['current_package']} → {opp['upgrade_options'][0]}")
    if PUSHOVER_API and PUSHOVER_USER and opps:
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Upsell Engine","message":f"💰 {len(opps)} upsell opportunities identified"}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except Exception:  # noqa: bare-except

            pass
    return {"opportunities": len(opps)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Upsell] %(message)s")
    run()
