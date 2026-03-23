#!/usr/bin/env python3
"""
agents/traffic_conversion_engine.py — CRO's Revenue Machine
Jeff Banks' #1 priority: drive traffic → convert → retain → upsell

THIS IS THE REVENUE ENGINE. Everything else supports this.

TRAFFIC SOURCES (in order of ROI):
1. SEO blog content → organic Google traffic → /proflow/ CTA
2. Social media posts → link in bio → /proflow/
3. Cold email outreach → direct to /proflow/
4. Newsletter → weekly value → embedded CTAs
5. Voice AI → inbound callers → qualify → /activate/
6. Press/PR → brand search → homepage → /proflow/
7. Referral program → existing clients → new signups

CONVERSION POINTS:
- Homepage → /proflow/ (offer page)
- Blog posts → inline CTA → /proflow/
- Exit popup → email capture → nurture → /proflow/
- /proflow/ → /activate/ (onboarding)
- /activate/ → Stripe checkout → payment
- Payment → auto-onboarding → content delivery starts

RETENTION:
- Weekly reports keep them seeing value
- Daily content keeps them dependent
- Monthly ROI calculation shows savings
- AI receptionist becomes part of their business

UPSELL:
- Starter → Growth (show what they're missing)
- Growth → Agency (when they want more)
- Any plan → DFY setup ($1,497 one-time)
- Any plan → Custom build ($24,997)
"""
import os,sys,json,logging,time
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),".."))
log=logging.getLogger("traffic_cro")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [CRO] %(message)s")
import urllib.request as urlreq,urllib.parse

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
GH_PAT=os.environ.get("GH_PAT","")
GMAIL_USER=os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS=os.environ.get("GMAIL_APP_PASS","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")

LIVE_REPO="nyspotlightreport/NY-Spotlight-Report-good"
SOURCE_REPO="nyspotlightreport/sct-agency-bots"

def claude(prompt,mt=1500):
    if not ANTHROPIC:return ""
    try:
        d=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":mt,"messages":[{"role":"user","content":prompt}]}).encode()
        r=urlreq.Request("https://api.anthropic.com/v1/messages",data=d,headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
        with urlreq.urlopen(r,timeout=90) as resp:return json.loads(resp.read())["content"][0]["text"]
    except:return ""

def gh_commit(repo,path,content,msg):
    import base64
    if not GH_PAT:return False
    enc=base64.b64encode(content.encode()).decode()
    sha=""
    try:
        r=urlreq.Request(f"https://api.github.com/repos/{repo}/contents/{path}",headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json"})
        with urlreq.urlopen(r,timeout=10) as resp:sha=json.loads(resp.read()).get("sha","")
    except Exception:  # noqa: bare-except

        pass
    d={"message":msg,"content":enc}
    if sha:d["sha"]=sha
    try:
        r=urlreq.Request(f"https://api.github.com/repos/{repo}/contents/{path}",data=json.dumps(d).encode(),method="PUT",
            headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
        urlreq.urlopen(r,timeout=15);return True
    except:return False

def push(t,m):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000]}).encode(),timeout=5)
    except Exception:  # noqa: bare-except

        pass
def send_email(to,subject,html):
    if not GMAIL_PASS:return False
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    try:
        msg=MIMEMultipart("alternative")
        msg["From"]=f"ProFlow <{GMAIL_USER}>";msg["To"]=to;msg["Subject"]=subject
        msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:s.starttls();s.login(GMAIL_USER,GMAIL_PASS);s.send_message(msg)
        return True
    except:return False


# ═══ CHANNEL 1: SEO CONTENT WITH CONVERSION ═══
def generate_conversion_blog_post():
    """Generate a blog post specifically designed to convert readers to customers."""
    topics = [
        ("How Much Does a Content Team Really Cost in 2026? (We Did the Math)", "cost comparison"),
        ("I Replaced My 3-Person Content Team with AI. Here's What Happened.", "case study"),
        ("The $4,000/Month Content Mistake Most Agencies Make", "pain point"),
        ("Why Your Freelance Writer Costs 10x What You Think", "hidden costs"),
        ("We Generated 30 Blog Posts in 30 Days for $297. Here's Every Post.", "proof"),
        ("AI Content vs Human Content: A Blind Test with Real Marketers", "comparison"),
        ("How to Get 90+ Social Media Posts Per Month Without a Social Media Manager", "how-to"),
        ("The Agency Owner's Guide to Firing Your Content Team (Nicely)", "guide"),
    ]
    import random
    title, angle = random.choice(topics)
    slug = title.lower()
    for c in "?:.'\"(),$": slug = slug.replace(c, "")
    slug = slug.replace(" ", "-").replace("--", "-").strip("-")[:60]
    
    html = claude(f"""Write a complete blog post that CONVERTS readers into ProFlow customers.

Title: {title}
Angle: {angle}
Target: Agency owners and small business owners spending $2K-8K/month on content

RULES FOR CONVERSION CONTENT:
1. Open with a specific, relatable pain point (not generic)
2. Use real numbers and specific examples throughout
3. Include a comparison table showing old way vs ProFlow
4. Include at least 2 natural CTAs (not pushy — helpful)
5. End with a clear, low-friction next step
6. Make the math undeniable — show them they're losing money every day they wait

CTAs to include naturally:
- "See exactly what you'd get → nyspotlightreport.com/proflow/"
- "Try it for 14 days — if we don't deliver, you don't pay → nyspotlightreport.com/activate/"
- "Call our AI receptionist right now to see the tech in action: (631) 892-9817"

Write 1,500 words. Full HTML page with nav, styled with Playfair Display + DM Sans fonts.
Include the conversion engine snippet before </body>:
- Sticky bottom CTA bar
- Auto-injected inline CTAs

Make it genuinely valuable — not a sales pitch disguised as an article.""", 3000)
    
    return {"title":title,"slug":slug,"html":html,"chars":len(html) if html else 0}


# ═══ CHANNEL 2: SOCIAL MEDIA WITH TRAFFIC INTENT ═══
def generate_traffic_social_posts():
    """Generate social posts specifically designed to drive traffic to /proflow/."""
    posts = claude("""Generate 7 social media posts designed to drive traffic to nyspotlightreport.com/proflow/

Each post should:
- Provide genuine value (not just "check out our product")
- Include a specific stat, insight, or provocative question
- End with a natural link to the offer page
- Feel like a real person sharing a real insight

Generate:
- 2 LinkedIn posts (data-driven, professional, 150-200 words)
- 2 Twitter/X posts (punchy, under 280 chars, with hook)
- 2 Instagram captions (visual-friendly, storytelling, with hashtags)
- 1 Facebook post (conversational, community-oriented)

URL to include: nyspotlightreport.com/proflow/
Phone to mention: (631) 892-9817 (for Voice AI demo)

Return as JSON array with: platform, content, hashtags fields.""", 1200)
    return posts


# ═══ CHANNEL 3: EMAIL NURTURE SEQUENCE ═══
EMAIL_NURTURE = [
    {"day":0,"subject":"Your free guide: Replace Your Content Team with AI","type":"lead_magnet"},
    {"day":1,"subject":"The $4,000 question most agencies can't answer","type":"pain_point"},
    {"day":3,"subject":"What 30 blog posts in 30 days actually looks like","type":"proof"},
    {"day":5,"subject":"The math that changed how I think about content","type":"cost_comparison"},
    {"day":7,"subject":"Ready to see it work? (14-day guarantee)","type":"soft_close"},
    {"day":10,"subject":"Quick question about your content situation","type":"engagement"},
    {"day":14,"subject":"Last thing — then I'll stop emailing","type":"final"},
]

def generate_nurture_email(day_config):
    """Generate a nurture email for the automated sequence."""
    return claude(f"""Write a nurture email for day {day_config['day']} of our email sequence.
Subject: {day_config['subject']}
Type: {day_config['type']}
Sender: S.C. Thomas, NY Spotlight Report
Product: ProFlow AI — done-for-you content engine, $97-497/mo
CTA URL: nyspotlightreport.com/proflow/

RULES:
- Short (under 200 words for body)
- Personal tone — like a real person writing to a colleague
- ONE clear CTA per email
- No hype, no urgency tricks, no scarcity manipulation
- Just genuinely useful insight + a natural invitation to learn more
- Plain HTML, minimal styling — like a real email

This is day {day_config['day']} of 14. {'This is the first touch — deliver the promised guide value.' if day_config['day']==0 else 'Build on previous emails without repeating.'}""", 500)


# ═══ CHANNEL 4: COLD OUTREACH WITH VALUE ═══
def generate_cold_outreach():
    """Generate personalized cold outreach templates."""
    return claude("""Generate 3 cold email templates for reaching agency owners about ProFlow.

RULES:
- Under 100 words each (short = higher open rate)
- No "I hope this finds you well"
- Lead with a specific insight about their business
- Include a single, low-commitment CTA
- Sound like a real person, not a sales bot

Template 1: "I noticed something about your content" approach
Template 2: "Quick question" approach  
Template 3: "Thought you'd find this useful" approach (link to a blog post)

Each template should have: subject line, body, and CTA.
Include {company}, {name}, {industry} merge fields.
CTA should link to nyspotlightreport.com/proflow/""", 800)


# ═══ MAIN: DAILY CRO ENGINE ═══
def run():
    log.info("="*60)
    log.info("TRAFFIC & CONVERSION ENGINE — CRO Daily Operations")
    log.info(f"Jeff Banks | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    log.info("="*60)
    
    results = {}
    
    # 1. Generate and publish conversion blog post
    log.info("\n[1] Generating conversion blog post...")
    post = generate_conversion_blog_post()
    if post["html"] and len(post["html"]) > 500:
        live = gh_commit(LIVE_REPO, f"blog/{post['slug']}/index.html", post["html"], f"CRO: {post['title']}")
        gh_commit(SOURCE_REPO, f"site/blog/{post['slug']}/index.html", post["html"], f"CRO: {post['title']}")
        results["blog_post"] = {"title": post["title"], "deployed": live, "chars": post["chars"]}
        log.info(f"  Published: {post['title']} ({post['chars']} chars)")
    
    # 2. Generate social posts
    log.info("\n[2] Generating traffic social posts...")
    social = generate_traffic_social_posts()
    results["social_posts"] = len(social) if social else 0
    
    # 3. Generate nurture emails (for new leads)
    log.info("\n[3] Generating nurture content...")
    for config in EMAIL_NURTURE[:2]:
        email_html = generate_nurture_email(config)
        results[f"email_day_{config['day']}"] = len(email_html) if email_html else 0
    
    # 4. Generate cold outreach templates
    log.info("\n[4] Generating cold outreach...")
    outreach = generate_cold_outreach()
    results["cold_templates"] = len(outreach) if outreach else 0
    
    push("CRO Daily", f"Blog: {results.get('blog_post',{}).get('title','none')[:40]} | Social: {results.get('social_posts',0)} posts")
    
    log.info(f"\n{'='*60}")
    log.info(f"CRO DAILY COMPLETE")
    log.info(f"{'='*60}")
    return results

if __name__=="__main__":
    run()
