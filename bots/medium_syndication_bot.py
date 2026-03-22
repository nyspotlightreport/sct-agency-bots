#!/usr/bin/env python3
"""
Medium Auto-Syndication Bot
Republishes affiliate content to Medium for additional traffic + authority
Medium Partner Program adds reading time revenue
canonical URL points back to our site (SEO safe)
"""
import os, requests, json, datetime

MEDIUM_TOKEN = os.environ.get("MEDIUM_INTEGRATION_TOKEN","")
SITE = "https://nyspotlightreport.com"

ARTICLES = [
    {
        "title": "I Built a $500/Month Passive Income System in 90 Days — Here's Every Step",
        "slug": "passive-income-online-2026",
        "tags": ["passive income", "side hustle", "make money online", "financial independence"],
        "content": """## The System That Changed My Income

After years of chasing passive income myths, I finally built a system that actually works.
Here's the exact combination that generates over $500/month with zero daily work required.

## Step 1: Bandwidth Sharing ($60/month)

[EarnApp](https://earnapp.com/i/NYSR) and [Honeygain](https://r.honeygain.me/NYSPOTLIGHT) pay you
to share your unused internet bandwidth. Install both, leave running. Your first payment arrives within 30 days.
No referrals needed. No tasks. Pure passive.

## Step 2: Digital Products ($150/month)

Templates, planners, and prompt packs on Gumroad. Create once, sell forever. I used AI tools
to create 20 products in a weekend. Now they sell while I sleep.

## Step 3: Affiliate Commissions ($200/month)

[HubSpot's affiliate program](https://hubspot.com/?via=nysr) pays up to $1,000 per sale.
[Ahrefs](https://ahrefs.com/?ref=nysr) pays $200. [Kinsta](https://kinsta.com/?ref=nysr) pays 10% recurring.
One honest recommendation per month compounds significantly.

## Step 4: Print-on-Demand ($90/month)

20 designs on Redbubble, Teepublic, and Society6. Same design, three platforms,
three income streams. Total upload time per design: 15 minutes once.

## The Key Insight

None of these streams is impressive alone. Combined and automated, they compound.
Month 3 looks nothing like month 1.

*Originally published at [NY Spotlight Report]({site}/{slug}).*"""
    },
    {
        "title": "The Newsletter Platform That Pays You From Your First Subscriber",
        "slug": "how-to-start-newsletter-make-money",
        "tags": ["newsletter", "email marketing", "beehiiv", "passive income"],
        "content": """## Stop Paying to Send Emails

Most newsletter platforms cost $29-99/month. [Beehiiv](https://beehiiv.com/?via=nysr) pays you.

Their built-in ad network monetizes your list automatically. Even at 100 subscribers, their ad
placements generate real revenue. No minimum. No waiting. Write your first issue and earn from it.

## Why This Changes the Math

Traditional model: Spend money → build list → maybe monetize eventually.
Beehiiv model: Start free → earn from first issue → compound as you grow.

Their 25% recurring affiliate commission also means recommending it to others generates
ongoing monthly income.

## The Growth Mechanism

Beehiiv's referral program rewards your readers for referring friends. Your list grows
itself with incentives you don't have to manage. The growth compounds without paid advertising.

## Bottom Line

[Start free on Beehiiv](https://beehiiv.com/?via=nysr). Write one honest weekly email about
something you know. The platform handles monetization. You focus on the audience.

*Originally published at [NY Spotlight Report]({site}/{slug}).*"""
    },
]

def get_medium_user_id():
    r = requests.get("https://api.medium.com/v1/me",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}", "Content-Type": "application/json"},
        timeout=10)
    if r.ok:
        return r.json()["data"]["id"]
    print(f"Medium auth error: {r.status_code} {r.text[:100]}")
    return None

def publish_to_medium(user_id, article, site):
    content = article["content"].format(site=site, slug=article["slug"])
    payload = {
        "title": article["title"],
        "contentFormat": "markdown",
        "content": content,
        "tags": article["tags"],
        "canonicalUrl": f"{site}/{article['slug']}",
        "publishStatus": "public"
    }
    r = requests.post(f"https://api.medium.com/v1/users/{user_id}/posts",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}", "Content-Type": "application/json"},
        json=payload, timeout=20)
    if r.ok:
        url = r.json()["data"]["url"]
        print(f"✅ Published to Medium: {url}")
        return True
    print(f"❌ Failed: {r.status_code} {r.text[:150]}")
    return False

def run():
    if not MEDIUM_TOKEN:
        print("No MEDIUM_INTEGRATION_TOKEN set.")
        print("Steps to get one:")
        print("1. Go to medium.com/me/settings")
        print("2. Security and Apps → Integration tokens")
        print("3. Generate token, add as MEDIUM_INTEGRATION_TOKEN in GitHub Secrets")
        return

    user_id = get_medium_user_id()
    if not user_id: return

    today = datetime.date.today().timetuple().tm_yday
    article = ARTICLES[today % len(ARTICLES)]

    print(f"Publishing to Medium: {article['title']}")
    publish_to_medium(user_id, article, SITE)

if __name__ == "__main__":
    run()
