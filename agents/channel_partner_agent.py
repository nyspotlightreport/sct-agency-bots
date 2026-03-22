#!/usr/bin/env python3
# Channel Partner Agent - Partner/reseller program management and recruitment.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

PARTNER_TIERS = {
    "referral": {"commission":0.20,"requirements":"None","benefits":"20% revenue share per referral"},
    "reseller": {"commission":0.30,"requirements":"5+ clients/quarter","benefits":"30% margin + marketing support"},
    "agency":   {"commission":0.40,"requirements":"10+ clients/quarter","benefits":"40% margin + white-label + priority support"},
}

PARTNER_ICPS = [
    "Marketing agencies (10-50 person)",
    "Digital agencies",
    "Freelance consultants serving SMBs",
    "Business coaches with email lists",
    "SaaS tools with complementary audience",
]

def generate_partner_pitch(partner_type, contact):
    tier = PARTNER_TIERS.get(partner_type, PARTNER_TIERS["referral"])
    name = (contact.get("name","") or "").split()[0] or "there"
    return claude(
        f"Write a partnership proposal email. Emphasize passive income and client value. Under 150 words.",
        f"To: {name} at {contact.get('company','')}. Partner tier: {partner_type}. Commission: {tier['commission']*100}%.",
        max_tokens=250
    ) or f"Hi {name}, I wanted to propose a partnership that could generate significant passive income for {contact.get('company','')}. As a {partner_type} partner, you earn {tier['commission']*100}% commission on every client you refer. Interested?"

def calculate_partner_earnings(clients_per_month, avg_deal_value, tier="reseller"):
    commission = PARTNER_TIERS[tier]["commission"]
    monthly = clients_per_month * avg_deal_value * commission
    return {
        "monthly_passive": round(monthly),
        "annual_passive": round(monthly * 12),
        "commission_rate": f"{commission*100}%",
        "tier": tier,
    }

def generate_partner_agreement(contact, tier="reseller"):
    tier_data = PARTNER_TIERS[tier]
    return f"PARTNER AGREEMENT\n\nPartner: {contact.get('company','')}\nTier: {tier}\nCommission: {tier_data['commission']*100}%\nRequirements: {tier_data['requirements']}\nTerm: 12 months, auto-renewing\n\nSigned: _____________"

def run():
    earnings = calculate_partner_earnings(5, 500, "reseller")
    log.info(f"Partner potential: ${earnings['monthly_passive']:,}/mo passive")
    return earnings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()