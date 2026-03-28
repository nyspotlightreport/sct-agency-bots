#!/usr/bin/env python3
"""
KingSumo Giveaway Bot — NYSR Agency
Creates and launches viral giveaway campaigns automatically.
Each campaign targets 500-2,000 new Beehiiv subscribers.
At 1,000 subs → Beehiiv Ad Network = $200-2,000/mo flipped on.
"""
import os, requests, json, time, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("KingSumoBot")

KS_KEY      = os.environ.get("KINGSUMO_API_KEY", "")
BEEHIIV_KEY = os.environ.get("BEEHIIV_API_KEY", "")
BEEHIIV_PUB = os.environ.get("BEEHIIV_PUB_ID", "")
# AG-NUCLEAR-GMAIL-ZERO-20260328: GMAIL       = os.environ.get("GMAIL_USER", "nyspotlightreport@gmail.com")

CAMPAIGN = {
    "name": "WIN: Complete Digital Productivity Bundle ($89 value)",
    "start_at": None,  # immediate
    "end_at": None,    # 7 days
    "prize": "All 10 NY Spotlight Report digital products — Goal Planner, Budget Tracker, 50 ChatGPT Prompts, Passive Income Guide + 6 more ($89 total value)",
    "entry_methods": [
        {"type": "email",         "points": 1, "label": "Enter with your email"},
        {"type": "share_twitter", "points": 3, "label": "Share on Twitter (+3 entries)"},
        {"type": "follow_twitter","points": 2, "label": "Follow @NYSpotlight (+2 entries)"},
        {"type": "newsletter",    "points": 5, "label": "Subscribe to newsletter (+5 entries — best odds)"},
    ],
    "thank_you_url": "https://nyspotlightreport.com/downloads/",
    "beehiiv_webhook": f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUB}/subscriptions",
}

PROMO_POSTS = {
    "twitter": """🎁 GIVEAWAY — Win our complete digital bundle ($89 value)

10 products including:
✅ 90-Day Goal Planner
✅ 50 ChatGPT Prompts for Business  
✅ Passive Income Guide
✅ Budget Planner + 6 more

To enter → subscribe to our free newsletter (5x entries):
👇 [LINK]

RT for extra entries 🔄

#giveaway #passiveincome #entrepreneur""",

    "instagram": """🎁 FREE GIVEAWAY — Win $89 in digital products

We're giving away our ENTIRE digital bundle:
• 90-Day Goal Planner
• 50 ChatGPT Business Prompts
• Passive Income Zero-Cost Guide
• Monthly Budget Planner
+ 6 more products

Subscribe to our newsletter for 5x entries (link in bio)
Ends in 7 days 👆

#giveaway #digitalproducts #passiveincome #sidehustle #entrepreneur""",

    "pinterest": "WIN $89 in digital products! Goal planner, budget tracker, ChatGPT prompts + more. Enter free via link."
}

def create_campaign():
    if not KS_KEY:
        log.warning("No KINGSUMO_API_KEY — generating campaign brief only")
        print("\n=== KINGSUMO CAMPAIGN BRIEF ===")
        print(f"Prize: {CAMPAIGN['prize']}")
        print(f"Duration: 7 days")
        print("\nPromo Posts:")
        for p, t in PROMO_POSTS.items():
            print(f"\n[{p.upper()}]")
            print(t)
        print("\nManual setup: https://app.kingsumo.com/giveaways/create")
        return

    r = requests.post("https://app.kingsumo.com/api/v1/giveaways",
        headers={"Authorization": f"Bearer {KS_KEY}", "Content-Type": "application/json"},
        json=CAMPAIGN, timeout=15)
    if r.status_code == 201:
        data = r.json()
        log.info(f"✅ Giveaway created: {data.get('url','')}")
    else:
        log.error(f"API error: {r.status_code}")

if __name__ == "__main__":
    create_campaign()
