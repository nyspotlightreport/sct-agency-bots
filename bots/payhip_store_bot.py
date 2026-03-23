#!/usr/bin/env python3
"""
Payhip Store Auto-Builder
Payhip API: Creates products, uploads files, sets prices
FREE plan: 5% fee, no monthly cost
Run: export PAYHIP_API_KEY=your_key (get from payhip.com/settings/api)
"""
import os, json, requests, time, base64

API_KEY = os.environ.get("PAYHIP_API_KEY", "")
BASE = "https://payhip.com/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
PDF_DIR = os.path.join(os.path.dirname(__file__), "gumroad_pdfs")

PRODUCTS = [
    {"name": "90-Day Goal Planner",                     "price": "12.99", "file": "90_day_goal_planner.pdf",
     "desc": "A structured 90-day goal planner with weekly reviews, habit trackers, and priority matrices. Crush your quarterly goals."},
    {"name": "30-Day Social Media Content Calendar",    "price": "9.99",  "file": "30_day_social_content_calendar.pdf",
     "desc": "30 days of done-for-you content ideas for Instagram, TikTok, LinkedIn & Twitter/X. Hashtag banks included."},
    {"name": "50 ChatGPT Prompts for Business",         "price": "7.99",  "file": "50_chatgpt_prompts_business.pdf",
     "desc": "50 battle-tested AI prompts for marketing copy, sales scripts, content, and operations. Copy-paste ready."},
    {"name": "100 Instagram Caption Templates",         "price": "7.99",  "file": "100_instagram_captions.pdf",
     "desc": "Fill-in-the-blank captions for every niche, mood, and content type. Never run out of ideas again."},
    {"name": "Monthly Budget Planner",                  "price": "8.99",  "file": "monthly_budget_planner.pdf",
     "desc": "Track income, control expenses, and grow your net worth — month by month."},
    {"name": "Weekly Meal Prep Planner",                "price": "6.99",  "file": "weekly_meal_prep_planner.pdf",
     "desc": "7-day meal planning with grocery lists, macro tracking, and 20+ quick recipe cards."},
    {"name": "Daily Habit Tracker — 30 Day Reset",      "price": "6.99",  "file": "daily_habit_tracker_30day.pdf",
     "desc": "30-day habit tracker with daily check-ins, mood tracking, and weekly review sections."},
    {"name": "Content Creation Checklist",              "price": "5.99",  "file": "content_creation_checklist.pdf",
     "desc": "50-point checklist covering blogs, social, email, and video. Every post, done right."},
    {"name": "Annual Business Plan Template",           "price": "14.99", "file": "annual_business_plan_template.pdf",
     "desc": "One-page summary + full 12-month business plan with revenue targets, OKRs, and risk register."},
    {"name": "Passive Income Zero-Cost Guide",          "price": "14.99", "file": "passive_income_zero_cost_guide.pdf",
     "desc": "25 proven passive income methods that require $0 to start. Includes 90-day launch plan."},
]

def create_product(p):
    pdf_path = os.path.join(PDF_DIR, p["file"])
    
    if not os.path.exists(pdf_path):
        print(f"  ⚠️  PDF missing: {pdf_path} — skipping file upload")
        pdf_data = None
    else:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

    form_data = {
        "title": p["name"],
        "description": p["desc"],
        "price": p["price"],
        "currency": "USD",
        "type": "digital",
        "published": "true",
    }

    files = {}
    if pdf_data:
        files["file"] = (p["file"], pdf_data, "application/pdf")

    r = requests.post(f"{BASE}/products",
                      headers={"Authorization": f"Bearer {API_KEY}"},
                      data=form_data,
                      files=files if files else None)
    return r

def run():
    if not API_KEY:
        print("❌ PAYHIP_API_KEY not set")
        print("Steps:")
        print("  1. Go to https://payhip.com → Sign Up (free)")
        print("  2. Settings → API → Generate Key")
        print("  3. Run: PAYHIP_API_KEY=your_key python3 payhip_store_bot.py")
        return

    print("=== PAYHIP STORE BUILDER ===\n")
    results = []

    for p in PRODUCTS:
        print(f"Creating: {p['name']} @ ${p['price']}")
        r = create_product(p)
        if r.status_code in [200, 201]:
            try:
                d = r.json()
                link = d.get("link", d.get("url", "created"))
                print(f"  ✅ Live: {link}")
                results.append({"name": p["name"], "price": p["price"], "url": link})
            except Exception:  # noqa: bare-except
                print(f"  ✅ Created (status {r.status_code})")
        else:
            print(f"  ❌ Failed ({r.status_code}): {r.text[:150]}")
        time.sleep(0.5)

    print(f"\n✅ {len(results)} products live on Payhip")
    with open("/home/claude/payhip_products.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run()
