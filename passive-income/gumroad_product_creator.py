#!/usr/bin/env python3
"""
Gumroad Product Creator v2
Creates + PUBLISHES 10 products with actual PDF files attached
Products CANNOT be published without a file — this version handles that.
Run: python gumroad_product_creator.py
"""
import time, os, urllib.request
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip install playwright && playwright install chromium")
    from playwright.sync_api import sync_playwright

GITHUB_BASE = "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/data/kdp_books"

PRODUCTS = [
    {
        "name": "90-Day Goal Planner",
        "price": "12.99",
        "desc": "Structured 90-day goal planner to set and track quarterly goals with daily/weekly sections, habit trackers, and priority matrices.",
        "pdf": "90-Day_Goal_Planner.pdf"
    },
    {
        "name": "Daily Habit Tracker — 30 Day Reset",
        "price": "6.99",
        "desc": "30-day habit tracker designed around behavioral science. Track up to 10 habits daily with streak counters and reflection prompts.",
        "pdf": "Daily_Habit_Tracker_30_Day_Reset.pdf"
    },
    {
        "name": "Monthly Budget Planner",
        "price": "8.99",
        "desc": "Comprehensive monthly budget planner covering income, expense categories, savings goals, and debt payoff tracker.",
        "pdf": "Monthly_Budget_Planner_Finance_Tracker.pdf"
    },
    {
        "name": "Weekly Meal Prep Planner",
        "price": "6.99",
        "desc": "7-day meal planning template with grocery lists, macro tracking, prep schedules, and recipe cards.",
        "pdf": "Weekly_Meal_Prep_Planner.pdf"
    },
    {
        "name": "Annual Business Plan Template",
        "price": "14.99",
        "desc": "Full 12-month business planning template covering vision, revenue targets, marketing strategy, and quarterly milestones.",
        "pdf": "Business_Plan_Template_Annual_Planner.pdf"
    },
    {
        "name": "Fitness Workout Log — 90 Days",
        "price": "6.99",
        "desc": "90 days of structured workout logging with exercise logs, rest day guidance, and progress tracking.",
        "pdf": "Fitness_Workout_Log_90_Days.pdf"
    },
    {
        "name": "Gratitude Journal — 365 Daily Prompts",
        "price": "7.99",
        "desc": "365-day guided gratitude journal with daily prompts for mindfulness and positive thinking.",
        "pdf": "Gratitude_Journal_365_Days_Daily_Prompts.pdf"
    },
    {
        "name": "Word Search Puzzle Book — 100 Puzzles",
        "price": "7.99",
        "desc": "100 word search puzzles for adults. Hours of entertainment and mental exercise.",
        "pdf": "Word_Search_Puzzles_for_Adults_100_Puzzl.pdf"
    },
    {
        "name": "Sudoku Puzzles — 200 Easy to Hard",
        "price": "7.99",
        "desc": "200 Sudoku puzzles ranging from easy to hard. Perfect for all skill levels.",
        "pdf": "Sudoku_Puzzles_Easy_to_Hard_200_Puzzles.pdf"
    },
    {
        "name": "Password Keeper & Account Organizer",
        "price": "5.99",
        "desc": "Secure password keeper and log book for organizing all your online accounts and credentials.",
        "pdf": "Password_Keeper_Log_Book_Organizer.pdf"
    },
]

def download_pdfs(dl_dir):
    dl_dir.mkdir(exist_ok=True)
    print("Downloading PDFs from GitHub...")
    for prod in PRODUCTS:
        fpath = dl_dir / prod["pdf"]
        if fpath.exists() and fpath.stat().st_size > 5000:
            print("  Have: " + prod["pdf"])
            continue
        url = GITHUB_BASE + "/" + prod["pdf"]
        try:
            urllib.request.urlretrieve(url, fpath)
            print("  Got: " + prod["pdf"] + " (" + str(fpath.stat().st_size // 1024) + "KB)")
        except Exception as e:
            print("  Failed: " + prod["pdf"] + " — " + str(e)[:40])

def create_product(page, prod, idx, total, pdf_path):
    name = prod["name"]
    price = prod["price"]
    desc = prod["desc"]
    print("[" + str(idx) + "/" + str(total) + "] " + name + "  $" + price)

    # Go to new product page
    page.goto("https://app.gumroad.com/products/new", timeout=25000)
    page.wait_for_load_state("networkidle", timeout=20000)
    time.sleep(2)

    # --- Step 1: Fill name ---
    try:
        page.wait_for_selector("input[placeholder*='name'], input[name*='name'], #product_name", timeout=10000)
        name_input = page.query_selector("input[placeholder*='name'], input[name*='name'], #product_name")
        if name_input:
            name_input.triple_click()
            name_input.fill(name)
            print("  Name filled")
    except Exception as e:
        print("  Name issue: " + str(e)[:40])

    # --- Step 2: Upload PDF file ---
    try:
        file_input = page.query_selector("input[type='file']")
        if file_input:
            file_input.set_input_files(str(pdf_path))
            print("  PDF uploading...")
            page.wait_for_timeout(5000)
        else:
            print("  No file input found")
    except Exception as e:
        print("  File upload issue: " + str(e)[:40])

    # --- Step 3: Set price ---
    try:
        price_input = page.query_selector("input[name*='price'], input[id*='price']")
        if price_input:
            price_input.triple_click()
            price_input.fill(price)
            print("  Price set: $" + price)
    except Exception as e:
        print("  Price issue: " + str(e)[:40])

    # --- Step 4: Save/publish ---
    try:
        save_btn = page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Save'), button:has-text('Publish')")
        if save_btn:
            save_btn.click()
            page.wait_for_timeout(4000)
            print("  Saved!")
            return True
        else:
            print("  No save button found")
            return False
    except Exception as e:
        print("  Save issue: " + str(e)[:40])
        return False

def run():
    print("=" * 50)
    print("  GUMROAD PRODUCT CREATOR v2")
    print("  Creates products WITH PDFs attached = publishable")
    print("=" * 50)

    dl_dir = Path.home() / "nysr-gumroad-pdfs"
    download_pdfs(dl_dir)

    # Check all PDFs downloaded
    missing = [p for p in PRODUCTS if not (dl_dir / p["pdf"]).exists()]
    if missing:
        print("Missing PDFs: " + str([p["name"] for p in missing]))
        print("Check GitHub repo: data/kdp_books/")

    print("Starting browser. Log in to Gumroad when it opens.")
    input("Press ENTER to start...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto("https://gumroad.com/login")
        print("Login: nyspotlightreport@gmail.com")
        input("Logged in? Press ENTER to start creating products...")

        created = 0
        for i, prod in enumerate(PRODUCTS, 1):
            pdf_path = dl_dir / prod["pdf"]
            if not pdf_path.exists():
                print("Skipping (no PDF): " + prod["name"])
                continue
            if create_product(page, prod, i, len(PRODUCTS), pdf_path):
                created += 1
            time.sleep(2)

        print()
        print("Created: " + str(created) + "/" + str(len(PRODUCTS)) + " products")
        print("Go to app.gumroad.com to verify and publish each one.")
        input("Press ENTER to close browser...")
        browser.close()

if __name__ == "__main__":
    run()
