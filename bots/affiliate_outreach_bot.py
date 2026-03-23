#!/usr/bin/env python3
# Affiliate Outreach Bot - Recruits affiliates, manages program, tracks commissions.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
log = logging.getLogger(__name__)

AFFILIATE_PROGRAM = {
    "commission": "30% recurring for 12 months",
    "cookie_days": 90,
    "min_payout": "$50",
    "payout_schedule": "Monthly on the 15th",
    "signup_url": "https://nyspotlightreport.com/affiliates/",
}

AFFILIATE_TARGETS = [
    "Marketing newsletters (10k+ subscribers)",
    "YouTube channels (content creation niche)",
    "Business podcasts",
    "SaaS review blogs",
    "Marketing tool aggregators",
    "LinkedIn influencers in marketing",
]

def generate_affiliate_pitch(prospect):
    name = (prospect.get("name","") or "").split()[0] or "there"
    audience = prospect.get("audience","your audience")
    return {
        "subject": f"Partnership opportunity - earn 30% recurring, {name}?",
        "body": claude(
            "Write an affiliate partnership pitch email. 30% recurring commission for 12 months. Under 120 words.",
            f"To: {name}. Their audience: {audience}. Our product: AI content automation at $97-497/mo.",
            max_tokens=200
        ) or f"Hi {name}, I run NYSR - an AI content automation platform at $97-497/mo. I'd love to offer you 30% recurring commission (for 12 months) for every customer you refer. Given your audience at {audience}, I think it could be a great fit. Interested in the details?",
    }

def run():
    prospects = [
        {"name":"Marketing Newsletter","audience":"50k marketing professionals"},
        {"name":"AI Tools Blog","audience":"tech-savvy entrepreneurs"},
    ]
    for p in prospects:
        pitch = generate_affiliate_pitch(p)
        log.info(f"Affiliate pitch: {pitch['subject']}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
