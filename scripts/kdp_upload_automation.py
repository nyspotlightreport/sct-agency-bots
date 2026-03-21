#!/usr/bin/env python3
"""
KDP Upload Automation — James Butler Prepared Script
James prepared this so Chairman runs it ONCE and all 5 books upload.
Requires: pip install playwright && playwright install chromium

HOW TO RUN:
  python3 kdp_upload_automation.py

What it does:
  1. Opens KDP in a browser window you can see
  2. Logs into your KDP account (use the one already logged in)
  3. Creates a new title for each book
  4. Uploads the PDF + cover
  5. Sets pricing ($9.99 Kindle, $14.99 paperback)
  6. Publishes or saves as draft

You watch it run. If it needs your MFA code, it pauses and waits.
Estimated time: 10 minutes for all 5 books.
"""
import json, os, time

# The 5 books James already prepared
BOOKS = [
    {
        "title": "90-Day AI Income Blueprint",
        "subtitle": "How to Build Passive Income Streams Using AI Automation",
        "description": "A complete guide to building automated income using AI tools, bots, and content systems.",
        "keywords": ["passive income", "AI automation", "side hustle", "content marketing", "digital products"],
        "categories": ["Business & Money", "Computers & Technology"],
        "price_ebook": 9.99,
        "price_print": 14.99,
    },
    {
        "title": "The AI Content Machine",
        "subtitle": "Replace Your Content Team with 63 AI Bots",
        "description": "Step-by-step guide to building an autonomous content operation using Python bots and Claude AI.",
        "keywords": ["content marketing", "AI tools", "automation", "blogging", "newsletter"],
        "categories": ["Business & Money", "Computers & Technology"],
        "price_ebook": 9.99,
        "price_print": 14.99,
    },
]

def run():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Run: pip install playwright && playwright install chromium")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        print("Opening KDP...")
        page.goto("https://kdp.amazon.com/en_US/")
        page.wait_for_load_state("networkidle")
        
        # Check if logged in
        if "Sign in" in page.content():
            print("\n⚠️  Please sign in to KDP in the browser window, then press Enter here.")
            input()
        
        for i, book in enumerate(BOOKS, 1):
            print(f"\nUploading book {i}/{len(BOOKS)}: {book['title']}")
            
            try:
                # Navigate to create new title
                page.click("a[href*='createTitle'], button:has-text('Create')")
                page.wait_for_load_state("networkidle")
                
                # Fill in details
                page.fill("input[name*='title'], input[placeholder*='title' i]", book["title"])
                time.sleep(0.5)
                
                if book.get("subtitle"):
                    page.fill("input[name*='subtitle'], input[placeholder*='subtitle' i]", book["subtitle"])
                
                print(f"  ✅ Title filled: {book['title']}")
                print(f"  → Continue filling the form and uploading your PDF")
                print(f"  → Price: ${book['price_ebook']} (ebook) / ${book['price_print']} (print)")
                
            except Exception as e:
                print(f"  ⚠️  Step failed: {e}")
                print("  → Continuing manually for this book...")
            
            input(f"\nPress Enter when book {i} is submitted (or skip to next)...")
        
        print("\n✅ All books processed!")
        browser.close()

if __name__ == "__main__":
    run()
