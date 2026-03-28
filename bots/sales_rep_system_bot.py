#!/usr/bin/env python3
"""
Commission Sales Rep System — NYSR Agency
Manages commission-only sales reps for ProFlow AI & DFY Agency.
Commission structure: 30% recurring for life of client.
$97/mo plan = $29.10/mo per sale
$297/mo plan = $89.10/mo per sale
$997/mo plan = $299.10/mo per sale

Rep earns on every month client stays — truly passive for them.
"""
import os, requests, json, logging, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("SalesRepSystem")

# AG-NUCLEAR-GMAIL-ZERO-20260328: GMAIL_USER = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
# AG-NUCLEAR-GMAIL-ZERO-20260328: GMAIL_PASS = os.environ.get("GMAIL_APP_PASS","")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY","")

# Commission structure
PLANS = {
    "starter":    {"price": 97,   "commission_rate": 0.30, "monthly": 29.10},
    "growth":     {"price": 297,  "commission_rate": 0.30, "monthly": 89.10},
    "agency":     {"price": 497,  "commission_rate": 0.30, "monthly": 149.10},
    "dfy_essential": {"price": 997,  "commission_rate": 0.30, "monthly": 299.10},
    "dfy_growth":    {"price": 1997, "commission_rate": 0.30, "monthly": 599.10},
}

REP_RECRUITMENT_EMAIL = """
Subject: Earn $300-600/month per client you refer (recurring commissions)

Hi {name},

I'm the founder of NY Spotlight Report, an AI-powered content agency helping entrepreneurs automate their content marketing.

I'm looking for commission-only sales partners to help grow our client base.

Here's the deal:
• 30% recurring commission for the LIFE of every client you bring
• Our plans range from $97-1,997/month
• One sale = $29-599/month EVERY MONTH for as long as they stay
• 10 clients at $297/mo = $891/month passive for you, forever

What you do:
• Identify entrepreneurs who need content (LinkedIn, Twitter, your network)
• Send them our 2-minute demo video
• We close the sale and onboard them
• You get paid automatically via Stripe

No experience needed. No cold calling. Just introductions.

If you're interested, reply YES and I'll send you your personal affiliate link + tracking dashboard.

Clients typically stay 12-18 months. One client = $350-7,000 in commissions over their lifetime.

— S.C. Thomas
NY Spotlight Report
nyspotlightreport.com/proflow/
"""

REP_ONBOARDING = """
Welcome to the NYSR Sales Partner Program!

Your affiliate link: https://nyspotlightreport.com/proflow/?ref={rep_code}
Your dashboard: https://nyspotlightreport.com/rep-dashboard/{rep_code}
Commission: 30% recurring, paid monthly via Stripe or PayPal

YOUR SCRIPT (LinkedIn DM):
---
Hey [Name] — quick question. I work with a content automation company that 
publishes daily blog posts, newsletters, and social media for entrepreneurs 
completely on autopilot. Given that you're growing [their business], would 
it be worth 10 minutes to see if it fits?
---

WHO TO TARGET:
- Entrepreneurs with 1,000+ LinkedIn followers who post inconsistently
- Business coaches who talk about content but rarely publish
- E-commerce owners who need SEO traffic
- Freelancers building their personal brand

OBJECTION HANDLING:
"We already have someone do our content" → Our bots produce more in a day than a VA does in a week, at 1/10th the cost. It's not a replacement, it's a multiplier.
"Not the right time" → The best time to start building content infrastructure was last year. Second best is today.
"Too expensive" → Our clients typically earn back their subscription in affiliate + digital product revenue within 60-90 days.

Questions? Reply to this email anytime.
"""

REP_TARGETS = [
    # LinkedIn search: entrepreneurs, coaches, agency owners with 1k+ followers
    "linkedin.com/in/search?keywords=entrepreneur+content+marketing",
    "linkedin.com/in/search?keywords=business+coach+digital+products",
    "linkedin.com/in/search?keywords=agency+owner+content+creator",
    # Fiverr/Upwork freelancers with sales backgrounds
    "fiverr.com/search/gigs?query=sales+closer+commission",
    "upwork.com/search/jobs/?q=commission+sales",
]

def track_rep_sales():
    """Track sales attributed to each rep via Stripe metadata"""
    if not STRIPE_KEY: return []
    import requests
    r = requests.get("https://api.stripe.com/v1/subscriptions?limit=100&status=active",
        auth=(STRIPE_KEY,""), timeout=15)
    subs = r.json().get("data",[])
    rep_earnings = {}
    for sub in subs:
        meta = sub.get("metadata",{})
        rep = meta.get("rep_code")
        if rep:
            plan_amt = sub["plan"]["amount"]/100
            commission = plan_amt * 0.30
            rep_earnings[rep] = rep_earnings.get(rep,0) + commission
    return rep_earnings

def generate_rep_report():
    earnings = track_rep_sales()
    log.info(f"Active reps with sales: {len(earnings)}")
    total = sum(earnings.values())
    for rep, amt in sorted(earnings.items(), key=lambda x: x[1], reverse=True):
        log.info(f"  Rep {rep}: ${amt:.2f}/mo commission")
    log.info(f"Total commissions owed: ${total:.2f}/mo")
    return earnings

if __name__ == "__main__":
    log.info("Sales Rep Commission System")
    log.info(f"Plans available: {len(PLANS)}")
    for plan, data in PLANS.items():
        log.info(f"  {plan}: ${data['price']}/mo → ${data['monthly']:.2f}/mo commission")
    log.info("\nRecruiting targets identified. Drafting outreach emails...")
    generate_rep_report()
