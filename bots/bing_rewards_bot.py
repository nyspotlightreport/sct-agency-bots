#!/usr/bin/env python3
"""
Bing Rewards Auto-Bot — Daily Microsoft Rewards automation
Earns ~$5-15/month in gift cards/PayPal on autopilot
Searches 30 terms on Bing (PC + Mobile) to max out daily points
"""
import os, time, random, logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("BingBot")

MS_EMAIL = os.environ.get("MS_REWARDS_EMAIL", os.environ.get("GMAIL_USER",""))
MS_PASS  = os.environ.get("MS_REWARDS_PASS", "")

SEARCH_TERMS = [
    "how to make passive income online 2026","best AI tools for entrepreneurs","ChatGPT prompts for business",
    "digital products to sell online","Gumroad vs Payhip comparison","how to start a newsletter 2026",
    "best affiliate programs high commission","print on demand profit guide","YouTube automation faceless channel",
    "KDP low content books that sell","sweepstakes strategy win more","DePIN crypto passive income",
    "Honeygain vs EarnApp review 2026","n8n automation tutorial","Beehiiv newsletter monetization",
    "best free APIs for developers","stock photography that sells","how to flip websites for profit",
    "micro SaaS ideas 2026","AI generated music royalties","Notion template business income",
    "Amazon KDP royalty calculator","Reddit passive income strategies","dropshipping automation tools",
    "best dividend stocks 2026","real estate crowdfunding platforms","Upwork freelance tips 2026",
    "content calendar template free","email list growth strategies","social media monetization guide",
]

def run_searches(page, terms, delay=2):
    for term in terms:
        try:
            page.goto(f"https://www.bing.com/search?q={term.replace(' ','+')}")
            page.wait_for_timeout(delay * 1000)
            log.info(f"  Searched: {term[:40]}")
        except Exception as e:
            log.warning(f"  Search failed: {e}")

def run():
    if not MS_EMAIL or not MS_PASS:
        log.warning("MS_REWARDS_EMAIL and MS_REWARDS_PASS not set — skipping Bing bot")
        return
    with sync_playwright() as pw:
        # PC searches
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
        )
        page = ctx.new_page()
        # Login
        page.goto("https://login.microsoftonline.com/")
        page.fill('input[type="email"]', MS_EMAIL)
        page.click('input[type="submit"]')
        page.wait_for_timeout(1000)
        page.fill('input[type="password"]', MS_PASS)
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)
        log.info("🖥️  Running PC searches...")
        run_searches(page, SEARCH_TERMS[:30])
        browser.close()
        # Mobile searches  
        browser2 = pw.chromium.launch(headless=True)
        ctx2 = browser2.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36",
            viewport={"width":390,"height":844}
        )
        page2 = ctx2.new_page()
        page2.goto("https://www.bing.com/")
        log.info("📱 Running Mobile searches...")
        run_searches(page2, SEARCH_TERMS[:20])
        browser2.close()
        log.info("✅ Bing Rewards complete — points earned!")

if __name__ == "__main__":
    run()
