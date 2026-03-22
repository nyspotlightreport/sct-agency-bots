#!/usr/bin/env python3
"""
KingSumo Giveaway Bot — NYSR Agency
Creates viral giveaway campaigns that build the Beehiiv list.
Strategy: Give away 1 of our own digital products → collect emails → 
          add to Beehiiv → monetize via Ad Network at 1,000 subscribers
Expected: 500-2,000 new subscribers per campaign
"""
import os, json

KINGSUMO_KEY = os.environ.get("KINGSUMO_API_KEY", "")
BEEHIIV_KEY  = os.environ.get("BEEHIIV_API_KEY", "")
BEEHIIV_PUB  = os.environ.get("BEEHIIV_PUB_ID", "")

# Pre-built giveaway campaigns — plug-and-play
CAMPAIGNS = [
    {
        "name": "WIN: Full Digital Product Bundle (Worth $89)",
        "prize": "Complete NY Spotlight Report Digital Bundle — all 10 products ($89 value)",
        "prize_value": 89,
        "duration_days": 7,
        "goal": "Build Beehiiv list to 1,000 subscribers for Ad Network unlock",
        "entry_methods": [
            {"type": "email", "points": 1, "label": "Enter with email"},
            {"type": "share_twitter", "points": 3, "label": "Share on Twitter/X (+3 entries)"},
            {"type": "follow_twitter", "points": 2, "label": "Follow @NYSpotlight (+2 entries)"},
            {"type": "subscribe_beehiiv", "points": 5, "label": "Subscribe to newsletter (+5 entries — best odds)"},
        ],
        "email_sequence": {
            "confirmation": "You're in! 🎉 One more way to win: Subscribe to the free NY Spotlight Report newsletter for 5 bonus entries.",
            "day3_nudge": "3 days left — your current odds are strong. Share with friends to boost your entries.",
            "winner": "🏆 Congratulations! You've won the Digital Bundle. Your download links are below."
        },
        "promo_posts": {
            "twitter": "🎁 GIVEAWAY: WIN all 10 of our digital products (planners, templates, prompt packs — $89 value)\n\nTo enter:\n✅ RT this tweet\n✅ Subscribe to our newsletter (link below)\n\n5 bonus entries for subscribers 👇\n\n#giveaway #passiveincome #digitalproducts",
            "instagram": "🎁 FREE GIVEAWAY — $89 Digital Bundle\n\nWinning this gets you:\n✅ 90-Day Goal Planner\n✅ 100 Instagram Caption Templates\n✅ 50 ChatGPT Prompts\n✅ Budget Planner + 6 more\n\nLink in bio to enter 👆\n\n#giveaway #digitalproducts #entrepreneur #passiveincome #freebies",
            "pinterest": "Win a $89 Digital Product Bundle! Planners, templates & AI prompt packs. Free to enter. Link in bio."
        }
    }
]

def generate_campaign_brief():
    """Output full campaign setup brief for KingSumo"""
    campaign = CAMPAIGNS[0]
    print("=" * 60)
    print("KINGSUMO GIVEAWAY — SETUP BRIEF")
    print("=" * 60)
    print(f"\nCampaign: {campaign['name']}")
    print(f"Prize: {campaign['prize']}")
    print(f"Value: ${campaign['prize_value']}")
    print(f"Duration: {campaign['duration_days']} days")
    print(f"\nGoal: {campaign['goal']}")
    print("\nEntry Methods:")
    for m in campaign["entry_methods"]:
        print(f"  +{m['points']} pts — {m['label']}")
    print("\nPromo Posts Ready:")
    for platform, copy in campaign["promo_posts"].items():
        print(f"\n[{platform.upper()}]")
        print(copy)
    print("\n" + "=" * 60)
    print("AFTER LAUNCH: Route all emails to Beehiiv via webhook")
    print("URL: https://api.beehiiv.com/v2/publications/{pub_id}/subscriptions")
    print("=" * 60)

if __name__ == "__main__":
    generate_campaign_brief()
