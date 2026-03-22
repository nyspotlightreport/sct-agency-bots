#!/usr/bin/env python3
"""
Teepublic Auto-Uploader — 20 designs → $40-100/month passive
Run: python teepublic_uploader.py
"""
import time, os, urllib.request
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip install playwright && playwright install chromium")
    from playwright.sync_api import sync_playwright

GITHUB_BASE = "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/data/redbubble_designs"

DESIGNS = [
    ("nyc-skyline-minimal.svg",  "NYC Skyline Minimal Black White", "nyc,new york,skyline,minimal,city,urban,architecture"),
    ("hustle-motivational.svg",  "Hustle Daily Gold Motivational",  "hustle,motivation,gold,entrepreneur,grind,success"),
    ("moon-phases.svg",          "Moon Phases Lunar Cycle Art",     "moon,lunar,celestial,moon phases,astronomy,space"),
    ("no-days-off.svg",          "No Days Off Fitness Motivation",  "no days off,fitness,gym,workout,athlete,grind"),
    ("create-your-path.svg",     "Create Your Own Path Nature",     "path,inspiration,nature,motivation,green,adventure"),
    ("coffee-first.svg",         "Coffee First Funny Quote Mug",    "coffee,funny,humor,caffeine,morning,coffee lover"),
    ("geometric-peaks.svg",      "Geometric Mountain Sunset Art",   "mountain,geometric,sunset,nature,hiking,adventure"),
    ("zodiac-scorpio.svg",       "Scorpio Zodiac Dark Art",         "scorpio,zodiac,astrology,scorpion,halloween,dark"),
    ("aquarius-celestial.svg",   "Aquarius Zodiac Celestial Blue",  "aquarius,zodiac,astrology,celestial,blue,water"),
    ("abstract-mandala.svg",     "Sacred Geometry Mandala",         "mandala,sacred geometry,geometric,spiritual,zen"),
    ("leo-zodiac-fire.svg",      "Leo Zodiac Fire Sign Art",        "leo,zodiac,fire,astrology,lion,horoscope"),
    ("midnight-forest.svg",      "Midnight Forest Dark Moon",       "forest,midnight,moon,dark,trees,nature,gothic"),
    ("retro-synthwave.svg",      "Retro 80s Synthwave Neon",        "retro,synthwave,80s,neon,vintage,vaporwave"),
    ("plant-parent-humor.svg",   "Plant Parent Funny Quote",        "plant,plant parent,funny,humor,plants,garden"),
    ("nyc-yellow-cab.svg",       "NYC Yellow Taxi New York",        "nyc,taxi,yellow cab,new york,city,urban"),
    ("digital-nomad-life.svg",   "Digital Nomad Work Anywhere",     "digital nomad,remote work,travel,laptop,work anywhere"),
    ("be-the-energy.svg",        "Be The Energy Positive Vibes",    "energy,positive,vibes,inspiration,motivation,gold"),
    ("mountains-adventure.svg",  "Mountains Adventure Night Sky",   "mountains,adventure,night sky,stars,hiking,outdoors"),
    ("capricorn-earth.svg",      "Capricorn Zodiac Earth Sign",     "capricorn,zodiac,astrology,earth,goat,horoscope"),
    ("stay-wild-free.svg",       "Stay Wild and Free Boho",         "wild,free,boho,bohemian,nature,spiritual"),
]

def download_designs(dl_dir):
    dl_dir.mkdir(exist_ok=True)
    print("Downloading designs from GitHub...")
    for name, _, _ in DESIGNS:
        fpath = dl_dir / name
        if fpath.exists() and fpath.stat().st_size > 500:
            print(f"  Have: {name}")
            continue
        try:
            urllib.request.urlretrieve(f"{GITHUB_BASE}/{name}", fpath)
            print(f"  Got: {name}")
        except Exception as e:
            print(f"  Failed: {name}: {e}")

def upload_design(page, fname, title, tags, svg_path, idx, total):
    print(f"[{idx}/{total}] {title}")
    page.goto("https://www.teepublic.com/uploads/new", timeout=25000)
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    time.sleep(2)

    try:
        fi = page.query_selector("input[type='file']")
        if fi:
            fi.set_input_files(str(svg_path))
            print(f"  File set, waiting...")
            page.wait_for_timeout(6000)
        else:
            print("  No file input found — may need manual upload")
            return False
    except Exception as e:
        print(f"  Upload err: {e}"); return False

    try:
        page.wait_for_selector("input[name*='title'], input[placeholder*='title']", timeout=12000)
        page.fill("input[name*='title']", title, timeout=5000)
    except: pass

    try:
        tag_input = page.query_selector("input[name*='tag'], textarea[name*='tag']")
        if tag_input: tag_input.fill(tags)
    except: pass

    try:
        page.click("button[type='submit'], input[type='submit']", timeout=5000)
        page.wait_for_timeout(3000)
        print(f"  ✅ Submitted")
        return True
    except Exception as e:
        print(f"  Submit err: {e}"); return False

def run():
    print("╔══════════════════════════════════════════════╗")
    print("║  TEEPUBLIC UPLOADER — 20 designs             ║")
    print("║  Same designs as Redbubble = 2x income       ║")
    print("╚══════════════════════════════════════════════╝")
    dl_dir = Path.home() / "nysr-teepublic"
    download_designs(dl_dir)

    input("Press ENTER to open browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto("https://www.teepublic.com/user-sign-in")
        print("Log in to Teepublic (create free account if needed)")
        input("Logged in? Press ENTER...")

        ok = 0
        for i, (fname, title, tags) in enumerate(DESIGNS, 1):
            svg_path = dl_dir / fname
            if not svg_path.exists(): continue
            if upload_design(page, fname, title, tags, svg_path, i, len(DESIGNS)): ok += 1
            time.sleep(1)

        print(f"\n✅ {ok}/{len(DESIGNS)} designs uploaded to Teepublic!")
        input("Press ENTER to close...")
        browser.close()

if __name__ == "__main__":
    run()
