#!/usr/bin/env python3
"""
Etsy Digital Download Auto-Lister
Creates listings for all 10 digital products on Etsy
Etsy has 90M buyers - same products, massive audience
Uses Playwright browser automation
"""
import time, os, urllib.request
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip install playwright && playwright install chromium")
    from playwright.sync_api import sync_playwright

GITHUB_PDF_BASE = "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/data/kdp_books"

LISTINGS = [
    {
        "title": "90-Day Goal Planner Printable PDF - Undated Quarterly Planner Instant Download",
        "price": "7.99",
        "pdf": "90-Day_Goal_Planner.pdf",
        "desc": "Achieve your biggest goals with this beautiful 90-day goal planner. Undated so you can start any time. Includes daily/weekly planning pages, habit trackers, priority matrices, and monthly reviews. Instant download PDF - print at home or at your local print shop.",
        "tags": "goal planner,90 day planner,printable planner,digital planner,undated planner,quarterly planner,goal setting,productivity planner,instant download",
        "category": "Digital Downloads"
    },
    {
        "title": "Monthly Budget Planner Printable PDF - Finance Tracker Instant Download",
        "price": "7.99",
        "pdf": "Monthly_Budget_Planner_Finance_Tracker.pdf",
        "desc": "Take control of your finances with this comprehensive monthly budget planner. Track income, expenses, savings goals, and debt payoff all in one place. 12-month format. Instant download PDF.",
        "tags": "budget planner,monthly budget,finance tracker,printable budget,money planner,savings tracker,expense tracker,financial planner,instant download",
        "category": "Digital Downloads"
    },
    {
        "title": "Daily Habit Tracker Printable - 30 Day Reset Challenge PDF Instant Download",
        "price": "6.99",
        "pdf": "Daily_Habit_Tracker_30_Day_Reset.pdf",
        "desc": "Build lasting habits with this science-backed 30-day habit tracker. Track up to 10 habits daily with streak counters and weekly reflection prompts. Instant download PDF.",
        "tags": "habit tracker,daily habit,30 day challenge,printable tracker,habit journal,self improvement,routine planner,instant download",
        "category": "Digital Downloads"
    },
    {
        "title": "Weekly Meal Prep Planner Printable PDF - Grocery List Template Instant Download",
        "price": "6.99",
        "pdf": "Weekly_Meal_Prep_Planner.pdf",
        "desc": "Simplify your meal prep with this organized weekly planner. Includes meal planning grid, grocery list template, macro tracking, and prep schedule. Instant download PDF.",
        "tags": "meal planner,meal prep,weekly meal plan,grocery list,printable meal planner,nutrition tracker,food planner,instant download",
        "category": "Digital Downloads"
    },
    {
        "title": "Business Plan Template Printable PDF - Annual Business Planner Instant Download",
        "price": "8.99",
        "pdf": "Business_Plan_Template_Annual_Planner.pdf",
        "desc": "Professional business plan template for entrepreneurs. Covers vision, market analysis, revenue targets, marketing strategy, and quarterly milestones. 12-month planning format. Instant download PDF.",
        "tags": "business plan template,annual planner,business planner,entrepreneur planner,startup planner,small business,business planning,instant download",
        "category": "Digital Downloads"
    },
]

def download_pdfs(dl_dir):
    dl_dir.mkdir(exist_ok=True)
    print("Downloading PDFs from GitHub...")
    for listing in LISTINGS:
        fpath = dl_dir / listing["pdf"]
        if fpath.exists():
            print(f"  Have: {listing['pdf']}")
            continue
        try:
            urllib.request.urlretrieve(f"{GITHUB_PDF_BASE}/{listing['pdf']}", fpath)
            print(f"  Downloaded: {listing['pdf']}")
        except Exception as e:
            print(f"  Failed: {listing['pdf']}: {e}")

def create_listing(page, listing, pdf_path, idx, total):
    print(f"\n[{idx}/{total}] Creating Etsy listing: {listing['title'][:50]}...")
    
    page.goto("https://www.etsy.com/sell/", timeout=20000)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(2)
    
    # Navigate to create new listing
    page.goto("https://www.etsy.com/your/shops/me/tools/listings/create", timeout=20000)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(3)
    
    print(f"  Manual steps required on Etsy listing page:")
    print(f"  1. Select: Digital Download")
    print(f"  2. Title: {listing['title']}")
    print(f"  3. Price: ${listing['price']}")
    print(f"  4. Upload file: {pdf_path}")
    print(f"  5. Tags: {listing['tags'][:80]}")
    print(f"  6. Description: {listing['desc'][:100]}...")
    input("  Press ENTER after completing this listing...")
    return True

def run():
    print("=" * 55)
    print("  ETSY DIGITAL DOWNLOAD LISTER")
    print("  5 listings = $30-80/month (90M Etsy buyers)")
    print("=" * 55)
    
    dl_dir = Path.home() / "nysr-etsy-pdfs"
    download_pdfs(dl_dir)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto("https://etsy.com/signin")
        print("\nLog in to your Etsy seller account")
        input("Logged in? Press ENTER...")
        
        for i, listing in enumerate(LISTINGS, 1):
            pdf_path = dl_dir / listing["pdf"]
            create_listing(page, listing, pdf_path, i, len(LISTINGS))
        
        print(f"\n{len(LISTINGS)} Etsy listings created!")
        input("Press ENTER to close...")
        browser.close()

if __name__ == "__main__":
    run()
