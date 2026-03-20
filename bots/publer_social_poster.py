#!/usr/bin/env python3
"""
Publer Social Auto-Poster
Posts affiliate content snippets to all connected social accounts daily
Platforms: Twitter, LinkedIn, Facebook, Pinterest, Instagram
Publer API: https://publer.io/docs/api
"""
import os, requests, json, datetime, random

PUBLER_KEY = os.environ.get("PUBLER_API_KEY","")
PUBLER_WS  = os.environ.get("PUBLER_WORKSPACE_ID","")
BASE_URL   = "https://app.publer.io/hooks/media"

SITE = "https://nyspotlightreport.com"

POST_TEMPLATES = [
    {
        "text": "The apps that pay you passive income just for having internet:\n\n✅ EarnApp\n✅ Honeygain\n\n$60-100/month. Zero effort after install.\n\n{site}/best-passive-income-apps-2026",
        "hashtags": "#passiveincome #sidehustle #makemoneyonline"
    },
    {
        "text": "If you're not building a newsletter in 2026, you're leaving money on the table.\n\nBeehiiv pays you from day 1 via their ad network — even with 100 subscribers.\n\n{site}/how-to-start-newsletter-make-money",
        "hashtags": "#newsletter #beehiiv #emailmarketing"
    },
    {
        "text": "The $500/month passive income formula:\n\n1. Bandwidth sharing: $60\n2. Digital products: $150\n3. Affiliate commissions: $150\n4. Print-on-demand: $80\n5. KDP books: $60\n\nAll running 24/7. {site}",
        "hashtags": "#passiveincome #sidehustle2026 #financialfreedom"
    },
    {
        "text": "Print-on-demand = upload design once, earn forever.\n\nRedbubble + Teepublic + Society6 = 3 platforms, same design, 3x income.\n\n{site}/best-print-on-demand-sites-2026",
        "hashtags": "#printondemand #redbubble #passiveincome"
    },
    {
        "text": "Amazon KDP lets you publish planners, journals, and puzzle books with ZERO upfront cost.\n\nRoyalties hit your account every month. For life.\n\n{site}/amazon-kdp-guide-2026",
        "hashtags": "#amazonKDP #selfpublishing #passiveincome"
    },
    {
        "text": "Affiliate marketing programs paying $100-1000 per referral:\n\n💰 HubSpot: up to $1,000\n💰 WP Engine: $200+\n💰 Ahrefs: $200\n💰 Kinsta: 10% recurring\n\n{site}/best-affiliate-programs",
        "hashtags": "#affiliatemarketing #makemoneyonline #blogging"
    },
    {
        "text": "Digital products have 90%+ margins.\n\nCreate a Canva template once. Sell it on Gumroad forever.\n\nNo shipping. No inventory. Pure profit.\n\n{site}/how-to-sell-digital-products-2026",
        "hashtags": "#digitalproducts #gumroad #etsy #passiveincome"
    },
]

def get_workspaces():
    r = requests.get("https://app.publer.io/api/v1/workspaces",
        headers={"Authorization": f"Bearer {PUBLER_KEY}"}, timeout=10)
    if r.ok: return r.json().get("workspaces", [])
    print(f"Workspaces error: {r.status_code} {r.text[:100]}")
    return []

def get_accounts():
    r = requests.get("https://app.publer.io/api/v1/accounts",
        headers={"Authorization": f"Bearer {PUBLER_KEY}"}, timeout=10)
    if r.ok: return r.json().get("accounts", [])
    print(f"Accounts error: {r.status_code} {r.text[:100]}")
    return []

def post_content(text, account_ids):
    full_text = text.replace("{site}", SITE)
    
    payload = {
        "post": {
            "text": full_text,
            "account_ids": account_ids,
            "status": "published",
        }
    }
    
    r = requests.post("https://app.publer.io/api/v1/posts",
        headers={"Authorization": f"Bearer {PUBLER_KEY}", "Content-Type": "application/json"},
        json=payload, timeout=15)
    
    print(f"Post result: {r.status_code}")
    if r.ok:
        print(f"Posted: {full_text[:80]}...")
    else:
        print(f"Error: {r.text[:200]}")
    return r.ok

def run():
    if not PUBLER_KEY:
        print("No PUBLER_API_KEY set"); return
    
    # Get connected accounts
    accounts = get_accounts()
    if not accounts:
        print("No social accounts found in Publer")
        print("Connect accounts at: app.publer.io/settings/accounts")
        return
    
    account_ids = [a["id"] for a in accounts]
    print(f"Found {len(accounts)} connected accounts: {[a.get('type','?') for a in accounts]}")
    
    # Pick today's post
    today_num = datetime.date.today().timetuple().tm_yday
    template = POST_TEMPLATES[today_num % len(POST_TEMPLATES)]
    text = template["text"] + "\n\n" + template["hashtags"]
    
    success = post_content(text, account_ids)
    if success:
        print("✅ Daily social post published!")
    else:
        print("❌ Post failed")

if __name__ == "__main__":
    run()
