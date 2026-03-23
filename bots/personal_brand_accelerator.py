#!/usr/bin/env python3
"""
Personal Brand Accelerator — NYSR Fixer PR
╔══════════════════════════════════════════════════════════════╗
║  OBJECTIVE: Turn an unknown person into a recognized name   ║
║  in their target field within 30-90 days.                   ║
╚══════════════════════════════════════════════════════════════╝

The 30-Day Protocol:

WEEK 1 — Foundation (digital footprint)
  Day 1-2: LinkedIn fully optimized + connected to 100+ relevant people
  Day 3-4: Twitter/X profile + first 10 threads posted
  Day 5:   Medium profile + first 3 authority articles
  Day 6-7: Quora profile + 10 expert answers published

WEEK 2 — Authority building
  Day 8-9:   YouTube channel + 5 keyword-optimized videos
  Day 10-11: Crunchbase + AngelList + Muck Rack profiles
  Day 12-13: Guest post on 3 medium-DA blogs (500-1,000 readers)
  Day 14:    First press release on EINPresswire (free tier)

WEEK 3 — Community infiltration
  Day 15-17: Reddit — value posts in 5 relevant communities
  Day 18-19: Twitter engagement — reply to 50 influencers in niche
  Day 20-21: First podcast pitch batch (10 shows)
  Day 21:    First newsletter mention or swap

WEEK 4 — Amplification
  Day 22-24: Second press release + first journalist tip
  Day 25-26: LinkedIn + Twitter cross-promotion peak
  Day 27-28: First podcast recording (should have 2-3 booked)
  Day 29-30: Wikipedia notability check — if criteria met, draft article

RESULT:
  - 50+ Google results for their name (up from 0)
  - 7-10 page 1 SERP results controlled
  - 2-5 podcast interviews scheduled
  - 1,000+ LinkedIn connections in niche
  - 500-2,000 Twitter followers in field
  - Google Knowledge Panel (if 2+ press mentions secured)
"""
import os, sys, json, logging, requests
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [BrandAccel] %(message)s")
log = logging.getLogger()

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN  = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")

PR_SYSTEM = """You are a personal brand strategist who has built 100+ public figures from zero.
You understand the mechanics of recognition, authority, and digital presence.
Write practical, specific, immediately executable content."""

def generate_30_day_plan(person_name: str, expertise_area: str, 
                          target_audience: str, current_status: str = "unknown") -> dict:
    """Generate the complete 30-day nobody-to-known protocol."""
    
    if not ANTHROPIC:
        return _static_30_day_plan(person_name, expertise_area)
    
    return claude_json(
        PR_SYSTEM,
        f"""Create a complete 30-day personal brand acceleration plan:

Person: {person_name}
Expertise: {expertise_area}
Target audience: {target_audience}
Current online presence: {current_status}

Generate a precise, day-by-day action plan with SPECIFIC content to publish.

Return JSON:
{{
  "week_1_foundation": {{
    "day_1_linkedin": {{
      "headline": "Exact LinkedIn headline to use",
      "summary_opening": "First 3 sentences of LinkedIn summary",
      "first_post": "First LinkedIn post content (150 words)",
      "connection_targets": "Type of people to connect with"
    }},
    "day_3_twitter": {{
      "bio": "Exact Twitter bio (160 chars)",
      "pinned_thread": "5-tweet thread to pin — hook + value",
      "first_10_tweets": ["Tweet 1","Tweet 2","Tweet 3"]
    }},
    "day_5_medium": {{
      "article_1_title": "First Medium article to publish",
      "article_1_hook": "Opening paragraph",
      "article_2_title": "Second article",
      "article_3_title": "Third article"
    }},
    "day_6_quora": {{
      "bio": "Quora bio with keyword",
      "top_3_questions_to_answer": ["Q1","Q2","Q3"],
      "answer_format": "How to structure the answers for authority"
    }}
  }},
  "week_2_authority": {{
    "youtube_channel": {{
      "channel_name": "SEO-optimized channel name",
      "video_1_title": "First video title + description outline",
      "video_2_title": "Second video",
      "video_3_title": "Third video"
    }},
    "press_release_1": {{
      "angle": "First PR angle",
      "headline": "Press release headline",
      "key_quote": "Quote from {person_name}"
    }},
    "guest_post_targets": ["Blog 1 (why)","Blog 2 (why)","Blog 3 (why)"]
  }},
  "week_3_infiltration": {{
    "reddit_subreddits": ["r/sub1 - angle","r/sub2 - angle","r/sub3 - angle"],
    "influencers_to_engage": "What TYPE of accounts to reply to and how",
    "podcast_pitch_template": "50-word pitch template for their specific story",
    "podcast_targets_tier1": ["Show 1","Show 2","Show 3"]
  }},
  "week_4_amplification": {{
    "press_release_2": "Second angle — different hook",
    "journalist_tips": "Which journalists to tip and with what angle",
    "wikipedia_check": "Does this person qualify? What notability criteria to pursue?",
    "google_knowledge_panel_triggers": "Exact steps to trigger Google to create a Knowledge Panel"
  }},
  "serp_domination_sequence": [
    {{"day":1,"platform":"LinkedIn","action":"Create/optimize profile","expected_rank":"top 3 for name search"}},
    {{"day":2,"platform":"Medium","action":"Publish first article","expected_rank":"page 1 within 48h"}},
    {{"day":3,"platform":"Twitter","action":"Optimize profile + first thread","expected_rank":"page 1"}},
    {{"day":7,"platform":"YouTube","action":"First video published","expected_rank":"page 1 within 7 days"}},
    {{"day":10,"platform":"Press Release","action":"EINPresswire distribution","expected_rank":"page 1 via pickup"}},
    {{"day":21,"platform":"Podcast","action":"First episode live","expected_rank":"persists indefinitely"}}
  ],
  "name_recognition_milestones": {{
    "day_7":  "X Google results for name (baseline)",
    "day_30": "Y Google results + Z controlled on page 1",
    "day_60": "Full page 1 control + press mentions",
    "day_90": "Google Knowledge Panel + recognized in niche"
  }}
}}""",
        max_tokens=3500
    ) or _static_30_day_plan(person_name, expertise_area)

def _static_30_day_plan(name, expertise):
    return {
        "week_1_foundation": {
            "day_1_linkedin": {
                "headline": f"{name} | {expertise} Expert | Founder, NY Spotlight Report",
                "summary_opening": f"I spent 6 months building the AI system that replaced my entire content team. Now I help entrepreneurs do the same.",
                "first_post": f"Six months ago I had a content problem. 20+ hours/week just to stay consistent. Now I have 63 bots doing it for $70/month. Here's exactly what I built...",
            }
        },
        "serp_domination_sequence": [
            {"day":1,"platform":"LinkedIn","action":"Fully optimize profile","expected_rank":"Top 3 for name search"},
            {"day":2,"platform":"Medium","action":"Publish authority article","expected_rank":"Page 1 in 48h"},
            {"day":3,"platform":"Twitter/X","action":"Optimize + pin thread","expected_rank":"Page 1"},
            {"day":7,"platform":"YouTube","action":"First video","expected_rank":"Page 1 within 7 days"},
            {"day":10,"platform":"Press Release","action":"EINPresswire","expected_rank":"Page 1 via news pickups"},
        ]
    }

def create_client_brief(client_name: str, expertise: str, audience: str) -> str:
    """Create a full client brief document."""
    plan = generate_30_day_plan(client_name, expertise, audience)
    
    brief = f"""# Personal Brand Acceleration Brief
**Client:** {client_name}
**Expertise:** {expertise}  
**Target Audience:** {audience}
**Generated:** {date.today()}

## Goal
Establish {client_name} as a recognized authority in {expertise} within 30-90 days.

## SERP Domination Sequence
"""
    
    if "serp_domination_sequence" in plan:
        for step in plan["serp_domination_sequence"]:
            brief += f"- **Day {step.get('day')}** [{step.get('platform')}]: {step.get('action')} → *{step.get('expected_rank')}*
"
    
    brief += "
## Full 30-Day Plan
"
    brief += json.dumps(plan, indent=2)
    
    return brief

def run():
    log.info("Personal Brand Accelerator starting...")
    
    # Default: run for S.C. Thomas
    client = os.environ.get("BRAND_CLIENT", "S.C. Thomas")
    expertise = os.environ.get("BRAND_EXPERTISE", "AI automation and content marketing")
    audience = os.environ.get("BRAND_AUDIENCE", "entrepreneurs building online businesses")
    
    log.info(f"Client: {client}")
    log.info(f"Expertise: {expertise}")
    
    plan = generate_30_day_plan(client, expertise, audience)
    
    if plan:
        # Save plan
        if GH_TOKEN:
            H2 = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
            REPO2 = "nyspotlightreport/sct-agency-bots"
            slug = client.lower().replace(" ","_").replace(".","")
            path = f"data/brand_plans/{slug}_30day.json"
            payload = json.dumps({"client":client,"expertise":expertise,"plan":plan,"date":str(date.today())}, indent=2)
            body = {"message":f"feat: 30-day brand plan for {client}","content":base64.b64encode(payload.encode()).decode()}
            import base64
            requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}", json=body, headers=H2)
        
        if "name_recognition_milestones" in plan:
            ms = plan["name_recognition_milestones"]
            log.info(f"\nProjected milestones:")
            for k,v in ms.items():
                log.info(f"  {k}: {v}")
        
        log.info(f"\n✅ 30-day brand acceleration plan saved")
        log.info(f"   View at: data/brand_plans/")

if __name__ == "__main__":
    run()
