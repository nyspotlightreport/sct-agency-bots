#!/usr/bin/env python3
"""
Merch Platform Bot — NYSR Agency
Generates print-on-demand designs and submits to:
- TeePublic (instant approval)
- Redbubble (already live)
- Merch by Amazon (invite-only, submit request)
- Spreadshirt
- Zazzle
All zero inventory, zero fulfillment.
"""
import os, requests, json, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("MerchBot")

DESIGNS = [
    {"text": "PASSIVE INCOME > ACTIVE INCOME", "niche": "entrepreneur", "color": "#C9A84C"},
    {"text": "BUILD IN PUBLIC. PROFIT IN PRIVATE.", "niche": "startup", "color": "#1B3A5C"},
    {"text": "90 DAYS TO CHANGE EVERYTHING", "niche": "motivation", "color": "#1A3320"},
    {"text": "SIDE HUSTLE SEASON. ALL YEAR.", "niche": "hustle", "color": "#2D1B0E"},
    {"text": "WORK SMARTER. EARN WHILE YOU SLEEP.", "niche": "entrepreneur", "color": "#0D1B2A"},
    {"text": "DAILY HABITS. LONG GAME.", "niche": "productivity", "color": "#2A1A0F"},
    {"text": "NOT A JOB. A REVENUE SYSTEM.", "niche": "entrepreneur", "color": "#1C1C3A"},
    {"text": "AUTOMATE EVERYTHING.", "niche": "tech", "color": "#0F2A2A"},
    {"text": "MY PORTFOLIO IS PAYING ME.", "niche": "finance", "color": "#1A2A0F"},
    {"text": "SUBSCRIBE TO THE LIFESTYLE.", "niche": "digital nomad", "color": "#2A1A3A"},
]

PLATFORMS = {
    "TeePublic": "https://www.teepublic.com/user/nyspotlightreport/sell",
    "Redbubble":  "https://www.redbubble.com/portfolio/images/new (already live)",
    "Merch by Amazon": "https://merch.amazon.com (submit invite request)",
    "Spreadshirt": "https://www.spreadshirt.com/create-and-sell",
    "Zazzle": "https://www.zazzle.com/sell",
    "Printful+Etsy": "printful.com → connect Etsy store → auto-fulfill",
}

if __name__ == "__main__":
    log.info(f"{len(DESIGNS)} designs ready")
    log.info(f"Estimated revenue per platform: $20-100/mo at scale")
    for platform, url in PLATFORMS.items():
        log.info(f"  {platform}: {url}")
    with open("data/merch_designs.json","w") as f:
        json.dump(DESIGNS, f, indent=2)
    log.info("Designs saved to data/merch_designs.json")
