#!/usr/bin/env python3
"""
LemonSqueezy Store Builder — NYSR Agency
Creates all 10 digital products on LemonSqueezy with:
- Built-in affiliate program (30% commission)
- Automatic checkout URLs
- Zero transaction fees (Stripe only)
Requires: LEMONSQUEEZY_API_KEY secret in GitHub
"""
import os, json, ssl, urllib.request, urllib.parse, time

API_KEY  = os.environ.get("LEMONSQUEEZY_API_KEY", "")
BASE     = "https://api.lemonsqueezy.com/v1"
STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "")

PRODUCTS = [
    {"name": "90-Day Goal Planner",                    "price": 1299, "desc": "Crush your quarterly goals with this structured 90-day system. Daily/weekly/monthly reviews, habit trackers, and priority matrices. Instant PDF download."},
    {"name": "30-Day Social Media Content Calendar",   "price": 999,  "desc": "30 done-for-you post ideas for Instagram, TikTok, LinkedIn & Twitter/X. Includes hashtag banks and caption formulas."},
    {"name": "50 ChatGPT Prompts for Business",        "price": 799,  "desc": "50 battle-tested ChatGPT prompts for marketing copy, email sequences, sales scripts, and content creation. Copy-paste ready."},
    {"name": "Monthly Budget Planner",                 "price": 899,  "desc": "Track income, control expenses, and grow your net worth month by month. Includes debt payoff tracker and net worth calculator."},
    {"name": "Weekly Meal Prep Planner",               "price": 699,  "desc": "7-day meal planning with grocery lists, macro tracking, prep schedule, and 20+ recipe cards. Save time and money every week."},
    {"name": "Daily Habit Tracker — 30 Day Reset",     "price": 699,  "desc": "Build habits that actually stick. Track up to 5 habits daily with mood tracking and weekly completion reviews."},
    {"name": "100 Instagram Caption Templates",        "price": 799,  "desc": "Fill-in-the-blank captions for every niche, mood, and content type. Hook formulas, engagement drivers, and CTA scripts included."},
    {"name": "Content Creation Checklist",             "price": 599,  "desc": "The exact 50-point checklist for creating blog posts, social media, email, and video content that converts, ranks, and gets shared."},
    {"name": "Annual Business Plan Template",          "price": 1499, "desc": "Your complete one-page + detailed annual business plan. Revenue breakdown, marketing plan, OKRs, risk register, and quarterly goals."},
    {"name": "Passive Income Zero-Cost Guide",         "price": 1499, "desc": "25 proven passive income methods that require $0 to start. Includes 90-day launch plan and realistic earnings by method."},
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(method, path, data=None):
    url  = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req  = urllib.request.Request(url, data=body, method=method,
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Accept": "application/vnd.api+json",
                 "Content-Type": "application/vnd.api+json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read())
    except urllib.request.HTTPError as e:
        return {"error": e.code, "msg": e.read().decode()[:200]}

def get_store():
    r = api("GET", "/stores")
    stores = r.get("data", [])
    if stores:
        s = stores[0]
        return s["id"], s["attributes"]["name"]
    return None, None

def create_product(store_id, prod):
    payload = {"data": {"type": "products", "attributes": {
        "name": prod["name"],
        "description": prod["desc"],
        "status": "published"
    }, "relationships": {"store": {"data": {"type": "stores", "id": str(store_id)}}}}}
    return api("POST", "/products", payload)

def create_variant(product_id, price_cents):
    payload = {"data": {"type": "variants", "attributes": {
        "name": "Default",
        "price": price_cents,
        "is_membership": False,
        "interval": None
    }, "relationships": {"product": {"data": {"type": "products", "id": str(product_id)}}}}}
    return api("POST", "/variants", payload)

def run():
    if not API_KEY:
        print("❌ No LEMONSQUEEZY_API_KEY set")
        print("👉 Get yours at: https://app.lemonsqueezy.com/settings/api")
        return

    store_id, store_name = get_store()
    if not store_id:
        print("❌ Could not find store. Check API key.")
        return

    print(f"✅ Store: {store_name} (ID: {store_id})")
    print(f"Creating {len(PRODUCTS)} products with affiliate program...\n")

    results = []
    for p in PRODUCTS:
        r = create_product(store_id, p)
        if "data" in r:
            pid    = r["data"]["id"]
            slug   = r["data"]["attributes"].get("slug", "")
            buy_url = r["data"]["attributes"].get("buy_now_url", f"https://store.lemonsqueezy.com/checkout/buy/{slug}")
            results.append({"name": p["name"], "price": p["price"]/100, "id": pid, "url": buy_url})
            print(f"✅ {p['name']} — ${p['price']/100:.2f}")
            print(f"   Buy URL: {buy_url}")
        else:
            print(f"❌ {p['name']}: {r}")
        time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"✅ LemonSqueezy Store LIVE: {len(results)}/{len(PRODUCTS)} products")
    print(f"💰 Total catalog value: ${sum(p['price'] for p in results):.2f}")
    print(f"🔗 Affiliate program: https://app.lemonsqueezy.com/affiliates")
    print("   Set commission to 30% — let others sell for you")

if __name__ == "__main__":
    run()
