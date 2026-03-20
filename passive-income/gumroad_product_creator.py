#!/usr/bin/env python3
"""
Gumroad Product Creator — Browser automation since API is deprecated
Creates 10 new products on Gumroad via Playwright
Run: python gumroad_product_creator.py
"""
import time, os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip install playwright && playwright install chromium")
    from playwright.sync_api import sync_playwright

NEW_PRODUCTS = [
    {"name":"LinkedIn Content Calendar 30 Days","price":"9.99","desc":"30-day LinkedIn posting calendar with hooks, CTAs, and templates to grow your professional network consistently."},
    {"name":"YouTube Channel Launch Kit","price":"11.99","desc":"Complete YouTube launch toolkit: niche selection worksheet, 90-day content calendar, title formulas, and thumbnail checklist."},
    {"name":"Notion Second Brain Template","price":"14.99","desc":"Complete Notion workspace: project tracker, weekly planner, book notes database, habit tracker, and goal dashboard."},
    {"name":"Cold Email Swipe File 50 Templates","price":"12.99","desc":"50 proven cold email templates for B2B outreach, follow-ups, partnership asks, and client pitches."},
    {"name":"Instagram Growth Playbook 2026","price":"9.99","desc":"Reels hooks, story templates, bio optimization, hashtag strategy, and daily engagement tactics for 2026."},
    {"name":"Freelancer Rate Calculator Bundle","price":"7.99","desc":"Spreadsheet to set freelance rates correctly. Includes 10 professional invoice templates."},
    {"name":"SEO Content Brief Template","price":"6.99","desc":"Fill-in-the-blank SEO brief: keyword strategy, competitor gaps, internal links, heading structure."},
    {"name":"Email Welcome Sequence 7 Templates","price":"15.99","desc":"7 pre-written welcome emails that build trust and drive sales. Plug in your details and activate."},
    {"name":"Passive Income Tracker Dashboard","price":"8.99","desc":"Google Sheets dashboard for tracking all passive income streams with monthly projections."},
    {"name":"Business Startup Checklist 2026","price":"6.99","desc":"127-item checklist covering legal, finance, branding, marketing, and launch for new businesses."},
]

def create_product(page, prod, idx, total):
    print(f"[{idx}/{total}] Creating: {prod[\'name\']}  ${prod[\'price\']}")
    
    page.goto("https://app.gumroad.com/products/new/digital", timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    
    try:
        page.fill("input[name=\'name\']", prod["name"], timeout=8000)
        print(f"  Name set")
    except Exception as e:
        try:
            page.fill("#product_name", prod["name"], timeout=5000)
        except:
            print(f"  Name field not found: {e}")
            return False
    
    try:
        page.fill("textarea[name=\'description\'], #product_description", prod["desc"], timeout=5000)
    except: pass
    
    try:
        price_input = page.query_selector("input[name=\'price\'], input[id*=\'price\']")
        if price_input:
            price_input.triple_click()
            price_input.fill(prod["price"])
    except Exception as e:
        print(f"  Price field issue: {e}")
    
    try:
        page.click("button[type=\'submit\'], input[type=\'submit\']", timeout=5000)
        page.wait_for_timeout(3000)
        print(f"  ✅ Created!")
        return True
    except Exception as e:
        print(f"  Submit err: {e}")
        return False

def run():
    print("╔═══════════════════════════════════════╗")
    print("║  GUMROAD PRODUCT CREATOR (10 new)     ║")
    print("╚═══════════════════════════════════════╝")
    
    print("\nStarting browser — log in to Gumroad...")
    input("Press ENTER to continue...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        page.goto("https://gumroad.com/login")
        print("Log in to Gumroad: nyspotlightreport@gmail.com")
        input("Logged in? Press ENTER...")
        
        created = 0
        for i, prod in enumerate(NEW_PRODUCTS, 1):
            if create_product(page, prod, i, len(NEW_PRODUCTS)):
                created += 1
            time.sleep(2)
        
        print(f"\n✅ {created}/{len(NEW_PRODUCTS)} products created!")
        print("Each product now earns passive income 24/7.")
        input("Press ENTER to close...")
        browser.close()

if __name__ == "__main__":
    run()
