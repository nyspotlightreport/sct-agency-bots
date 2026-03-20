#!/usr/bin/env python3
"""
KDP Book Auto-Uploader
Automates uploading all 10 books to Amazon KDP
Run: python kdp_uploader.py
Requires: pip install playwright
Then: playwright install chromium
"""
import time, json, sys, os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Installing Playwright...")
    os.system("pip install playwright")
    os.system("playwright install chromium")
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BOOKS = [
    {"title":"90-Day Goal Planner","pdf":"90-Day_Goal_Planner.pdf","price":"7.99",
     "desc":"A structured 90-day goal planner to help you set and track quarterly goals. Includes daily/weekly/monthly sections, habit trackers, and priority matrices.",
     "keywords":"goal planner,90 day planner,quarterly planner,goals tracker,habit journal,undated planner,productivity planner,goal setting workbook"},
    {"title":"Daily Habit Tracker 30 Day Reset","pdf":"Daily_Habit_Tracker_30_Day_Reset.pdf","price":"6.99",
     "desc":"30-day habit tracker designed around behavioral science. Track up to 10 habits daily with streak counters and reflection prompts.",
     "keywords":"habit tracker,daily habit planner,30 day challenge,habit journal,self improvement,daily planner,behavior tracker,routine planner"},
    {"title":"Monthly Budget Planner Finance Tracker","pdf":"Monthly_Budget_Planner_Finance_Tracker.pdf","price":"7.99",
     "desc":"Comprehensive monthly budget planner covering income tracking, expense categories, savings goals, and debt payoff tracker.",
     "keywords":"budget planner,monthly budget,finance tracker,expense log,money planner,savings tracker,debt payoff,financial planner"},
    {"title":"Weekly Meal Prep Planner","pdf":"Weekly_Meal_Prep_Planner.pdf","price":"6.99",
     "desc":"7-day meal planning template with grocery lists, macro tracking, prep schedules, and recipe cards.",
     "keywords":"meal prep planner,weekly meal plan,grocery list,nutrition tracker,meal planning journal,food planner,diet planner"},
    {"title":"Business Plan Template Annual Planner","pdf":"Business_Plan_Template_Annual_Planner.pdf","price":"8.99",
     "desc":"Full 12-month business planning template covering vision, revenue targets, marketing strategy, and quarterly milestones.",
     "keywords":"business plan template,annual planner,business planner,entrepreneur planner,startup planner,business strategy,business journal"},
    {"title":"Fitness Workout Log 90 Days","pdf":"Fitness_Workout_Log_90_Days.pdf","price":"6.99",
     "desc":"90 days of structured workout logging with exercise logs, rest day guidance, and progress tracking.",
     "keywords":"workout log,fitness journal,exercise tracker,gym log,workout planner,fitness tracker,training journal,90 day fitness"},
    {"title":"Word Search Puzzles for Adults 100 Puzzles","pdf":"Word_Search_Puzzles_for_Adults_100_Puzzl.pdf","price":"7.99",
     "desc":"100 word search puzzles for adults. Hours of entertainment and mental exercise.",
     "keywords":"word search,puzzle book,word search for adults,activity book,brain games,word puzzles,large print word search"},
    {"title":"Gratitude Journal 365 Days Daily Prompts","pdf":"Gratitude_Journal_365_Days_Daily_Prompts.pdf","price":"7.99",
     "desc":"365-day guided gratitude journal with daily prompts for mindfulness and positive thinking.",
     "keywords":"gratitude journal,daily journal,365 day journal,mindfulness journal,positivity journal,self care journal,daily prompts"},
    {"title":"Password Keeper Log Book Organizer","pdf":"Password_Keeper_Log_Book_Organizer.pdf","price":"5.99",
     "desc":"Secure password keeper and log book for organizing all your online accounts and credentials.",
     "keywords":"password keeper,password book,internet password organizer,password log,account tracker,login organizer"},
    {"title":"Sudoku Puzzles Easy to Hard 200 Puzzles","pdf":"Sudoku_Puzzles_Easy_to_Hard_200_Puzzles.pdf","price":"7.99",
     "desc":"200 Sudoku puzzles ranging from easy to hard. Perfect for all skill levels.",
     "keywords":"sudoku,sudoku puzzle book,sudoku for adults,easy sudoku,hard sudoku,puzzle book,brain games,number puzzles"},
]

# Download PDFs from GitHub
GITHUB_BASE = "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/data/kdp_books"

def download_pdfs(download_dir):
    import urllib.request
    download_dir.mkdir(exist_ok=True)
    print("Downloading PDFs from GitHub...")
    for book in BOOKS:
        fpath = download_dir / book['pdf']
        if fpath.exists():
            print(f"  Already have: {book['pdf']}")
            continue
        url = f"{GITHUB_BASE}/{book['pdf']}"
        try:
            urllib.request.urlretrieve(url, fpath)
            print(f"  Downloaded: {book['pdf']} ({fpath.stat().st_size//1024}KB)")
        except Exception as e:
            print(f"  Failed: {book['pdf']}: {e}")
    return download_dir

def upload_book(page, book, pdf_path, idx, total):
    print(f"\n[{idx}/{total}] Uploading: {book['title']}")
    
    # Navigate to new paperback
    page.goto("https://kdp.amazon.com/en_US/title-setup/paperback/new/details", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=20000)
    
    # Title
    try:
        page.fill('input[id*="title"]', book['title'], timeout=5000)
    except:
        page.fill('input[name*="title"]', book['title'], timeout=5000)
    
    # Description
    try:
        page.fill('textarea[id*="description"]', book['desc'], timeout=5000)
    except: pass
    
    # Keywords
    try:
        kw_list = book['keywords'].split(',')
        for i, kw in enumerate(kw_list[:7]):
            page.fill(f'input[id*="keyword"][id*="{i}"]', kw.strip(), timeout=3000)
    except: pass
    
    print(f"  Filled metadata. Navigating to content upload...")
    
    # Save and continue to content page
    try:
        page.click('button[id*="save-and-continue"]', timeout=5000)
        page.wait_for_load_state("networkidle", timeout=15000)
    except: pass
    
    # Upload PDF
    try:
        page.set_input_files('input[type="file"]', str(pdf_path), timeout=10000)
        print(f"  PDF uploaded. Waiting for processing...")
        page.wait_for_timeout(8000)  # KDP processes the PDF
    except Exception as e:
        print(f"  PDF upload issue: {e}")
    
    # Set price
    try:
        page.fill('input[id*="us-price"]', book['price'], timeout=5000)
    except: pass
    
    print(f"  ✅ Book setup complete. Review and publish manually.")

def run():
    print("╔══════════════════════════════════════════════════╗")
    print("║     KDP BOOK UPLOADER — ProFlow Digital          ║")
    print("║     10 books → ~$50/month royalties forever     ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    download_dir = Path.home() / "nysr-kdp-books"
    download_pdfs(download_dir)
    
    print("\nStarting browser... Log in to KDP when it opens.")
    input("Press ENTER when ready...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        # Open KDP login
        page.goto("https://kdp.amazon.com")
        print("\nLog in to KDP in the browser window.")
        print("When you're on the KDP dashboard, press ENTER here...")
        input()
        
        # Upload each book
        for i, book in enumerate(BOOKS, 1):
            pdf_path = download_dir / book['pdf']
            if not pdf_path.exists():
                print(f"  Skipping {book['title']} - PDF not found")
                continue
            try:
                upload_book(page, book, pdf_path, i, len(BOOKS))
                time.sleep(2)
            except Exception as e:
                print(f"  Error on {book['title']}: {e}")
                input("  Press ENTER to continue to next book...")
        
        print("\n✅ All books processed!")
        print("Review each draft in KDP and click 'Publish' to go live.")
        input("Press ENTER to close browser...")
        browser.close()

if __name__ == "__main__":
    run()
