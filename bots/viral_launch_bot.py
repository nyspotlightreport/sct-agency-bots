#!/usr/bin/env python3
"""
Viral Launch Bot — NYSR Agency
Executes platform-specific viral content strategies.

Platforms:
1. Hacker News "Show HN" — dev/entrepreneur audience, can hit front page
2. Twitter/X viral thread — builds following + drives traffic
3. LinkedIn viral post — B2B audience, high engagement

"Show HN: I built 63 bots to run my entire business automatically"
This story has massive viral potential — it's the perfect HN post.
"""
import os, sys, logging, json
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s, u, **k): return ""

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ViralLaunch] %(message)s")
log = logging.getLogger()

HN_POST = {
    "title": "Show HN: I built 63 bots to automate my entire content business",
    "url": "https://nyspotlightreport.com/blog/automated-content-operation/",
    "text": """I've spent the last 6 months building a system of 63 AI bots that run my entire content marketing and passive income operation without any ongoing work from me.

Here's what it does:

**Content:**
- Publishes 1 SEO blog post daily (Claude API writes it, GitHub Actions deploys it)
- Sends weekly newsletter via Beehiiv automatically
- Posts to 6 social platforms daily via Publer
- Generates and uploads YouTube Shorts daily

**Revenue:**
- 10-product digital store on Gumroad with automated delivery webhooks
- Affiliate link injector scans every published post and adds contextual links
- VPS running 4 bandwidth sharing apps (Honeygain, Traffmonetizer, etc.) passively

**Sales:**
- Apollo API pulls 200 verified prospects/day
- Claude writes a unique personalized email per person (not templates)
- HubSpot logs everything, 3-email sequence over 7 days
- Inbox agent reads replies and responds autonomously using Claude

**Infrastructure:**
- 52 GitHub Actions workflows (all the "employees")
- Netlify for the site (instant deploys on every git push)
- Everything runs for ~$6/month VPS + Claude API costs ($1-2/day)

The stack is mostly Python, GitHub Actions YAML, and Anthropic's API.

Happy to go deep on any specific component. The architecture writeup is at the link above.

What questions do you have?""",
    "submit_url": "https://news.ycombinator.com/submit"
}

TWITTER_VIRAL_THREAD = """I built 63 AI bots that run my entire content business.

Here's the full breakdown: 🧵 (1/12)

---

2/ The problem I was solving:

Content marketing = 20+ hours/week.
Content staff = $3,000-6,000/month.
Most people quit by month 2.

I wanted a system that ran without me.

---

3/ The blog engine:

Every morning, a bot:
→ Finds trending keywords in my niche
→ Writes a 1,800-word SEO post using Claude API
→ Publishes to my site automatically
→ Creates a newsletter issue from the content

I've published 180+ posts this way.

---

4/ The social media layer:

Each blog post generates:
→ Twitter thread
→ LinkedIn article
→ Instagram caption + hashtags
→ Pinterest pin
→ Facebook post
→ YouTube Shorts script

Scheduled via Publer. 5 platforms posting daily.

---

5/ The revenue layer:

10 digital products on Gumroad.
Automated delivery via webhook.
Affiliate links auto-injected into every post.
VPS running bandwidth sharing apps 24/7.

None of this needs attention after setup.

---

6/ The sales engine:

Apollo API → 200 verified prospects/day
Claude API → unique email per person (not templates)
3-email sequence → 7 day window
Inbox agent → reads and replies autonomously

Current reply rate: 8-12% (vs 1-2% for templates)

---

7/ The cost:

VPS: $6/month
Claude API: ~$2/day
Everything else: free tier tools

Total: ~$66/month in recurring costs.

---

8/ The honest numbers:

Revenue so far: $0 (launched this week after 6 months building)

But the infrastructure is solid. SEO takes 60-90 days.
Cold email is generating conversations now.

---

9/ What took the longest:

Figuring out that WordPress had 0 sites attached (all blog posts going nowhere for months)

The EarnApp Docker image being dead company-wide

Google OAuth consent screen having a bug that blocked YouTube uploads

---

10/ What I'd do differently:

Start posting on Reddit and Quora immediately instead of waiting.
The SEO benefit from quality answers lasts years.
I left 6 months of compounding traffic on the table.

---

11/ The architecture:

→ GitHub Actions = the "employees" (52 active workflows)
→ Claude API = the brain
→ Netlify = deployment
→ Apollo = lead data
→ Everything else = free tier tools

---

12/ Full writeup + free 30-day content plan:

nyspotlightreport.com/free-plan/

The system generates a custom content plan for your specific niche in 60 seconds.

What would you want to automate first?"""

LINKEDIN_VIRAL_POST = """I spent 6 months building 63 AI bots that run my entire content business.

Here's what they do every day while I sleep:

→ Publish 1 SEO blog post (Claude writes it)
→ Send weekly newsletter to subscribers
→ Post to 6 social platforms daily
→ Generate + upload YouTube Shorts
→ Send 200 personalized cold emails
→ Read and reply to inbound inquiries

Total monthly cost: ~$66.

Compare that to:
→ Content writer: $3,000-6,000/month
→ Social media manager: $2,000-4,000/month  
→ Email marketer: $2,500-5,000/month
→ VA team: $2,000-3,000/month

= $9,500-18,000/month for humans to do what the bots do.

Is the quality perfect? No. Is it consistent and scalable? Yes.

The real insight: most content doesn't need to be perfect. It needs to be consistent. Consistent compounds. Perfect gets abandoned.

I wrote up the full technical breakdown here:
nyspotlightreport.com/blog/automated-content-operation/

What part of this would you want to apply to your business?"""

if __name__ == "__main__":
    log.info("Viral Launch Assets Ready\n")
    
    log.info("HACKER NEWS:")
    log.info(f"Title: {HN_POST['title']}")
    log.info(f"Submit at: {HN_POST['submit_url']}")
    log.info("Best time: Tuesday-Thursday, 8-11 AM EST")
    
    log.info("\nTWITTER THREAD:")
    log.info(f"Length: {len(TWITTER_VIRAL_THREAD.split('---'))} tweets")
    log.info("Post as thread, not individual tweets")
    
    log.info("\nLINKEDIN:")
    log.info(f"Length: {len(LINKEDIN_VIRAL_POST.split(chr(10)))} lines")
    log.info("Best engagement: Tuesday-Thursday 8-10 AM")
    
    import json
    with open("data/viral_launch_assets.json", "w") as f:
        json.dump({
            "hacker_news": HN_POST,
            "twitter_thread": TWITTER_VIRAL_THREAD,
            "linkedin": LINKEDIN_VIRAL_POST
        }, f, indent=2)
    log.info("\n✅ All viral assets saved to data/viral_launch_assets.json")
