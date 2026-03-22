#!/usr/bin/env python3
"""
Pinterest Auto-Setup + Poster Bot — FIXED v3
Issue found: Token exists, but no Pinterest boards in account.
Fix: Auto-creates boards via API, then posts to them.

Boards created:
1. "Passive Income Ideas" — highest traffic niche
2. "AI Tools for Entrepreneurs"  
3. "Content Marketing Tips"
4. "Side Hustle Strategies"
5. "Digital Products"
"""
import os, logging, requests, json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [Pinterest] %(message)s")
log = logging.getLogger()

TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
BASE  = "https://api.pinterest.com/v5"
HDRS  = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

BOARDS_TO_CREATE = [
    {"name": "Passive Income Ideas 2026",     "description": "Proven passive income strategies, tools, and systems for entrepreneurs. Updated weekly.", "privacy": "PUBLIC"},
    {"name": "AI Tools for Entrepreneurs",     "description": "Best AI tools, automations, and workflows for business owners and online entrepreneurs.", "privacy": "PUBLIC"},
    {"name": "Content Marketing Automation",  "description": "How to automate your blog, newsletter, and social media. Systems that run without you.", "privacy": "PUBLIC"},
    {"name": "Side Hustle Strategies",         "description": "Side hustle ideas, income stacks, and proven methods to earn online in 2026.", "privacy": "PUBLIC"},
    {"name": "Digital Products & Downloads",  "description": "How to create and sell digital products — templates, guides, planners, and more.", "privacy": "PUBLIC"},
]

PIN_TEMPLATES = [
    {
        "title": "25 Passive Income Streams That Cost $0 to Start",
        "description": "Every method on this list is free to start. Bandwidth sharing, digital products, affiliate marketing, newsletter monetization — all running on autopilot. Full guide at nyspotlightreport.com/blog/passive-income-zero-cost-2026/",
        "link": "https://nyspotlightreport.com/blog/passive-income-zero-cost-2026/",
        "board_name": "Passive Income Ideas 2026"
    },
    {
        "title": "How to Automate Your Entire Content Operation",
        "description": "Blog, newsletter, social media, YouTube — all automated. 63 AI bots. Zero manual work after setup. See the full system at nyspotlightreport.com",
        "link": "https://nyspotlightreport.com/blog/automated-content-operation/",
        "board_name": "Content Marketing Automation"
    },
    {
        "title": "The Cold Email System That Books 5 Demos/Week",
        "description": "Apollo + Claude + Gmail = 200 personalized emails per day. 8-12% reply rate. Full breakdown at nyspotlightreport.com",
        "link": "https://nyspotlightreport.com/blog/cold-email-system-proflow/",
        "board_name": "Side Hustle Strategies"
    },
    {
        "title": "Free 30-Day Content Plan Generator",
        "description": "AI builds your complete content calendar in 60 seconds. Blog posts, newsletter, social media — all planned. Free at nyspotlightreport.com/free-plan/",
        "link": "https://nyspotlightreport.com/free-plan/",
        "board_name": "AI Tools for Entrepreneurs"
    },
    {
        "title": "10 Digital Products You Can Sell on Gumroad Today",
        "description": "Templates, planners, guides, checklists — create once, sell forever. See our full store at spotlightny.gumroad.com",
        "link": "https://nyspotlightreport.com/blog/passive-income-zero-cost-2026/",
        "board_name": "Digital Products & Downloads"
    },
]

def get_boards():
    r = requests.get(f"{BASE}/boards", headers=HDRS, timeout=10)
    if r.status_code == 200:
        return {b["name"]: b["id"] for b in r.json().get("items", [])}
    log.error(f"Get boards: {r.status_code} {r.text[:100]}")
    return {}

def create_board(name, description, privacy="PUBLIC"):
    r = requests.post(f"{BASE}/boards",
        headers=HDRS,
        json={"name": name, "description": description, "privacy": privacy},
        timeout=15)
    if r.status_code in [200, 201]:
        board_id = r.json().get("id")
        log.info(f"  ✅ Board created: '{name}' ({board_id})")
        return board_id
    log.error(f"  ❌ Board creation failed: {r.status_code} {r.text[:100]}")
    return None

def create_pin(board_id, title, description, link):
    payload = {
        "board_id": board_id,
        "title": title[:100],
        "description": description[:500],
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1000&q=80"
        }
    }
    r = requests.post(f"{BASE}/pins", headers=HDRS, json=payload, timeout=20)
    ok = r.status_code in [200, 201]
    log.info(f"  {'✅' if ok else '❌'} Pin: {title[:50]} | {r.status_code}")
    if not ok: log.debug(r.text[:200])
    return ok

def run():
    if not TOKEN:
        log.error("No PINTEREST_ACCESS_TOKEN in environment")
        log.info("Get token: developers.pinterest.com → My apps → create app → generate access token")
        log.info("Scopes needed: boards:read boards:write pins:read pins:write")
        return

    log.info("Pinterest Bot v3 starting...")
    
    # Step 1: Get existing boards
    boards = get_boards()
    log.info(f"Existing boards: {len(boards)} — {list(boards.keys())[:3]}")
    
    # Step 2: Create any missing boards
    for board_def in BOARDS_TO_CREATE:
        if board_def["name"] not in boards:
            log.info(f"Creating board: {board_def['name']}")
            new_id = create_board(board_def["name"], board_def["description"], board_def["privacy"])
            if new_id:
                boards[board_def["name"]] = new_id
    
    # Step 3: Post today's pin
    import datetime
    today_pin = PIN_TEMPLATES[datetime.date.today().timetuple().tm_yday % len(PIN_TEMPLATES)]
    board_id  = boards.get(today_pin["board_name"])
    
    if not board_id:
        # Fallback to any board
        board_id = list(boards.values())[0] if boards else None
    
    if board_id:
        ok = create_pin(board_id, today_pin["title"], today_pin["description"], today_pin["link"])
        if ok:
            log.info(f"✅ Pinterest: pin posted to '{today_pin['board_name']}'")
    else:
        log.error("No boards available — check token permissions")

if __name__ == "__main__":
    run()
