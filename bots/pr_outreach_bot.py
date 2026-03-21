#!/usr/bin/env python3
"""
PR Outreach Bot — NYSR Agency
Pitches ProFlow AI story to journalists, podcasts, and newsletters.
One podcast feature = 500-5,000 targeted listeners.
One newsletter feature = 200-2,000 targeted readers.
One press mention = domain authority + ongoing organic traffic.
"""
import os, requests, logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("PRBot")

GMAIL_USER = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS","")

PR_TARGETS = [
    # Podcasts covering entrepreneurship/automation
    {"outlet":"Indie Hackers Podcast",       "contact":"courtland@indiehackers.com",    "type":"podcast", "reach":"200K"},
    {"outlet":"My First Million",            "contact":"editorial@mfm.fm",              "type":"podcast", "reach":"1M"},
    {"outlet":"Side Hustle School",          "contact":"chris@sidehustleschool.com",     "type":"podcast", "reach":"300K"},
    {"outlet":"Smart Passive Income",        "contact":"team@smartpassiveincome.com",    "type":"podcast", "reach":"500K"},
    # Newsletter features
    {"outlet":"Starter Story",               "contact":"pat@starterstory.com",           "type":"newsletter","reach":"150K"},
    {"outlet":"Trends.vc",                   "contact":"newsletter@trends.vc",           "type":"newsletter","reach":"30K"},
    {"outlet":"The Saturday Solopreneur",    "contact":"justin@saturdaysolopreneur.com", "type":"newsletter","reach":"50K"},
    # Press/Media
    {"outlet":"Inc Magazine",                "contact":"tips@inc.com",                   "type":"press",    "reach":"10M"},
    {"outlet":"Entrepreneur.com",            "contact":"submissions@entrepreneur.com",   "type":"press",    "reach":"5M"},
    {"outlet":"Product Hunt",                "contact":"hello@producthunt.com",          "type":"launch",   "reach":"500K"},
]

PODCAST_PITCH = """Subject: Guest pitch: How I replaced $4,000/month in content staff with AI bots

Hi,

I'm S.C. Thomas, founder of NY Spotlight Report. I think I have a story your audience would find genuinely useful — and a little surprising.

Over the past 90 days, I built a system of 63 AI bots that run our entire content operation: daily blog posts, weekly newsletter, daily social media across 5 platforms, YouTube Shorts, and digital product delivery.

The result: $0 in content staff costs, 20,000+ subscribers, and a growing passive income stack — all running without me touching it.

What makes this podcast-worthy:
- The specific tools and bots (all open-source/low-cost)  
- The exact income streams it generates (affiliate, digital products, SaaS)
- The mistakes I made along the way
- How other entrepreneurs could replicate it

I'm not selling anything — just sharing the system transparently. Happy to do a demo live during the episode.

My story: nyspotlightreport.com/proflow/

Available any week. What topics resonate most with your audience right now?

— S.C. Thomas
NY Spotlight Report | Coram, NY"""

NEWSLETTER_PITCH = """Subject: Case study pitch for {outlet} — 63 bots, $0 in content costs

Hi,

I have a case study that might be a good fit for your audience:

I built a fully automated content and passive income system using 63 bots. The system publishes daily blog posts, weekly newsletters, and daily social media — without any human involvement.

The numbers after 90 days:
- 20,000+ newsletter subscribers (from 0)
- 300+ blog posts live
- $1,200+/month in passive income (growing)
- $0 in content staff costs

I'm sharing the exact stack and results publicly. No affiliate deal needed — just think your audience of {audience_type} would find this genuinely useful.

Happy to write a custom piece or provide data for your editorial format.

— S.C. Thomas, NY Spotlight Report"""

def send_pr_pitch(target):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    if target["type"] == "podcast":
        subject = "Guest pitch: How I replaced $4,000/month in content staff with AI bots"
        body    = PODCAST_PITCH
    else:
        subject = f"Case study pitch for {target['outlet']} — 63 bots, $0 in content costs"
        body    = NEWSLETTER_PITCH.format(
            outlet=target["outlet"],
            audience_type="entrepreneurs and solopreneurs"
        )
    
    if not GMAIL_PASS:
        log.info(f"[DRAFT] PR pitch to {target['outlet']} ({target['reach']} reach)")
        return True
    
    msg = MIMEMultipart()
    msg["From"] = f"S.C. Thomas <{GMAIL_USER}>"
    msg["To"]   = target["contact"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body,"plain"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(GMAIL_USER,GMAIL_PASS)
            smtp.send_message(msg)
        log.info(f"✅ PR pitch → {target['outlet']} ({target['reach']})")
        return True
    except Exception as e:
        log.error(f"❌ {target['outlet']}: {e}")
        return False

if __name__ == "__main__":
    log.info(f"PR targets: {len(PR_TARGETS)} | Total potential reach: 12M+")
    for target in PR_TARGETS[:3]:
        send_pr_pitch(target)
        time.sleep(5)
    log.info("PR outreach sent. One placement = 500-5,000 targeted visitors")
