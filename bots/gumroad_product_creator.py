#!/usr/bin/env python3
"""
Gumroad Auto-Lister — ProFlow Digital
Creates all 20 products on Gumroad using existing API credentials
Runs once to populate; can re-run to sync/update
"""
import os, requests, json, time, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("GumroadBot")

TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN","iWDmua3jwn2oZDPa0nOUnvACE5lyeELc-uA3GwTxjmM")
BASE  = "https://api.gumroad.com/v2"

PRODUCTS = [
    {"name":"90-Day Goal Planner","price":1299,"desc":"A structured 90-day goal planner to help you set, track, and crush quarterly goals. Includes daily/weekly/monthly review sections, habit trackers, and priority matrices. Instant PDF download.","tags":["planner","goals","productivity"]},
    {"name":"30-Day Social Media Content Calendar","price":999,"desc":"30 days of planned social media content with done-for-you post ideas, hashtag sets, and engagement prompts for Instagram, TikTok, LinkedIn, and Twitter/X. Never run out of content again.","tags":["social media","content calendar","marketing"]},
    {"name":"50 ChatGPT Prompts for Business","price":799,"desc":"50 battle-tested ChatGPT prompts for entrepreneurs — covering marketing copy, email sequences, sales scripts, market research, and content creation. Copy-paste and go.","tags":["chatgpt","prompts","AI","business"]},
    {"name":"Monthly Budget Planner","price":899,"desc":"A comprehensive monthly budget planner covering income tracking, expense categories, savings goals, debt payoff tracker, and net worth calculator. Built for real results.","tags":["budget","finance","money","planner"]},
    {"name":"Weekly Meal Prep Planner","price":699,"desc":"7-day meal planning template with grocery lists, macro tracking, prep schedules, and 20+ fill-in recipe cards. Save time and money every week.","tags":["meal prep","nutrition","health","planner"]},
    {"name":"Daily Habit Tracker — 30 Day Reset","price":699,"desc":"30-day habit tracker designed around behavioral science. Track up to 10 habits daily with streak counters, reflection prompts, and a month-end review system.","tags":["habits","tracker","self improvement"]},
    {"name":"Annual Business Plan Template","price":1499,"desc":"A full 12-month business planning template covering vision, revenue targets, marketing strategy, team structure, quarterly milestones, and KPIs. Built for solo operators and small teams.","tags":["business plan","entrepreneur","strategy"]},
    {"name":"Content Creation Checklist — 50 Posts Done Right","price":599,"desc":"A 50-item content checklist covering every format: blog posts, reels, carousels, YouTube videos, newsletters, and podcasts. Never publish weak content again.","tags":["content creation","checklist","social media"]},
    {"name":"100 Instagram Caption Templates","price":799,"desc":"100 done-for-you Instagram caption templates for lifestyle, business, motivation, humor, and promotional content. Fill in the blanks and post. Works for any niche.","tags":["instagram","captions","social media","templates"]},
    {"name":"Email Marketing Swipe File — 50 Emails","price":1299,"desc":"50 proven email templates covering welcome sequences, promotional campaigns, abandoned cart recovery, re-engagement, and affiliate promotions. Works with any email platform.","tags":["email marketing","templates","copywriting"]},
    {"name":"Freelancer Invoice + Contract Template Pack","price":599,"desc":"A pack of 5 professional invoice templates and 1 freelance service agreement — ready to customize in Word or Google Docs. Get paid faster and look more professional.","tags":["freelancer","invoice","contract","templates"]},
    {"name":"30-Day Fitness Planner","price":799,"desc":"30 structured days of workout planning with exercise logs, rest day guidance, progress tracking, and nutrition notes. Works for all fitness levels.","tags":["fitness","workout","planner","health"]},
    {"name":"Notion Productivity Dashboard Template","price":999,"desc":"A complete Notion workspace template with project management, goal tracking, daily journal, reading list, habit tracker, and content calendar — all linked together.","tags":["notion","productivity","dashboard","template"]},
    {"name":"Client Onboarding Toolkit","price":1199,"desc":"Everything you need to onboard new clients professionally: welcome packet template, questionnaire, project brief, contract checklist, and communication SOP. For freelancers and agencies.","tags":["freelancer","agency","client","onboarding"]},
    {"name":"YouTube Channel Planning Kit","price":899,"desc":"Plan, launch, and grow a YouTube channel with this complete kit: niche research template, content calendar, video script framework, thumbnail checklist, and monetization tracker.","tags":["youtube","content","creator","planning"]},
    {"name":"Side Hustle Launch Checklist","price":699,"desc":"A 90-item checklist covering every step of launching a side hustle — from idea validation to first sale. Covers digital products, services, affiliate marketing, and ecommerce.","tags":["side hustle","entrepreneur","business","checklist"]},
    {"name":"AI Prompt Pack — Marketing Edition (100 Prompts)","price":999,"desc":"100 AI prompts for marketing professionals covering ad copy, SEO meta descriptions, email subject lines, social captions, brand voice guidelines, and launch copy. Works with ChatGPT, Claude, and Gemini.","tags":["AI prompts","marketing","chatgpt","copywriting"]},
    {"name":"Weekly Review & Planning Workbook","price":799,"desc":"A structured weekly planning workbook with Monday planning, Friday review, win logging, priorities matrix, energy management, and next-week preview. Build the habit in 30 days.","tags":["planning","productivity","workbook","weekly review"]},
    {"name":"Financial Freedom Tracker — 12-Month Edition","price":1199,"desc":"Track your path to financial freedom with monthly P&L, net worth progress, investment tracker, debt snowball calculator, income diversification planner, and 12-month milestone map.","tags":["finance","freedom","tracker","money","investing"]},
    {"name":"Digital Creator Starter Kit","price":1499,"desc":"Everything a new digital creator needs: niche selection guide, platform comparison matrix, content system template, email list setup guide, first product launch checklist, and revenue tracker. Start your creator business right.","tags":["creator","digital products","business","starter kit"]},
]

def list_existing():
    r = requests.get(f"{BASE}/products", params={"access_token":TOKEN})
    if r.ok:
        return {p['name']:p['id'] for p in r.json().get('products',[])}
    return {}

def create_product(p):
    data = {
        "access_token": TOKEN,
        "name": p['name'],
        "price": p['price'],
        "description": p['desc'],
        "published": True,
        "require_shipping": False,
    }
    r = requests.post(f"{BASE}/products", data=data)
    if r.ok:
        pid = r.json().get('product',{}).get('id','')
        log.info(f"✅ Created: {p['name']} (${p['price']/100:.2f}) → ID: {pid}")
        return pid
    else:
        log.error(f"❌ Failed: {p['name']} → {r.text[:200]}")
        return None

def run():
    log.info("🚀 Gumroad Product Creator Starting...")
    existing = list_existing()
    log.info(f"Existing products: {len(existing)}")
    created = 0
    for p in PRODUCTS:
        if p['name'] in existing:
            log.info(f"⏭️  Already exists: {p['name']}")
            continue
        pid = create_product(p)
        if pid: created += 1
        time.sleep(1)
    log.info(f"✅ Done. Created {created} new products.")
    # Save summary
    all_prods = list_existing()
    with open("data/gumroad_products.json","w") as f:
        json.dump(all_prods, f, indent=2)
    log.info(f"📄 Product list saved to data/gumroad_products.json")

if __name__ == "__main__":
    run()
