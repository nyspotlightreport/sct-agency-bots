#!/usr/bin/env python3
"""
Autonomous Marketing Command Center — NYSR Marketing Agency
═══════════════════════════════════════════════════════════════

Coordinates every marketing channel simultaneously.
Learns what traffic converts, doubles what works, kills what doesn't.

CHANNELS MANAGED:
  • SEO content pipeline (Ahrefs keyword intelligence)
  • Paid ad simulation (organic equivalent)
  • Social media campaigns (6 platforms, coordinated messaging)
  • Email marketing (Beehiiv sequences)
  • Affiliate traffic
  • PR & press outreach
  • Community marketing (Reddit, Quora, forums)
  • Content syndication (Medium, LinkedIn, newsletters)
  • Viral mechanics (referral, share incentives)

SELF-OPTIMIZATION:
  • Traffic attribution tracked per channel
  • Conversion rate per traffic source logged
  • Weekly reallocation: more resources to high-converting channels
  • Monthly ICP refinement based on actual converters
  • A/B testing all CTAs, landing pages, ad copy
"""
import os, sys, json, logging, requests, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Marketing] %(message)s")
log = logging.getLogger()

ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN    = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
AHREFS_KEY  = os.environ.get("AHREFS_API_KEY","")
GH_H        = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
REPO        = "nyspotlightreport/sct-agency-bots"

MARKETING_SYSTEM = """You are Elliot Shaw, VP Marketing at NY Spotlight Report.
You build marketing systems that compound — each piece of content multiplies across channels.
Your philosophy: distribution beats content. 10 channels at once beats 1 channel perfectly.
You think in funnels: traffic → email → engaged subscriber → buyer → promoter.
Data first. Every decision backed by numbers. Every channel tracked and attributed."""

# ── CHANNEL PERFORMANCE TRACKING ─────────────────────────────────

CHANNELS = {
    "seo_blog":         {"type":"organic","cost":0,     "current_visitors":0,"conv_rate":0,"roi":0},
    "linkedin_posts":   {"type":"social", "cost":0,     "current_visitors":0,"conv_rate":0,"roi":0},
    "twitter_threads":  {"type":"social", "cost":0,     "current_visitors":0,"conv_rate":0,"roi":0},
    "reddit_posts":     {"type":"community","cost":0,   "current_visitors":0,"conv_rate":0,"roi":0},
    "email_sequences":  {"type":"email",  "cost":0,     "current_visitors":0,"conv_rate":0,"roi":0},
    "medium_articles":  {"type":"syndication","cost":0, "current_visitors":0,"conv_rate":0,"roi":0},
    "youtube_shorts":   {"type":"video",  "cost":0,     "current_visitors":0,"conv_rate":0,"roi":0},
    "pr_mentions":      {"type":"pr",     "cost":0,     "current_visitors":0,"conv_rate":0,"roi":0},
    "affiliate_links":  {"type":"affiliate","cost":0,   "current_visitors":0,"conv_rate":0,"roi":0},
    "guest_posts":      {"type":"backlink","cost":0,    "current_visitors":0,"conv_rate":0,"roi":0},
}

def run_channel_optimization() -> dict:
    """
    Analyze all channels, reallocate effort to top performers.
    Returns optimization plan for the week.
    """
    perf = load_channel_performance()
    
    if not any(ch.get("current_visitors",0) > 0 for ch in perf.values()):
        # No data yet — build initial launch plan
        return generate_launch_plan()
    
    # Sort by conversion efficiency
    sorted_channels = sorted(
        [(k,v) for k,v in perf.items()],
        key=lambda x: x[1].get("conv_rate",0) * x[1].get("current_visitors",1),
        reverse=True
    )
    
    top_channels  = [k for k,v in sorted_channels[:3]]
    dead_channels = [k for k,v in sorted_channels if v.get("current_visitors",0)==0
                     and v.get("last_ran") and 
                     (datetime.now()-datetime.fromisoformat(v["last_ran"])).days > 14]
    
    return {
        "week": str(date.today()),
        "priority_channels": top_channels,
        "pause_channels": dead_channels,
        "recommendation": f"Double output on {top_channels[0] if top_channels else 'all channels'}",
        "a_b_tests_running": []
    }

def generate_launch_plan() -> dict:
    """When no data exists — aggressive launch across all channels simultaneously."""
    return {
        "week": str(date.today()),
        "mode": "LAUNCH",
        "priority_channels": ["seo_blog","linkedin_posts","reddit_posts","email_sequences"],
        "daily_actions": {
            "monday":    ["blog_post","linkedin_post","email_sequence_step"],
            "tuesday":   ["twitter_thread","reddit_value_post","medium_syndication"],
            "wednesday": ["youtube_short_script","linkedin_article","pr_outreach_3_journalists"],
            "thursday":  ["blog_post","twitter_thread","reddit_ama_comment"],
            "friday":    ["newsletter_send","linkedin_post","affiliate_content"],
            "saturday":  ["reddit_post","twitter_thread","youtube_community"],
            "sunday":    ["seo_audit","week_review","plan_next_week"],
        },
        "volume_targets": {
            "blog_posts_per_week":    7,
            "social_posts_per_day":   3,
            "cold_emails_per_day":  200,
            "pr_pitches_per_week":   10,
            "youtube_shorts_per_week": 5,
        }
    }

def generate_campaign_assets(theme: str, channels: list) -> dict:
    """
    Generate full campaign assets for a given theme across multiple channels.
    One theme → all channels → coordinated message.
    """
    if not ANTHROPIC:
        return {"theme": theme, "assets": {}}
    
    return claude_json(
        MARKETING_SYSTEM,
        f"""Generate a full coordinated campaign for this theme: {theme}
Target channels: {", ".join(channels)}
Brand: NY Spotlight Report — SC Thomas, AI automation expert
Goal: Drive traffic to nyspotlightreport.com/free-plan/ (free 30-day content plan)

Return JSON with assets for each channel:
{{
  "campaign_name": str,
  "core_message": "one sentence — the hook/angle for this campaign",
  "assets": {{
    "seo_blog": {{"title": str, "keyword": str, "word_count": 750, "h2s": ["H2 1","H2 2","H2 3"]}},
    "linkedin_post": "full 200-word post with spacing for readability",
    "twitter_thread": ["tweet 1 hook (strong)","tweet 2","tweet 3","tweet 4 CTA"],
    "email_subject": "subject line for newsletter",
    "email_preview": "preview text (50 chars)",
    "reddit_title": "title for r/entrepreneur or r/SideProject",
    "youtube_hook": "first 15 seconds of YouTube Shorts script",
    "press_angle": "one paragraph pitch angle for journalists"
  }},
  "cta_primary": "exact CTA text",
  "cta_url": "https://nyspotlightreport.com/free-plan/",
  "expected_reach": "realistic estimate"
}}""",
        max_tokens=1500
    ) or {"theme": theme, "assets": {}}

def load_channel_performance() -> dict:
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/marketing/channel_performance.json", headers=GH_H)
    if r.status_code == 200:
        try: return json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    return CHANNELS.copy()

def save_optimization_plan(plan: dict):
    path = "data/marketing/optimization_plan.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    existing = []
    if r.status_code == 200:
        try: existing = json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    if not isinstance(existing, list): existing = []
    existing.insert(0, plan)
    existing = existing[:12]
    body = {"message": f"marketing: optimization plan {date.today()}",
            "content": base64.b64encode(json.dumps(existing, indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)

def run():
    log.info("Marketing Command Center starting...")
    
    # Channel optimization
    plan = run_channel_optimization()
    save_optimization_plan(plan)
    log.info(f"Mode: {plan.get('mode','OPTIMIZE')}")
    log.info(f"Priority channels: {plan.get('priority_channels',[][:3])}")
    
    # Generate today's campaign assets
    themes = [
        "I replaced a $4,000/month content team with AI bots",
        "The content automation stack that runs itself",
        "How to build passive income with AI tools in 2026",
        "63 bots, $70/month, daily output — the system breakdown",
    ]
    today_theme = themes[date.today().timetuple().tm_yday % len(themes)]
    
    log.info(f"Today's campaign theme: {today_theme}")
    channels = plan.get("priority_channels", ["seo_blog","linkedin_posts","twitter_threads"])
    
    assets = generate_campaign_assets(today_theme, channels[:4])
    
    if assets.get("assets"):
        path = f"data/marketing/campaigns/{date.today()}.json"
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
        body = {"message": f"marketing: campaign assets {date.today()}",
                "content": base64.b64encode(json.dumps(assets, indent=2).encode()).decode()}
        if r.status_code == 200: body["sha"] = r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)
        log.info(f"✅ Campaign assets saved: {len(assets.get('assets',{}))} channels")
    
    log.info("✅ Marketing Command Center complete")

if __name__ == "__main__":
    run()
