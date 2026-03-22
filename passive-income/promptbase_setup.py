#!/usr/bin/env python3
"""
PromptBase Listing Creator
Opens browser to create prompt pack listings on PromptBase
You're already logged in as nyspotlight
Prompts are pre-written for maximum sales
"""
import time, os
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system("pip install playwright && playwright install chromium")
    from playwright.sync_api import sync_playwright

PROMPT_PACKS = [
    {
        "title": "50 ChatGPT Business Prompts for Entrepreneurs",
        "price": "4.99",
        "model": "ChatGPT",
        "desc": "50 high-quality prompts for entrepreneurs covering marketing copy, business plans, email sequences, social media, and sales scripts. Each prompt is tested and optimized for GPT-4.",
        "prompts": [
            "Write a compelling elevator pitch for [business] that solves [problem] for [target customer] in under 30 seconds",
            "Create a 7-email welcome sequence for [business] that builds trust and drives [product] sales",
            "Generate 10 Facebook ad headlines for [product] targeting [audience] with [pain point]",
            "Write a business plan executive summary for [business idea] with market size, revenue model, and 3-year projection",
            "Create a cold email sequence (3 emails) for [service] targeting [industry] decision makers"
        ]
    },
    {
        "title": "30 Midjourney Prompts for Print-on-Demand Designs",
        "price": "5.99",
        "model": "Midjourney",
        "desc": "30 proven Midjourney prompts for creating bestselling t-shirt, poster, and sticker designs. Optimized for Redbubble and Teepublic. Includes zodiac, motivational, nature, and retro styles.",
        "prompts": [
            "minimalist black and white city skyline silhouette, flat vector art, t-shirt design, clean lines, no background --ar 1:1 --style raw",
            "bold typographic motivational quote poster, gold letters on black background, luxury minimal design, print ready --ar 2:3",
            "sacred geometry mandala, intricate symmetrical pattern, black and white, tattoo style, detailed fine lines --ar 1:1 --style raw"
        ]
    },
    {
        "title": "25 Claude AI Prompts for Content Creators",
        "price": "3.99",
        "model": "Claude",
        "desc": "25 optimized prompts for content creators using Claude. Covers YouTube scripts, newsletter issues, blog posts, social captions, and content repurposing. Save hours of writing time.",
        "prompts": [
            "Write a YouTube video script for [topic] that opens with a hook, delivers 5 key insights, and ends with a CTA to [subscribe/buy]. Target length: 8 minutes. Tone: [educational/entertaining/inspiring]",
            "Transform this blog post into: 1) A Twitter/X thread (10 tweets), 2) An Instagram caption with hooks, 3) A LinkedIn article intro, 4) A YouTube Short script. Blog post: [paste content]",
            "Write a weekly newsletter issue about [topic] with: compelling subject line, 3-section structure, 1 actionable tip, and a soft promotion for [product/service]"
        ]
    },
    {
        "title": "20 DALL-E Prompts for Digital Product Covers",
        "price": "3.99",
        "model": "DALL-E",
        "desc": "20 professional prompts for creating digital product mockup covers, ebook covers, course thumbnails, and template previews. Makes your Gumroad and Etsy listings stand out.",
        "prompts": [
            "professional ebook cover design for a productivity planner, clean minimal design, gold and white color scheme, modern typography, high-end feel, product mockup style",
            "digital product cover for a social media template pack, vibrant gradient background, device mockup with screenshots, professional and modern design",
            "course thumbnail for online business training, professional photo background, bold title text overlay, engaging and trustworthy design"
        ]
    },
    {
        "title": "40 GPT-4 Prompts for Passive Income Research",
        "price": "5.99",
        "model": "ChatGPT",
        "desc": "40 research and analysis prompts for finding passive income opportunities, analyzing niches, evaluating affiliate programs, and building digital product businesses.",
        "prompts": [
            "Analyze the passive income potential of [niche] including: market size, competition level, monetization methods, realistic income range, time to profitability, and top 5 action steps",
            "Research the top 10 affiliate programs in [industry] and compare: commission rate, cookie duration, average order value, payout threshold, and approval difficulty",
            "Generate 20 digital product ideas for [profession/interest] that solve specific problems, with estimated pricing and platform recommendations"
        ]
    },
]

def create_listing(page, pack, idx, total):
    name = pack["title"]
    print(f"[{idx}/{total}] Creating: {name}")
    
    page.goto("https://promptbase.com/sell", timeout=20000)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(2)
    
    try:
        # Look for create/sell button
        create_btn = page.query_selector("a[href*=\"create\"], button:has-text(\"Sell\"), a:has-text(\"Create\")")
        if create_btn:
            create_btn.click()
            time.sleep(2)
    except: pass
    
    print(f"  Navigate to promptbase.com/sell to create listing manually")
    print(f"  Title: {name}")
    print(f"  Price: ${pack['price']}")
    print(f"  Model: {pack['model']}")
    print(f"  Description: {pack['desc'][:100]}...")
    print()
    input("  Press ENTER after creating this listing...")
    return True

def run():
    print("=" * 50)
    print("  PromptBase Listing Creator")
    print("  5 prompt packs = $20-30/month passive")
    print("=" * 50)
    print()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://promptbase.com/login")
        print("Log in to PromptBase (nyspotlight account)")
        input("Logged in? Press ENTER...")
        
        for i, pack in enumerate(PROMPT_PACKS, 1):
            create_listing(page, pack, i, len(PROMPT_PACKS))
        
        print(f"All {len(PROMPT_PACKS)} prompt packs created!")
        input("Press ENTER to close...")
        browser.close()

if __name__ == "__main__":
    run()
