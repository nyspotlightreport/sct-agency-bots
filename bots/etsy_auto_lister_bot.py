#!/usr/bin/env python3
"""
Etsy Digital Product Auto-Lister — NYSR Agency
Lists all 10 digital PDFs on Etsy automatically.
Requires: ETSY_API_KEY, ETSY_SHOP_ID in GitHub secrets
90M+ active buyers vs Gumroad's smaller base.
"""
import os, requests, json, time, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("EtsyBot")

API_KEY  = os.environ.get("ETSY_API_KEY", "")
SHOP_ID  = os.environ.get("ETSY_SHOP_ID", "")
BASE     = "https://openapi.etsy.com/v3/application"

PRODUCTS = [
    {"title": "90-Day Goal Planner PDF - Quarterly Goals Tracker Printable",
     "price": 1299, "tags": ["goal planner","quarterly planner","printable planner","digital download","productivity"],
     "file": "90_day_goal_planner.pdf", "desc": "Crush your quarterly goals with this 90-day structured planner. Daily/weekly/monthly review sections, habit trackers, priority matrices. Instant PDF download."},
    {"title": "50 ChatGPT Prompts for Business - AI Prompts Pack",
     "price": 799,  "tags": ["chatgpt prompts","ai prompts","business prompts","digital download","entrepreneur"],
     "file": "50_chatgpt_prompts_business.pdf", "desc": "50 battle-tested ChatGPT prompts for marketing, sales, email, and content creation. Copy-paste ready. Instant download."},
    {"title": "Passive Income Guide PDF - 25 Zero Cost Methods That Work",
     "price": 1499, "tags": ["passive income","side hustle","make money","digital download","financial freedom"],
     "file": "passive_income_zero_cost_guide.pdf", "desc": "25 proven passive income methods requiring $0 to start. Includes 90-day launch plan. Instant PDF download."},
    {"title": "Monthly Budget Planner PDF - Finance Tracker Printable",
     "price": 899,  "tags": ["budget planner","finance tracker","monthly budget","printable","digital download"],
     "file": "monthly_budget_planner.pdf", "desc": "Track income, expenses, savings goals, and debt payoff. 12-month system. Instant PDF download."},
    {"title": "100 Instagram Caption Templates - Social Media Content Pack",
     "price": 799,  "tags": ["instagram captions","social media templates","content creator","digital download","marketing"],
     "file": "100_instagram_captions.pdf", "desc": "100 fill-in-the-blank captions for every niche and mood. Hook formulas and CTA scripts included. Instant download."},
    {"title": "30-Day Social Media Content Calendar PDF - Post Ideas",
     "price": 999,  "tags": ["content calendar","social media planner","content ideas","digital download","instagram"],
     "file": "30_day_social_content_calendar.pdf", "desc": "30 days of done-for-you content ideas with hashtag banks. For Instagram, TikTok, LinkedIn, Twitter/X. Instant download."},
    {"title": "Daily Habit Tracker PDF - 30 Day Reset Printable",
     "price": 699,  "tags": ["habit tracker","daily habits","30 day challenge","printable","digital download"],
     "file": "daily_habit_tracker_30day.pdf", "desc": "Track up to 5 habits daily for 30 days. Mood tracking, weekly reviews, completion rates. Instant PDF download."},
    {"title": "Weekly Meal Prep Planner PDF - Grocery List & Macros",
     "price": 699,  "tags": ["meal prep planner","grocery list","meal planning","printable","digital download"],
     "file": "weekly_meal_prep_planner.pdf", "desc": "7-day meal planning with grocery lists, macro tracking, and 20+ recipe cards. Instant PDF download."},
    {"title": "Annual Business Plan Template PDF - One Page Plan",
     "price": 1499, "tags": ["business plan","startup template","annual planning","digital download","entrepreneur"],
     "file": "annual_business_plan_template.pdf", "desc": "Complete annual business plan with revenue breakdown, OKRs, risk register, and quarterly goals. Instant download."},
    {"title": "Content Creation Checklist PDF - 50 Posts Done Right",
     "price": 599,  "tags": ["content checklist","blogging tips","social media checklist","digital download","creator"],
     "file": "content_creation_checklist.pdf", "desc": "50-point checklist for blog posts, social media, email, and video content that converts and ranks. Instant download."},
]

def create_listing(product):
    if not API_KEY or not SHOP_ID:
        log.warning("Missing ETSY_API_KEY or ETSY_SHOP_ID")
        return None
    payload = {
        "quantity": 999, "title": product["title"],
        "description": product["desc"],
        "price": {"amount": product["price"], "divisor": 100, "currency_code": "USD"},
        "who_made": "i_did", "when_made": "2020_2025",
        "taxonomy_id": 2078, "tags": product["tags"][:13],
        "listing_type": "download", "is_digital": True,
        "should_auto_renew": True, "state": "draft"
    }
    r = requests.post(f"{BASE}/shops/{SHOP_ID}/listings",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload, timeout=15)
    if r.status_code == 201:
        data = r.json()
        log.info(f"✅ Created: {product['title'][:50]} → listing_id={data['listing_id']}")
        return data["listing_id"]
    else:
        log.error(f"❌ {product['title'][:40]}: {r.status_code} {r.text[:100]}")
        return None

if __name__ == "__main__":
    log.info(f"Creating {len(PRODUCTS)} Etsy listings...")
    created = 0
    for p in PRODUCTS:
        lid = create_listing(p)
        if lid: created += 1
        time.sleep(0.5)
    log.info(f"Done: {created}/{len(PRODUCTS)} listings created")
    log.info("NEXT: Go to etsy.com/your/shops/listings → activate each + upload PDF file")
