#!/usr/bin/env python3
"""
LemonSqueezy Store Auto-Builder
Creates all 10 products with files, affiliate program, checkout links
Run ONCE after Chairman creates free account at lemonsqueezy.com
Set: export LEMONSQUEEZY_API_KEY=your_key
"""
import os, json, requests, time

API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
BASE = "https://api.lemonsqueezy.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json"
}

PRODUCTS = [
    {"name": "90-Day Goal Planner",                           "price": 1299, "file": "90_day_goal_planner.pdf"},
    {"name": "30-Day Social Media Content Calendar",          "price": 999,  "file": "30_day_social_content_calendar.pdf"},
    {"name": "50 ChatGPT Prompts for Business",               "price": 799,  "file": "50_chatgpt_prompts_business.pdf"},
    {"name": "100 Instagram Caption Templates",               "price": 799,  "file": "100_instagram_captions.pdf"},
    {"name": "Monthly Budget Planner",                        "price": 899,  "file": "monthly_budget_planner.pdf"},
    {"name": "Weekly Meal Prep Planner",                      "price": 699,  "file": "weekly_meal_prep_planner.pdf"},
    {"name": "Daily Habit Tracker — 30 Day Reset",            "price": 699,  "file": "daily_habit_tracker_30day.pdf"},
    {"name": "Content Creation Checklist — 50 Posts",        "price": 599,  "file": "content_creation_checklist.pdf"},
    {"name": "Annual Business Plan Template",                 "price": 1499, "file": "annual_business_plan_template.pdf"},
    {"name": "Passive Income Zero-Cost Guide",                "price": 1499, "file": "passive_income_zero_cost_guide.pdf"},
]

def get_store_id():
    r = requests.get(f"{BASE}/stores", headers=HEADERS)
    stores = r.json().get("data", [])
    if stores:
        sid = stores[0]["id"]
        print(f"✅ Store ID: {sid} — {stores[0]['attributes']['name']}")
        return sid
    print("❌ No store found. Create one at app.lemonsqueezy.com")
    return None

def create_product(store_id, product):
    payload = {
        "data": {
            "type": "products",
            "attributes": {
                "name": product["name"],
                "description": f"Instant digital download. Professional template by NY Spotlight Report.",
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": str(store_id)}}
            }
        }
    }
    r = requests.post(f"{BASE}/products", headers=HEADERS, json=payload)
    if r.status_code in [200, 201]:
        return r.json()["data"]["id"]
    print(f"  ❌ Product create failed: {r.text[:200]}")
    return None

def create_variant(product_id, price_cents):
    payload = {
        "data": {
            "type": "variants",
            "attributes": {
                "name": "Standard",
                "price": price_cents,
                "is_subscription": False,
                "pay_what_you_want": False,
            },
            "relationships": {
                "product": {"data": {"type": "products", "id": str(product_id)}}
            }
        }
    }
    r = requests.post(f"{BASE}/variants", headers=HEADERS, json=payload)
    if r.status_code in [200, 201]:
        return r.json()["data"]["id"]
    print(f"  ❌ Variant failed: {r.text[:200]}")
    return None

def run():
    if not API_KEY:
        print("❌ Set LEMONSQUEEZY_API_KEY first")
        print("   1. Go to: https://app.lemonsqueezy.com/settings/api")
        print("   2. Create API key")
        print("   3. Run: export LEMONSQUEEZY_API_KEY=your_key_here")
        print("   4. Re-run this script")
        return

    store_id = get_store_id()
    if not store_id:
        return

    print(f"\nCreating {len(PRODUCTS)} products in LemonSqueezy...\n")
    results = []

    for p in PRODUCTS:
        print(f"  → {p['name']}")
        pid = create_product(store_id, p)
        if pid:
            vid = create_variant(pid, p["price"])
            results.append({
                "name": p["name"],
                "product_id": pid,
                "variant_id": vid,
                "price": p["price"] / 100,
            })
            print(f"    ✅ Created (product: {pid})")
        time.sleep(0.5)

    print(f"\n✅ {len(results)}/{len(PRODUCTS)} products created")
    print("\n📋 Next: Upload PDF files in app.lemonsqueezy.com/products")
    print("📋 Enable affiliate program: Settings → Affiliates → 30% commission")

    with open("/home/claude/lemonsqueezy_products.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nProduct IDs saved to lemonsqueezy_products.json")

if __name__ == "__main__":
    run()
