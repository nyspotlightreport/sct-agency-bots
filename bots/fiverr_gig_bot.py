#!/usr/bin/env python3
"""
Fiverr Gig Auto-Responder Bot — NYSR Agency
Manages Fiverr gigs for AI/automation services.
Gig ideas (all deliverable via our bots):
- AI Bot Setup: $50-500
- Newsletter Setup: $99-299
- Content Strategy: $150-499
- WordPress Blog Setup: $99-199
Bot auto-generates proposals from inbox messages.
"""
import os, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("FiverrBot")

GIGS = [
    {
        "title": "I will set up an automated content marketing system for your business",
        "price": {"basic": 99, "standard": 199, "premium": 499},
        "description": "I'll build a fully automated content system using AI bots that publish blog posts, social media content, and email newsletters on autopilot. Basic: WordPress blog bot. Standard: + social media. Premium: Full system.",
        "tags": ["automation", "content marketing", "wordpress", "ai", "chatgpt"],
        "delivery": "3 days basic / 5 days standard / 7 days premium",
    },
    {
        "title": "I will create and launch your Beehiiv newsletter with 14-day email sequence",
        "price": {"basic": 149, "standard": 249, "premium": 499},
        "description": "Full newsletter setup on Beehiiv including branding, welcome sequence, automation, and 4-week content calendar. Premium includes 3 months of weekly newsletters written by AI.",
        "tags": ["newsletter", "beehiiv", "email marketing", "automation", "passive income"],
        "delivery": "3 days / 5 days / 14 days",
    },
    {
        "title": "I will build passive income bots for bandwidth sharing and digital product delivery",
        "price": {"basic": 79, "standard": 149, "premium": 299},
        "description": "Set up bandwidth sharing apps (Honeygain, Traffmonetizer, Pawns) + Gumroad digital store with automated delivery webhooks.",
        "tags": ["passive income", "automation", "gumroad", "digital products", "bot"],
        "delivery": "1 day / 2 days / 3 days",
    },
]

AUTO_RESPONSE = """Hi! Thanks for reaching out.

I can definitely help with {inquiry_topic}.

Quick questions to confirm we're a fit:
1. What's your timeline?
2. Do you have existing content/products, or starting from scratch?
3. What's your main goal (traffic, revenue, list growth)?

Based on what you've described, I'd recommend our {recommended_package} package at ${price}.

This includes:
{deliverables}

I typically respond within 2 hours. Looking forward to working with you!

— S.C. Thomas, NY Spotlight Report"""

if __name__ == "__main__":
    log.info(f"Fiverr gigs ready: {len(GIGS)}")
    for g in GIGS:
        total = sum(g["price"].values())
        log.info(f"  ${g['price']['basic']}-{g['price']['premium']} — {g['title'][:60]}")
    log.info("\nSetup: fiverr.com/selling → create each gig → add to profile")
    log.info("At 2 orders/mo per gig = $600-1,500/mo additional")
    import json
    with open("data/fiverr_gigs.json","w") as f:
        json.dump(GIGS, f, indent=2)
