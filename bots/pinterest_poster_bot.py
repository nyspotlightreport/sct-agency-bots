#!/usr/bin/env python3
"""
Pinterest Auto-Poster Bot
Posts affiliate content pins + POD design pins daily
Pinterest drives massive free traffic to affiliate pages and Redbubble
Uses Pinterest API v5
"""
import os, requests, json, datetime, random

PINTEREST_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN","")
SITE = "https://nyspotlightreport.com"
RB_BASE = "https://www.redbubble.com/people/nysr101"

# Pin templates for affiliate content
AFFILIATE_PINS = [
    {
        "title": "Best Passive Income Apps 2026 — $60-100/Month Doing Nothing",
        "description": "The apps that literally pay you while you sleep. EarnApp and Honeygain pay you to share unused bandwidth. $40-100/month, zero work. Full guide 👉 nyspotlightreport.com/best-passive-income-apps-2026 #passiveincome #sidehustle #makemoneyonline",
        "link": f"{SITE}/best-passive-income-apps-2026",
    },
    {
        "title": "Build a $500/Month Passive Income in 90 Days",
        "description": "Step by step: bandwidth sharing ($60) + digital products ($150) + affiliate commissions ($200) + print on demand ($90) = $500/month. All automated. Full breakdown at nyspotlightreport.com #passiveincome #financialfreedom",
        "link": f"{SITE}/passive-income-online-2026",
    },
    {
        "title": "How to Start a Newsletter That Earns Money Immediately",
        "description": "Beehiiv pays you from your FIRST subscriber via their ad network. No minimum. No wait. Just write, grow, earn. Free to start. Guide: nyspotlightreport.com/how-to-start-newsletter-make-money #newsletter #beehiiv #emailmarketing",
        "link": f"{SITE}/how-to-start-newsletter-make-money",
    },
    {
        "title": "Amazon KDP: Publish Books With ZERO Upfront Cost",
        "description": "Low content books (journals, planners, puzzle books) earn royalties forever on Amazon. 10 books can generate $200-500/month passively. No writing degree needed. Guide: nyspotlightreport.com/amazon-kdp-guide-2026 #amazonkdp #passiveincome",
        "link": f"{SITE}/amazon-kdp-guide-2026",
    },
    {
        "title": "Print-on-Demand: Upload Once, Earn Forever",
        "description": "Redbubble + Teepublic + Society6 = upload your design to 3 platforms, earn royalties on every sale. No inventory. No shipping. Just passive income. Guide: nyspotlightreport.com/best-print-on-demand-sites-2026 #printondemand #redbubble",
        "link": f"{SITE}/best-print-on-demand-sites-2026",
    },
    {
        "title": "Sell Digital Products and Make Money While You Sleep",
        "description": "Templates, planners, prompt packs. Create once on Gumroad or Etsy, sell forever. 90%+ margin. No fulfillment. Pure passive income. Full guide: nyspotlightreport.com/how-to-sell-digital-products-2026 #digitalproducts #gumroad",
        "link": f"{SITE}/how-to-sell-digital-products-2026",
    },
]

# POD Design pins linking to Redbubble
DESIGN_PINS = [
    {"title": "NYC Skyline Minimal Black White Art Print", "description": "Minimal New York City skyline print. Available on t-shirts, hoodies, phone cases, mugs, and more. Ships worldwide. #nyc #newyork #minimalist #wallart", "link": RB_BASE},
    {"title": "Hustle Daily Gold Motivational Poster", "description": "Bold gold typography motivational print. Perfect for home office or gym. Available on posters, canvas, and apparel. #hustle #motivation #entrepreneur", "link": RB_BASE},
    {"title": "Moon Phases Celestial Art Print", "description": "Minimalist lunar cycle art. Dark navy with white moon phases. Available as poster, canvas, and phone case. #moonphases #celestial #astronomy #wallart", "link": RB_BASE},
    {"title": "Sacred Geometry Mandala Art Print", "description": "Intricate geometric mandala on black background. Perfect for meditation spaces. Available on canvas, posters, and tapestries. #mandala #sacredgeometry #spiritual", "link": RB_BASE},
    {"title": "Retro 80s Synthwave Aesthetic Poster", "description": "Neon synthwave poster with retro grid. Perfect for gaming rooms and offices. T-shirts, hoodies, posters available. #synthwave #retro #80s #vaporwave", "link": RB_BASE},
]

def get_boards():
    r = requests.get("https://api.pinterest.com/v5/boards",
        headers={"Authorization": f"Bearer {PINTEREST_TOKEN}"}, timeout=10)
    if r.ok:
        return r.json().get("items", [])
    print(f"Boards error: {r.status_code} {r.text[:100]}")
    return []

def create_pin(board_id, title, description, link, image_url=None):
    payload = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url or "https://nyspotlightreport.com/assets/og-default.png"
        }
    }
    r = requests.post("https://api.pinterest.com/v5/pins",
        headers={"Authorization": f"Bearer {PINTEREST_TOKEN}", "Content-Type": "application/json"},
        json=payload, timeout=15)
    return r.ok, r.status_code

def run():
    if not PINTEREST_TOKEN:
        print("No PINTEREST_ACCESS_TOKEN — connect at developers.pinterest.com")
        print("Steps:")
        print("1. Create app at developers.pinterest.com")
        print("2. Request access token with boards:read,boards:write,pins:read,pins:write")
        print("3. Add PINTEREST_ACCESS_TOKEN to GitHub Secrets")
        return

    boards = get_boards()
    if not boards:
        print("No Pinterest boards found. Create boards at pinterest.com first:")
        print("  - Passive Income Tips")
        print("  - Wall Art Prints")
        print("  - Side Hustle Ideas")
        return

    board_id = boards[0]["id"]
    print(f"Posting to board: {boards[0].get('name','?')}")

    today = datetime.date.today().timetuple().tm_yday
    all_pins = AFFILIATE_PINS + DESIGN_PINS
    pin = all_pins[today % len(all_pins)]

    ok, code = create_pin(board_id, pin["title"], pin["description"], pin["link"])
    if ok:
        print(f"✅ Pin posted: {pin['title'][:60]}")
    else:
        print(f"❌ Failed: {code}")

if __name__ == "__main__":
    run()
