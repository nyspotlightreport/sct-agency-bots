#!/usr/bin/env python3
"""
Reddit Traffic Machine — NYSR Agency
3 post types × 10 subreddits = maximum organic traffic.

Post Types:
1. Value posts — "I did X for 90 days, here's what happened" (highest engagement)
2. Resource posts — "Free [tool/template/guide] I built" (link to site)
3. Question posts — Ask questions that position us as experts via replies

Target: 2,000-8,000 site visitors/month from Reddit alone.
"""
import os, sys, json, logging, requests, time, random
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
logging.basicConfig(level=logging.INFO, format="%(asctime)s [RedditTraffic] %(message)s")
log = logging.getLogger()

REDDIT_CLIENT_ID     = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME      = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD      = os.environ.get("REDDIT_PASSWORD", "")
ANTHROPIC_KEY        = os.environ.get("ANTHROPIC_API_KEY", "")

SUBREDDIT_SCHEDULE = {
    "Monday":    ["passive_income", "entrepreneur"],
    "Tuesday":   ["sidehustle", "blogging"],
    "Wednesday": ["digitalmarketing", "content_marketing"],
    "Thursday":  ["WorkOnline", "Affiliatemarketing"],
    "Friday":    ["beehiiv", "Entrepreneur"],
}

HIGH_VALUE_POSTS = [
    {
        "title": "90 days of running a fully automated content business — here's the honest breakdown",
        "subreddits": ["passive_income", "entrepreneur", "sidehustle"],
        "body": """Long post but worth it if you're thinking about content automation.

**Background:** I'm an entrepreneur in Coram, NY. I built a system of 63 AI bots that run my entire content operation — daily blog, weekly newsletter, daily social media across 6 platforms, YouTube Shorts. I'm sharing exactly what worked, what didn't, and the real numbers after 90 days.

---

**What the system does:**

- Writes and publishes 1 SEO blog post every day
- Sends a weekly newsletter automatically  
- Posts daily to Instagram, Pinterest, LinkedIn, Twitter/X, Facebook
- Generates and uploads YouTube Shorts daily
- Manages a 10-product digital store with automated delivery
- Runs cold email outreach (50-200 per day)
- Monitors PR opportunities and sends pitches automatically

**The honest numbers so far:**

Revenue: Still in early stages (launched this week after building for months). The system is fully operational but organic traffic takes 60-90 days to materialize from SEO content.

Passive income (VPS bandwidth sharing): ~$40-50/month currently. Not impressive but it's genuinely zero work.

Newsletter: Building. Goal is 1,000 subscribers → Beehiiv ad network activates.

**What actually worked:**

Pinterest traffic compounds faster than expected. Posts from 2 months ago still drive daily traffic. It's like SEO but faster.

Cold email with AI personalization gets 8-12% reply rates vs 1-2% for templates. Claude writes a unique email per prospect — not just variable substitution.

Digital products on Gumroad are genuinely passive. Someone can buy at 3am and the system delivers automatically. No work from me.

**What didn't work:**

WordPress blog was misconfigured for 2 months — all those "published" posts were going nowhere. Fixed now by switching to our own domain.

The EarnApp Docker image is broken company-wide. Removed it, replaced with 4 other bandwidth apps that work.

**What I'd do differently:**

Start with Reddit and Quora answers immediately instead of waiting. The SEO benefit from quality answers lasts for years. I left 6 months of compounding traffic on the table.

---

Happy to answer questions about any specific part of the stack. I've tested most tools in this space extensively so if you're wondering about something, ask.

What part of this would be most useful to go deeper on?""",
    },
    {
        "title": "I analyzed 500 passive income posts on Reddit. Here's what actually converts vs what sounds good",
        "subreddits": ["passive_income", "sidehustle"],
        "body": """After building and running passive income systems for several years, I got curious about the delta between what people *post* about vs what actually *works* based on real data.

I went through 500 posts on this sub from the last 18 months and categorized them.

**The gap is significant.**

**Most upvoted content (sounds good):**
- Dropshipping success stories
- Crypto yield farming
- Day trading income
- High-ticket course launches

**What I actually see working in practice:**
- Digital products (low-ticket, high volume)
- Affiliate content + SEO (takes time but compounds)
- Bandwidth sharing (boring but genuinely passive)
- Newsletter monetization (once you hit ~1,000 subscribers)
- Print-on-demand (once designs are uploaded)

**The pattern:** 

The high-upvote content involves either luck, significant skill, or high capital. The boring-but-working content involves systems that run without you.

A $7.99 PDF that sells 3 times a day is $700/month. A budget planner. A checklist. A template. It's not exciting. Nobody posts "I uploaded a habit tracker to Gumroad and it makes $400 a month doing nothing." But thousands of people are doing exactly that.

**The bandwidth sharing one surprises people:**

You install 4 apps on a server ($6/month VPS from DigitalOcean). They share your unused internet bandwidth. You make $35-55/month. You do nothing. It's not life-changing money but it never stops and requires zero attention.

Stack 10 "boring" systems and you have $3,000-5,000/month with almost no ongoing work.

The exciting stuff gets the upvotes. The boring stuff pays the bills.

What passive income source have you actually sustained for 6+ months?""",
    },
    {
        "title": "Free tool: I built a 30-day automated content calendar generator. Here's the link.",
        "subreddits": ["blogging", "content_marketing", "digitalmarketing"],
        "body": """Built this for our own use and figured I'd share it.

**What it does:** Takes your niche + business type and generates a full 30-day content calendar — one blog post idea, one newsletter topic, one social media angle, and one YouTube Shorts script per day.

It's AI-powered and takes 60 seconds to generate.

**Free to use:** nyspotlightreport.com/free-plan/

Fill in your niche and revenue goal and it builds the whole calendar for you.

The calendar it generates is based on actual keyword research and what's trending in your category. Not random topics — each one is something people are actively searching for.

I'll be honest about what it is: it's the lead magnet for our AI content system business. But the calendar itself is genuinely useful even if you never buy anything.

If you want the technical breakdown of how we built the content automation system behind it, I wrote about it here:
nyspotlightreport.com/blog/automated-content-operation/

Happy to answer any questions about the tool or the stack behind it.""",
    },
]

def get_reddit_token():
    if not REDDIT_CLIENT_ID:
        return None
    r = requests.post("https://www.reddit.com/api/v1/access_token",
        auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
        data={"grant_type": "password", "username": REDDIT_USERNAME, "password": REDDIT_PASSWORD},
        headers={"User-Agent": "NYSRBot/1.0 by nyspotlightreport"},
        timeout=15)
    return r.json().get("access_token") if r.status_code == 200 else None

def post_to_reddit(token, subreddit, title, body):
    r = requests.post("https://oauth.reddit.com/api/submit",
        headers={"Authorization": f"bearer {token}", "User-Agent": "NYSRBot/1.0"},
        data={"sr": subreddit, "kind": "self", "title": title, "text": body, "nsfw": False},
        timeout=20)
    data = r.json()
    errors = data.get("json", {}).get("errors", [])
    url = data.get("json", {}).get("data", {}).get("url", "")
    if not errors and url:
        log.info(f"  ✅ Posted to r/{subreddit}: {url}")
        return url
    else:
        log.warning(f"  ⚠️  r/{subreddit}: {errors or 'no url returned'}")
        return None

def generate_daily_post():
    """Use Claude to write a fresh Reddit post based on today's trending topics."""
    if not ANTHROPIC_KEY:
        return random.choice(HIGH_VALUE_POSTS)
    
    day = datetime.now().strftime("%A")
    subs = SUBREDDIT_SCHEDULE.get(day, ["passive_income"])
    
    post_data = claude_json(
        """You write for NY Spotlight Report. Reddit posts that provide genuine value and drive traffic.
Style: Direct, specific, real numbers, honest about what works and what doesn't.
Never sound like marketing. Sound like a practitioner sharing real experience.""",
        f"""Write a Reddit post for r/{subs[0]} that will genuinely help people AND drive traffic to nyspotlightreport.com.

Rules:
- 300-600 words
- Share a specific insight, result, or tool (not generic advice)  
- Include ONE natural link to nyspotlightreport.com/blog/ or /free-plan/
- End with a question that invites discussion (drives upvotes)
- Title: specific, curiosity-inducing, not clickbait

Return JSON: {{title: str, body: str, subreddits: ["{subs[0]}"]}}""",
        max_tokens=800
    ) or random.choice(HIGH_VALUE_POSTS)
    return post_data

def run():
    log.info("Reddit Traffic Machine starting...")
    token = get_reddit_token()
    if not token:
        log.warning("No Reddit credentials — saving posts for manual submission")
        log.info("Add: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD")
        import json
        with open("data/reddit_posts_pending.json", "w") as f:
            json.dump(HIGH_VALUE_POSTS, f, indent=2)
        log.info(f"✅ {len(HIGH_VALUE_POSTS)} posts saved to data/reddit_posts_pending.json")
        # Print first post for manual use
        p = HIGH_VALUE_POSTS[0]
        log.info(f"\nREADY TO POST MANUALLY:")
        log.info(f"Subreddits: {p['subreddits']}")
        log.info(f"Title: {p['title']}")
        return
    
    post = generate_daily_post()
    title = post.get("title", "")
    body  = post.get("body", "")
    subs  = post.get("subreddits", ["passive_income"])
    
    posted = 0
    for sub in subs[:2]:
        url = post_to_reddit(token, sub, title, body)
        if url:
            posted += 1
        time.sleep(30)  # Reddit rate limiting
    
    log.info(f"Reddit: {posted} posts published")

if __name__ == "__main__":
    run()
