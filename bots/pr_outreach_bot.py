#!/usr/bin/env python3
"""
PR & Media Relations Bot v2 — NYSR Agency
World-class PR at scale. No agency needed.

Strategy:
- Tier 1: Podcast guesting (12M+ combined reach) → direct exposure
- Tier 2: Newsletter features (1M+ combined readers) → targeted B2B
- Tier 3: Press coverage (journalist tips) → credibility + backlinks  
- Tier 4: Community authority (Indie Hackers, Hacker News) → developer/founder trust

Target: 2-3 placements/month = 50,000-200,000 new people reached/month
One placement converts at 0.5-2% = 250-4,000 new subscribers per feature.
"""
import os, sys, logging, json, smtplib, time
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
except:
    def claude(s, u, **k): return u[:200]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PR-Bot] %(message)s")
log = logging.getLogger()

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS", "")
ANTHROPIC  = os.environ.get("ANTHROPIC_API_KEY", "")

# ── TIER 1: PODCAST TARGETS (12M+ combined reach) ────────────────
PODCASTS = [
    {"name":"Indie Hackers Podcast",       "host":"Courtland Allen",   "email":"courtland@indiehackers.com",    "listeners":"50k",  "angle":"automation_founder"},
    {"name":"My First Million",            "host":"Sam Parr/Shaan Puri","email":"editorial@mfm.fm",             "listeners":"500k", "angle":"passive_income_system"},
    {"name":"Side Hustle School",          "host":"Chris Guillebeau",  "email":"chris@sidehustleschool.com",    "listeners":"200k", "angle":"zero_cost_passive"},
    {"name":"Smart Passive Income",        "host":"Pat Flynn",         "email":"team@smartpassiveincome.com",   "listeners":"300k", "angle":"automation_stack"},
    {"name":"Entrepreneurs on Fire",       "host":"John Lee Dumas",    "email":"kate@eofire.com",               "listeners":"100k", "angle":"ai_bots_revenue"},
    {"name":"The Tim Ferriss Show",        "host":"Tim Ferriss",       "email":"tips@tim.blog",                 "listeners":"700k", "angle":"systems_automation"},
    {"name":"How I Built This",            "host":"Guy Raz",           "email":"hibt@npr.org",                  "listeners":"1M",   "angle":"bootstrapped_ai"},
    {"name":"Acquired",                    "host":"Ben Gilbert/David", "email":"ben@acquiredfm.com",            "listeners":"200k", "angle":"ai_arbitrage"},
    {"name":"Nathan Latka SaaS",           "host":"Nathan Latka",      "email":"nathan@founderpath.com",        "listeners":"50k",  "angle":"saas_metrics"},
    {"name":"The Hustle Daily Show",       "host":"HubSpot",           "email":"podcasts@thehustle.co",         "listeners":"100k", "angle":"automation_trends"},
]

# ── TIER 2: NEWSLETTER TARGETS (2M+ combined readers) ────────────
NEWSLETTERS = [
    {"name":"Starter Story",          "editor":"Pat Walls",      "email":"pat@starterstory.com",          "subscribers":"250k","angle":"case_study"},
    {"name":"Trends.vc",              "editor":"Dru Riley",      "email":"newsletter@trends.vc",          "subscribers":"50k", "angle":"trend_analysis"},
    {"name":"The Saturday Solopreneur","editor":"Justin Welsh",  "email":"justin@saturdaysolopreneur.com","subscribers":"400k","angle":"solopreneur_systems"},
    {"name":"Dense Discovery",        "editor":"Kai Brach",      "email":"kai@densediscovery.com",        "subscribers":"30k", "angle":"tool_feature"},
    {"name":"TLDR Newsletter",        "editor":"Dan Ni",         "email":"dan@tldrnewsletter.com",        "subscribers":"1M",  "angle":"ai_automation"},
    {"name":"The Hustle",             "editor":"Editors",        "email":"tips@thehustle.co",             "subscribers":"1.5M","angle":"business_innovation"},
    {"name":"Morning Brew",           "editor":"Editors",        "email":"tips@morningbrew.com",          "subscribers":"4M",  "angle":"ai_entrepreneurship"},
    {"name":"Superhuman",             "editor":"Zain Kahn",      "email":"zain@superhuman.ai",            "subscribers":"300k","angle":"ai_productivity"},
    {"name":"Lenny's Newsletter",     "editor":"Lenny Rachitsky","email":"lennys@substack.com",           "subscribers":"200k","angle":"product_growth"},
    {"name":"Hiten Shah Newsletter",  "editor":"Hiten Shah",     "email":"hiten@hnewsletter.com",         "subscribers":"100k","angle":"saas_growth"},
]

# ── TIER 3: PRESS OUTLETS ─────────────────────────────────────────
PRESS = [
    {"name":"Inc Magazine",           "section":"Technology",  "email":"tips@inc.com",                   "reach":"10M", "angle":"ai_automation"},
    {"name":"Entrepreneur.com",       "section":"Technology",  "email":"submissions@entrepreneur.com",   "reach":"5M",  "angle":"passive_income_ai"},
    {"name":"Fast Company",           "section":"Technology",  "email":"tips@fastcompany.com",           "reach":"8M",  "angle":"future_of_work"},
    {"name":"Business Insider",       "section":"Tech",        "email":"tips@businessinsider.com",       "reach":"50M", "angle":"ai_bots_replace_staff"},
    {"name":"TechCrunch",             "section":"AI",          "email":"tips@techcrunch.com",            "reach":"12M", "angle":"ai_micro_saas"},
    {"name":"Forbes Entrepreneurs",   "section":"Technology",  "email":"forbesstaff@forbes.com",         "reach":"30M", "angle":"ai_entrepreneur"},
]

PITCH_SYSTEM = """You're the PR director for NY Spotlight Report.
Write pitches that are brief, specific, and news-worthy.
SC Thomas is the founder — built 63 AI bots that run his entire content business.
The story: replaced $4,000/month in content staff with automation costing $70/month.
Never: generic "would love to be on your show" pitches.
Always: lead with the specific result, make it about their audience."""

def write_pitch(target: dict, pitch_type: str) -> dict:
    """Write a personalized pitch using Claude."""
    if not ANTHROPIC:
        return _static_pitch(target, pitch_type)
    
    if pitch_type == "podcast":
        prompt = f"""Write a cold pitch email to {target["host"]} at {target["name"]} podcast.

Angle: {target["angle"]}
Their audience: ~{target["listeners"]} listeners
Style: Direct founder-to-founder, under 120 words total

The story: SC Thomas replaced his entire content team ($4,000/month) with 63 AI bots.
System publishes daily blogs, weekly newsletters, social media across 6 platforms,
YouTube Shorts — all automated for $70/month. Built in 6 months, now generates
passive income while running cold outreach to find new clients.

Return JSON: {{subject: str, body: str (under 120 words)}}"""

    elif pitch_type == "newsletter":
        prompt = f"""Write a case study pitch to {target["editor"]} at {target["name"]} newsletter.

Angle: {target["angle"]}
Their audience: ~{target["subscribers"]} subscribers
Style: Peer-to-peer, story-forward, under 100 words

The case study: Built 63 AI bots that run an entire content business autonomously.
Publishes daily, earns passively, acquires clients automatically.
Costs $70/month to run vs $4,000-8,000/month for equivalent human team.

Return JSON: {{subject: str, body: str (under 100 words)}}"""
    else:
        prompt = f"""Write a journalist tip to {target["name"]} ({target["section"]} section).

Angle: {target["angle"]}
Their reach: ~{target["reach"]}
Style: News tip format, factual, 3 bullet points max

The news: Solo entrepreneur replaced $4,000/month content team with 63 AI bots.
System runs fully autonomously — no humans needed for content creation.

Return JSON: {{subject: str, body: str (under 80 words)}}"""

    from agents.claude_core import claude_json
    return claude_json(PITCH_SYSTEM, prompt, max_tokens=300) or _static_pitch(target, pitch_type)

def _static_pitch(target: dict, pitch_type: str) -> dict:
    if pitch_type == "podcast":
        return {
            "subject": "Guest pitch: How I replaced $4,000/month in content staff with AI bots",
            "body": f"Hi {target.get('host', 'there')},

I'm SC Thomas, founder of NY Spotlight Report (Coram, NY).

I replaced my entire content team — $4,000/month — with 63 AI bots I built myself. The system now publishes daily blogs, weekly newsletters, and social media across 6 platforms automatically, for $70/month.

For your audience: I'll walk through exactly what I built, what it costs, and how to replicate the core of it in a weekend.

Open to 30-45 minutes whenever works for you.

— SC Thomas
nyspotlightreport.com"
        }
    elif pitch_type == "newsletter":
        return {
            "subject": f"Case study for {target.get('name','')}: 63 AI bots, $0 content costs",
            "body": f"Hi {target.get('editor', 'there')},

I built a fully automated content business — 63 bots handling daily blogs, newsletters, social media, cold email, and digital product delivery. Total cost: $70/month vs $4,000-8,000/month for a human team.

Think your readers would find a behind-the-scenes breakdown useful? Happy to write a 1,500-word case study exclusively for {target.get('name', 'your newsletter')}.

— SC Thomas, NY Spotlight Report"
        }
    else:
        return {
            "subject": "Story tip: Solo founder replaces content team with AI bots",
            "body": f"Hi,

Story tip for {target.get('section', 'your tech section')}:

• Solo entrepreneur replaced $4,000/month content staff with 63 custom AI bots
• System publishes 365 blog posts/year, manages 6 social platforms, sends newsletters — all automated
• Cost: $70/month. Approach: Python + Claude API + GitHub Actions

Happy to provide quotes, data, or a full interview.

SC Thomas, NY Spotlight Report — nyspotlightreport.com"
        }

def send_pitch(target: dict, pitch: dict) -> bool:
    """Send pitch via Gmail."""
    if not GMAIL_PASS:
        log.info(f"[DRAFT] Would pitch: {target.get('name','')} | {pitch['subject'][:50]}")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"SC Thomas <{GMAIL_USER}>"
        msg["To"]      = target["email"]
        msg["Subject"] = pitch["subject"]
        msg["Reply-To"]= GMAIL_USER
        msg.attach(MIMEText(pitch["body"], "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        log.info(f"✅ Sent: {target['name']} ({target['email']}) | {pitch['subject'][:50]}")
        return True
    except Exception as e:
        log.error(f"❌ Failed {target['name']}: {e}")
        return False

def save_pipeline(all_pitches: list):
    """Save PR pipeline to repo for tracking."""
    import json, base64
    GH_TOKEN = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
    if not GH_TOKEN: return
    H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO = "nyspotlightreport/sct-agency-bots"
    path = "data/pr_pipeline.json"
    payload = json.dumps({"updated": datetime.now().isoformat(), "pitches": all_pitches}, indent=2)
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H)
    body = {"message":"feat: update PR pipeline tracker","content":base64.b64encode(payload.encode()).decode()}
    if r.status_code==200: body["sha"]=r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=H)

def run():
    log.info("PR & Media Relations Bot v2 starting...")
    log.info(f"Targets: {len(PODCASTS)} podcasts | {len(NEWSLETTERS)} newsletters | {len(PRESS)} press")
    log.info(f"Combined reach: 20M+ people")
    
    # Rotate through targets weekly - 3 per run to avoid spam
    week_num = date.today().isocalendar()[1]
    
    # Pick 1 podcast + 1 newsletter + 1 press this week
    podcast   = PODCASTS[week_num % len(PODCASTS)]
    newsletter= NEWSLETTERS[week_num % len(NEWSLETTERS)]
    press_out = PRESS[week_num % len(PRESS)]
    
    pitches_sent = []
    
    for target, ptype in [(podcast,"podcast"),(newsletter,"newsletter"),(press_out,"press")]:
        log.info(f"Pitching: {target['name']} ({ptype})")
        pitch = write_pitch(target, ptype)
        if pitch:
            sent = send_pitch(target, pitch)
            pitches_sent.append({
                "outlet": target["name"], "type": ptype, 
                "sent": sent, "subject": pitch.get("subject",""),
                "date": str(date.today())
            })
            time.sleep(5)
    
    save_pipeline(pitches_sent)
    log.info(f"PR run complete: {sum(1 for p in pitches_sent if p['sent'])}/{len(pitches_sent)} sent")
    
    # Reach estimate
    reach = sum(int(t.get("listeners","0").replace("k","000").replace("M","000000"))
                for t in [podcast] if t.get("listeners"))
    log.info(f"Potential reach this week: {reach:,}+ people")

if __name__ == "__main__":
    run()
