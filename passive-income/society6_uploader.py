#!/usr/bin/env python3
"""
Society6 Auto-Uploader — premium art prints
Same designs → premium buyers → higher royalty per sale
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
    ("nyc-skyline-minimal.svg",  "NYC Skyline Minimal",      "new york, city, skyline, architecture, urban, minimal, black and white"),
    ("moon-phases.svg",          "Lunar Cycle Moon Phases",  "moon, lunar, astronomy, celestial, minimal, space, night"),
    ("geometric-peaks.svg",      "Geometric Mountain Peaks", "mountain, geometric, nature, sunset, landscape, travel, adventure"),
    ("abstract-mandala.svg",     "Sacred Geometry Mandala",  "mandala, sacred geometry, spiritual, meditation, geometric, pattern"),
    ("midnight-forest.svg",      "Midnight Forest",          "forest, trees, moon, night, dark, nature, mysterious"),
    ("retro-synthwave.svg",      "Synthwave 80s Retro",      "retro, 80s, synthwave, neon, pop art, colorful, vintage"),
    ("aquarius-celestial.svg",   "Aquarius Celestial",       "aquarius, zodiac, astrology, celestial, blue, mystical"),
    ("mountains-adventure.svg",  "Adventure Mountains",      "mountains, stars, night sky, adventure, nature, outdoors, travel"),
    ("be-the-energy.svg",        "Be The Energy",            "motivational, energy, positive, inspirational, gold, typography"),
    ("stay-wild-free.svg",       "Stay Wild and Free",       "boho, nature, wild, free, bohemian, inspirational, typography"),
]

def run():
    print("╔══════════════════════════════════════════════╗")
    print("║  SOCIETY6 UPLOADER — premium art prints      ║")
    print("╚══════════════════════════════════════════════╝")
    dl_dir = Path.home() / "nysr-society6"
    dl_dir.mkdir(exist_ok=True)

    for name, _, _ in DESIGNS:
        fpath = dl_dir / name
        if not fpath.exists():
            try:
                urllib.request.urlretrieve(f"{GITHUB_BASE}/{name}", fpath)
                print(f"  Downloaded: {name}")
            except Exception as e:
                print(f"  Failed: {name}")

    input("Press ENTER to open browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        page.goto("https://society6.com/studio")
        print("Log in or create a free Society6 account")
        print("Then navigate to: society6.com/studio")
        input("Ready? Press ENTER...")

        for i, (fname, title, tags) in enumerate(DESIGNS, 1):
            svg_path = dl_dir / fname
            if not svg_path.exists(): continue
            print(f"[{i}/{len(DESIGNS)}] Upload: {title}")
            print(f"  File: {svg_path}")
            print(f"  Title: {title}")
            print(f"  Tags: {tags}")
            input("  Manually upload this file, then press ENTER for next...")

        print(f"\n✅ All {len(DESIGNS)} designs processed!")
        print("Society6 pays 10% royalty on all products automatically.")
        input("Press ENTER to close...")
        browser.close()

if __name__ == "__main__":
    run()
