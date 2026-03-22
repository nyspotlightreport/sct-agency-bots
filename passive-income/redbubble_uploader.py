#!/usr/bin/env python3
"""
Redbubble Design Auto-Uploader
Automates uploading 10 SVG designs to Redbubble
Run: python redbubble_uploader.py
"""
import time, os, urllib.request
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip install playwright && playwright install chromium")
    from playwright.sync_api import sync_playwright

DESIGNS = [
    {"name":"nyc-skyline-minimal.svg",  "title":"NYC Skyline Minimal Art",
     "tags":"New York City, NYC, skyline, minimalist, city, urban, black white"},
    {"name":"hustle-motivational.svg",  "title":"Hustle Daily Motivational Quote",
     "tags":"hustle, motivational, quote, entrepreneur, grind, success, gold"},
    {"name":"moon-phases.svg",          "title":"Moon Phases Celestial Art",
     "tags":"moon phases, celestial, lunar, moon, space, astronomy, minimal"},
    {"name":"no-days-off.svg",          "title":"No Days Off Fitness Motivation",
     "tags":"no days off, fitness, gym, workout, motivation, athletic, hustle"},
    {"name":"create-your-path.svg",     "title":"Create Your Own Path Inspirational",
     "tags":"create your path, inspirational, nature, forest, motivation, adventure"},
    {"name":"coffee-first.svg",         "title":"Coffee First Everything Else Waits",
     "tags":"coffee, coffee lover, funny, humor, coffee quote, morning, caffeine"},
    {"name":"geometric-peaks.svg",      "title":"Geometric Mountain Peaks Sunset",
     "tags":"mountain, geometric, sunset, nature, hiking, outdoors, travel, adventure"},
    {"name":"zodiac-scorpio.svg",       "title":"Scorpio Zodiac Astrology Art",
     "tags":"scorpio, zodiac, astrology, horoscope, scorpion, october november"},
    {"name":"aquarius-celestial.svg",   "title":"Aquarius Zodiac Celestial Art",
     "tags":"aquarius, zodiac, astrology, horoscope, celestial, january february"},
    {"name":"abstract-mandala.svg",     "title":"Sacred Geometry Mandala Art",
     "tags":"mandala, sacred geometry, geometric, spiritual, meditation, pattern"},
]

GITHUB_BASE = "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/data/redbubble_designs"

def download_designs(dl_dir):
    dl_dir.mkdir(exist_ok=True)
    print("Downloading designs from GitHub...")
    for d in DESIGNS:
        fpath = dl_dir / d['name']
        if fpath.exists() and fpath.stat().st_size > 500:
            print(f"  Have: {d['name']}")
            continue
        try:
            urllib.request.urlretrieve(f"{GITHUB_BASE}/{d['name']}", fpath)
            print(f"  Downloaded: {d['name']} ({fpath.stat().st_size}B)")
        except Exception as e:
            print(f"  Failed: {d['name']}: {e}")

def upload_design(page, design, svg_path, idx, total):
    print(f"\n[{idx}/{total}] Uploading: {design['title']}")
    
    page.goto("https://www.redbubble.com/portfolio/images/new", timeout=20000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    
    # Upload file
    try:
        file_input = page.query_selector('input[type="file"]')
        if file_input:
            file_input.set_input_files(str(svg_path))
            print(f"  File set. Waiting for upload...")
            page.wait_for_timeout(5000)
        else:
            print(f"  File input not found - manual upload needed")
            return False
    except Exception as e:
        print(f"  Upload error: {e}")
        return False
    
    # Wait for title field
    try:
        page.wait_for_selector('input[name="work[title]"]', timeout=15000)
        page.fill('input[name="work[title]"]', design['title'])
    except:
        try:
            page.fill('input[id*="title"]', design['title'], timeout=5000)
        except:
            print("  Title field not found")
    
    # Tags
    try:
        tag_input = page.query_selector('input[name*="tag"], input[placeholder*="tag"], textarea[name*="tag"]')
        if tag_input:
            tag_input.fill(design['tags'])
    except: pass
    
    # Enable all products
    try:
        # Check all product checkboxes
        checkboxes = page.query_selector_all('input[type="checkbox"]')
        for cb in checkboxes[:20]:
            if not cb.is_checked():
                cb.check()
    except: pass
    
    # Save
    try:
        page.click('input[type="submit"], button[type="submit"]', timeout=5000)
        page.wait_for_timeout(3000)
        print(f"  ✅ Submitted: {design['title']}")
        return True
    except Exception as e:
        print(f"  Submit error: {e}")
        return False

def run():
    print("╔══════════════════════════════════════════════════╗")
    print("║   REDBUBBLE DESIGN UPLOADER — ProFlow Digital   ║")
    print("║   10 designs → ~$40-80/month royalties          ║")
    print("╚══════════════════════════════════════════════════╝")
    
    dl_dir = Path.home() / "nysr-redbubble-designs"
    download_designs(dl_dir)
    
    print("\nStarting browser. Log in to Redbubble when it opens.")
    input("Press ENTER when ready...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto("https://www.redbubble.com/auth/login")
        print("\nLog in to Redbubble: nysr101 / nyspotlightreport@gmail.com")
        input("Logged in? Press ENTER...")
        
        uploaded = 0
        for i, design in enumerate(DESIGNS, 1):
            svg_path = dl_dir / design['name']
            if not svg_path.exists():
                print(f"  Missing: {design['name']}")
                continue
            ok = upload_design(page, design, svg_path, i, len(DESIGNS))
            if ok: uploaded += 1
            time.sleep(1)
        
        print(f"\n✅ Uploaded {uploaded}/{len(DESIGNS)} designs!")
        print("Earnings start within 24-48 hours of going live.")
        input("Press ENTER to close browser...")
        browser.close()

if __name__ == "__main__":
    run()
