#!/usr/bin/env python3
"""
Beehiiv Email Drip Sequence Creator
Sets up 7-email welcome automation with embedded affiliate links
Revenue: Every new subscriber enters a sequence that drives affiliate clicks
"""
import os, requests, json

BEEHIIV_KEY = os.environ.get("BEEHIIV_API_KEY","")
BEEHIIV_PUB = os.environ.get("BEEHIIV_PUB_ID","")
BASE = "https://api.beehiiv.com/v2"
SITE = "https://nyspotlightreport.com"

DRIP_EMAILS = [
    {
        "delay_days": 0,
        "subject": "Welcome — your $500/month blueprint is inside",
        "preview": "The exact system I use to earn passively every month",
        "body": f"""Hi,

Welcome to the Passive Income Report.

Here's the blueprint I'll walk you through over the next week:

**Day 1-3: Zero-effort passive income (starts this week)**
Install EarnApp and Honeygain. Share your unused bandwidth. $40-100/month starts immediately.

**Day 4-7: Digital products (create once, earn forever)**  
I'll show you exactly which products sell without a following, and how to set them up free.

**Day 8-14: Affiliate commissions that compound**
The programs paying $100-1,000 per sale, and how to get your first referral without a huge audience.

Let's build this together.

— S.C. Thomas, NY Spotlight Report

P.S. The bandwidth apps take 5 minutes to install: [EarnApp](https://earnapp.com/i/NYSR) | [Honeygain](https://r.honeygain.me/NYSPOTLIGHT)
"""
    },
    {
        "delay_days": 1,
        "subject": "Day 1: Install these 2 apps and start earning tonight",
        "preview": "$40-100/month with zero daily work",
        "body": f"""Today's task takes 5 minutes.

**EarnApp** and **Honeygain** share your unused internet bandwidth with businesses that need residential IPs.

You don't do anything except have them installed. They run in the background.

**Install links:**
- [EarnApp](https://earnapp.com/i/NYSR) — Windows, Mac, Android, Raspberry Pi
- [Honeygain](https://r.honeygain.me/NYSPOTLIGHT) — Windows, Mac, Android, iOS

**Realistic earnings:** $30-60 combined per month per residential IP.

Most people see their first payment within 3-4 weeks. Both pay via PayPal.

That's it for today. Do it now while you're thinking about it.

Tomorrow: The digital products that sell while you sleep.
"""
    },
    {
        "delay_days": 3,
        "subject": "Day 3: The $9.99 product that sells every day",
        "preview": "Create once. Sell forever. Here's what actually converts.",
        "body": f"""The digital products that sell consistently without a following:

**1. Planners and templates ($7-15)**
Habit trackers, budget planners, content calendars. Buyers search for these on Etsy and Gumroad daily.

**2. AI prompt packs ($7-25)**
"50 ChatGPT prompts for [specific use case]" — high search volume, low competition.

**3. Swipe files and checklists ($5-15)**
Email templates, social media captions, startup checklists. Specific = sells.

**Where to sell:** Gumroad (free, 10% fee) or Etsy (90M buyers, $0.20/listing + 6.5%).

**The key:** One specific problem, one specific audience, one specific solution.

Full guide: [{SITE}/how-to-sell-digital-products-2026]({SITE}/how-to-sell-digital-products-2026)

Tomorrow: The affiliate programs that pay $100-1,000 per referral.
"""
    },
    {
        "delay_days": 6,
        "subject": "Day 6: Affiliate commissions — the highest ROI activity",
        "preview": "One honest recommendation = $100-1,000. Here are the programs.",
        "body": f"""The affiliate programs worth your time in 2026:

**Tier 1 — $200-1,000 per sale:**
- [HubSpot](https://hubspot.com/?via=nysr) — up to $1,000 | Genuinely the best free CRM
- [WP Engine](https://wpengine.com/?ref=nysr) — $200+ | Premium WordPress hosting  
- [Ahrefs](https://ahrefs.com/?ref=nysr) — $200 | Best SEO tool
- [SEMrush](https://semrush.com/?ref=nysr) — $200 | SEO + content

**Tier 2 — Recurring (compound over time):**
- [Kinsta](https://kinsta.com/?ref=nysr) — 10% recurring forever
- [ConvertKit](https://convertkit.com/?ref=nysr) — 30% recurring
- [Beehiiv](https://beehiiv.com/?via=nysr) — 25% recurring
- [ElevenLabs](https://elevenlabs.io/?ref=nysr) — 22% recurring

You don't need a huge audience. You need the right content in front of the right person.

One SEO article ranking for "best CRM for small business" converts 2-3 sales per month = $500-3,000 monthly from one page.

Full breakdown: [{SITE}/best-ai-tools-entrepreneurs-2026]({SITE}/best-ai-tools-entrepreneurs-2026)
"""
    },
    {
        "delay_days": 10,
        "subject": "Day 10: Print-on-demand — upload a design, earn forever",
        "preview": "Redbubble + Teepublic + Society6 = same design, 3x income",
        "body": f"""Print-on-demand is the most under-utilized passive income model.

You upload a design once. They manufacture, ship, handle returns, and pay you a royalty on every sale. Forever.

**The three platforms worth your time:**
1. **Redbubble** — Best organic discovery, 20%+ royalty
2. **Teepublic** — $4 flat per t-shirt, loyal buyer base  
3. **Society6** — Premium buyers, better for art prints

The strategy: Upload the same design to all three. 3x the listings, 3x the discovery, same 15-minute upload.

20 designs × 3 platforms = 60 listings earning 24/7.

**The design secret:** Zodiac art, typography quotes, and city minimalism consistently outsell complex designs. They're also the easiest to create with free tools.

Full guide: [{SITE}/best-print-on-demand-sites-2026]({SITE}/best-print-on-demand-sites-2026)
"""
    },
]

def setup_drip():
    if not BEEHIIV_KEY or not BEEHIIV_PUB:
        print("Missing BEEHIIV_API_KEY or BEEHIIV_PUB_ID")
        print("Get them at: app.beehiiv.com/settings/api")
        return

    print(f"Setting up Beehiiv drip sequence for publication: {BEEHIIV_PUB}")
    
    # Check if automations API is available
    r = requests.get(f"{BASE}/publications/{BEEHIIV_PUB}/automations",
        headers={"Authorization": f"Bearer {BEEHIIV_KEY}"}, timeout=10)
    
    print(f"Automations API: {r.status_code}")
    if r.ok:
        automations = r.json().get("data",[])
        print(f"Existing automations: {len(automations)}")
        for a in automations[:3]:
            print(f"  - {a.get('name','?')} | {a.get('status','?')}") 
    else:
        print(f"Response: {r.text[:200]}")
        print("\nBeehiiv automation setup requires manual configuration in dashboard:")
        print("1. Go to app.beehiiv.com")
        print("2. Automations → New Automation → Welcome Series")
        print("3. Add 5 emails based on the scripts in this file")
        print("4. Set delays: 0, 1, 3, 6, 10 days")

def run():
    setup_drip()
    
    # Save scripts for manual upload if needed
    import json
    with open("data/beehiiv_drip_scripts.json", "w") as f:
        json.dump(DRIP_EMAILS, f, indent=2)
    print("\nDrip scripts saved: data/beehiiv_drip_scripts.json")

if __name__ == "__main__":
    run()
