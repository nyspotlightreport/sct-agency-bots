#!/usr/bin/env python3
"""Upsell/Cross-sell Bot — Identifies expansion revenue opportunities in existing accounts.
Timing-based triggers + AI personalization for natural upgrade conversations."""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

UPSELL_TRIGGERS = {
    "hitting_limits":    {"timing_days":30, "message":"You're maxing out your plan. Time to upgrade."},
    "new_use_case":      {"timing_days":60, "message":"You unlocked a new use case. Here's how to expand it."},
    "competitor_mention": {"timing_days":0, "message":"They just mentioned a competitor — offer the comparison."},
    "growth_signal":     {"timing_days":14, "message":"They just posted a job in your target area."},
    "referral_ready":    {"timing_days":90, "message":"Happy customer. Ask for a referral + offer credit."},
}

UPGRADE_PATHS = {
    "proflow_starter→proflow_growth": {
        "trigger": "hitting_limits",
        "price_delta": 200,
        "value_add": "4× content volume + brand voice + priority support",
        "message_template": "You're producing great content — but you're hitting the 50-article limit. For $200/mo more, Growth gives you 200 articles, custom brand voice, and newsletter automation. Most clients on Growth 2× their organic traffic in 60 days. Want to upgrade?",
    },
    "proflow_growth→proflow_agency": {
        "trigger": "hitting_limits",
        "price_delta": 200,
        "value_add": "Unlimited + white-label + client portal + API",
        "message_template": "You've been consistently hitting 150+ articles. Agency tier gives you unlimited, plus a white-label dashboard to resell to your clients. At $497/mo, most agencies are making that back with one client. Want the details?",
    },
    "any→lead_gen": {
        "trigger": "new_use_case",
        "price_delta": 297,
        "value_add": "50 qualified leads/mo + email sequences + CRM sync",
        "message_template": "You're crushing content — now let's turn readers into customers. Lead Gen Starter adds 50 qualified leads/month from Apollo, automated email sequences, and CRM sync. ${price}/mo. Worth adding alongside your content system?",
    },
    "any→dfy_upgrade": {
        "trigger": "growth_signal",
        "price_delta": 1000,
        "value_add": "We handle everything — setup, management, optimization",
        "message_template": "Looks like you're scaling fast. Our DFY Growth upgrade means we take over the entire system — setup, management, reporting, optimization. $4,997 one-time. Want me to scope it for {company}?",
    },
}

def identify_upsell_opportunities(contact: dict) -> list:
    """Find expansion opportunities for an existing customer."""
    current_product = contact.get("product","proflow_starter")
    opportunities   = []
    for path, data in UPGRADE_PATHS.items():
        from_product = path.split("→")[0]
        if from_product in ["any", current_product]:
            opportunities.append({
                "path": path,
                "trigger": data["trigger"],
                "message": data["message_template"].replace("{company}", contact.get("company","your company")),
                "price_delta": data["price_delta"],
                "value_add": data["value_add"],
            })
    return opportunities

def generate_upsell_email(contact: dict, opportunity: dict) -> dict:
    name = (contact.get("name","") or "").split()[0] or "there"
    body = claude(
        "Write a natural, non-pushy upsell email. 80 words max. Lead with value, end with a question.",
        f"Customer: {name} at {contact.get('company','')}. Opportunity: {opportunity['message']}. Current plan: {contact.get('product','starter')}",
        max_tokens=180
    ) or f"Hi {name},\n\n{opportunity['message']}\n\nWorth a quick chat?\n\nS.C."
    return {"subject": f"Expanding your NYSR setup — {contact.get('company','')}", "body": body, "opportunity": opportunity}

def run():
    customer = {"name":"Sarah Kim","company":"DigitalAgency","product":"proflow_starter","email":"sarah@agency.com"}
    opps = identify_upsell_opportunities(customer)
    for opp in opps:
        email = generate_upsell_email(customer, opp)
        log.info(f"Upsell: {opp['path']} — ${opp['price_delta']}/mo delta")
    return opps

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
