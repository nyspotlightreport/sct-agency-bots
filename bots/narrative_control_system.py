#!/usr/bin/env python3
"""
Narrative Control System — NYSR Fixer PR
╔══════════════════════════════════════════════════════════════╗
║  OBJECTIVE: Shape, shift, or dominate the public narrative  ║
║  around any topic, person, brand, or keyword.               ║
╚══════════════════════════════════════════════════════════════╝

Use cases:
1. Brand narrative building — define how a brand is perceived
2. Topic ownership — become THE authority voice on any subject
3. Counter-narrative — displace negative coverage with positive volume
4. Thought leadership — associate a name with an expertise area

Strategy:
- "The most common story wins." — control what people read first
- 20 pieces on a topic published across authority platforms
  = Google treats you as the definitive source
- Fresh content + high DA platforms + internal linking
  = page 1 domination within 30-90 days

Methods: All white-hat. Factual content. Legitimate PR.
"""
import os, sys, json, logging, requests, time
from datetime import datetime, date
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [NarrativeControl] %(message)s")
log = logging.getLogger()

ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY","")
MEDIUM_T    = os.environ.get("MEDIUM_INTEGRATION_TOKEN","")
GH_TOKEN    = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")

PR_SYSTEM = """You are a world-class PR strategist and narrative architect.
You understand how public perception is built, shifted, and maintained.
Write with authority, specificity, and strategic intent.
All content is factual, professional, and serves legitimate communication goals."""

# Narrative frameworks — proven structures that shape perception
NARRATIVE_FRAMEWORKS = {
    "underdog_triumph": "The odds were against them. Here is how they built something remarkable anyway.",
    "category_creator":  "This didn't exist before them. Now it's the standard everyone else follows.",
    "trusted_expert":    "After [X] years in [field], this is what they know that nobody else does.",
    "community_builder": "They didn't just build a business. They built a movement of people who [shared value].",
    "problem_solver":    "Everyone saw the problem. Only [name] built the solution.",
    "pioneer":           "Before [name], [industry] worked like [old way]. After: everything changed.",
}

def generate_narrative_campaign(subject: str, narrative_goal: str, 
                                  framework: str = "trusted_expert",
                                  key_facts: list = None) -> dict:
    """
    Generate a complete narrative campaign.
    
    subject: Who or what the campaign is about
    narrative_goal: What we want people to believe/feel/know
    framework: Which story structure to use
    key_facts: Real facts to anchor the narrative in truth
    """
    if key_facts is None:
        key_facts = []
    
    frame = NARRATIVE_FRAMEWORKS.get(framework, NARRATIVE_FRAMEWORKS["trusted_expert"])
    
    if not ANTHROPIC:
        return _static_narrative(subject, narrative_goal)
    
    return claude_json(
        PR_SYSTEM,
        f"""Create a complete narrative control campaign:

Subject: {subject}
Goal: {narrative_goal}
Story framework: {frame}
Key facts to anchor in: {', '.join(key_facts) if key_facts else 'Use general entrepreneurship narrative'}

Generate ALL of the following:

Return JSON:
{{
  "master_narrative": {{
    "one_sentence": "The defining sentence — what this person/brand IS",
    "elevator_pitch": "3-sentence narrative that goes in every bio",
    "origin_story": "150-word origin story — compelling, human, true to facts",
    "vision_statement": "Where they are going (future-oriented)",
    "proof_points": ["Fact 1 that proves the narrative", "Fact 2", "Fact 3"]
  }},
  "content_blitz": [
    {{
      "platform": "Medium",
      "title": "Keyword-rich article title",
      "angle": "Specific editorial angle for this platform",
      "outline": ["H2 section 1", "H2 section 2", "H2 section 3"],
      "target_keyword": "exact keyword to rank for",
      "estimated_serp_position": "2-10 (Medium ranks fast)"
    }},
    {{
      "platform": "LinkedIn Article",
      "title": "Professional thought leadership title",
      "angle": "B2B credibility angle",
      "outline": ["Section 1", "Section 2", "Section 3"],
      "target_keyword": "professional keyword",
      "estimated_serp_position": "1-5 (LinkedIn + name = top 3)"
    }},
    {{
      "platform": "YouTube",
      "title": "Video title",
      "angle": "Visual storytelling angle",
      "outline": ["Intro hook", "Main content points", "CTA"],
      "target_keyword": "video keyword",
      "estimated_serp_position": "3-8"
    }},
    {{
      "platform": "Quora",
      "title": "Question to answer",
      "angle": "Expert authority answer",
      "outline": ["Direct answer", "Context", "Evidence", "CTA"],
      "target_keyword": "long-tail keyword",
      "estimated_serp_position": "4-10"
    }},
    {{
      "platform": "Press Release (EINPresswire)",
      "title": "Newswire headline",
      "angle": "News hook",
      "outline": ["Lead paragraph", "Quote", "Background", "Boilerplate"],
      "target_keyword": "news keyword",
      "estimated_serp_position": "2-6 (newswires rank fast)"
    }}
  ],
  "platform_bio_variations": {{
    "twitter_bio": "160 chars — punchy, keyword-rich",
    "instagram_bio": "150 chars — visual, personality-driven",
    "linkedin_headline": "120 chars — professional, keyword-rich",
    "medium_bio": "200 chars — authoritative",
    "author_bio_short": "50 words — third person, impressive",
    "author_bio_long": "150 words — third person, full story"
  }},
  "media_hook_angles": [
    "Podcast pitch angle 1 (most provocative/interesting)",
    "Podcast pitch angle 2 (data-driven)",
    "Press story angle (news value)",
    "Newsletter feature angle (community value)"
  ],
  "serp_projection": {{
    "day_30": "Expected search results — X of top 10 controlled",
    "day_60": "Expected search results — Y of top 10 controlled",
    "day_90": "Full page 1 ownership projection",
    "keywords_targeted": ["kw1","kw2","kw3","kw4","kw5"]
  }}
}}""",
        max_tokens=4000
    ) or _static_narrative(subject, narrative_goal)

def _static_narrative(subject, goal):
    return {
        "master_narrative": {
            "one_sentence": f"{subject} is the AI entrepreneur who automated an entire content marketing operation and documented every step.",
            "elevator_pitch": f"{subject} built 63 AI bots that run his entire content business while he sleeps. As founder of NY Spotlight Report, he helps entrepreneurs build the same systems — without the years of trial and error.",
            "origin_story": f"Six months ago, {subject} was spending 20+ hours a week on content marketing and getting nowhere. Instead of hiring a team, he built one. 63 AI bots later, his business publishes daily blogs, weekly newsletters, posts to six social platforms, and closes clients automatically — all for $70/month.",
            "vision_statement": "A world where every entrepreneur can have a Fortune 500 content operation without Fortune 500 costs.",
            "proof_points": ["63 AI bots running autonomously", "Replaced $4,000/month content team", "Full system costs $70/month to operate"]
        }
    }

def save_narrative_campaign(subject: str, campaign: dict):
    if not GH_TOKEN: return
    H2 = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO2 = "nyspotlightreport/sct-agency-bots"
    slug = subject.lower().replace(" ","-").replace(".","")[:30]
    path = f"data/narrative_campaigns/{slug}_{date.today()}.json"
    payload = json.dumps({"subject": subject, "created": str(date.today()), "campaign": campaign}, indent=2)
    body = {"message": f"feat: narrative campaign — {subject}",
            "content": base64.b64encode(payload.encode()).decode()}
    requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}", json=body, headers=H2)
    log.info(f"✅ Narrative campaign saved: {path}")

def run(subject=None, goal=None, framework="trusted_expert"):
    subject  = subject  or os.environ.get("CAMPAIGN_SUBJECT",  "S.C. Thomas")
    goal     = goal     or os.environ.get("CAMPAIGN_GOAL",     "establish as #1 AI automation expert for entrepreneurs")
    framework= framework or os.environ.get("CAMPAIGN_FRAMEWORK","trusted_expert")
    
    log.info(f"Narrative Control System starting")
    log.info(f"Subject:   {subject}")
    log.info(f"Goal:      {goal}")
    log.info(f"Framework: {framework} — {NARRATIVE_FRAMEWORKS.get(framework,'')[:60]}")
    
    campaign = generate_narrative_campaign(subject, goal, framework)
    
    if campaign:
        save_narrative_campaign(subject, campaign)
        
        if "master_narrative" in campaign:
            mn = campaign["master_narrative"]
            log.info(f"\nMASTER NARRATIVE:")
            log.info(f"  One sentence: {mn.get('one_sentence','')[:80]}")
            log.info(f"  Elevator: {mn.get('elevator_pitch','')[:80]}")
        
        if "serp_projection" in campaign:
            sp = campaign["serp_projection"]
            log.info(f"\nSERP PROJECTION:")
            log.info(f"  Day 30:  {sp.get('day_30','')}")
            log.info(f"  Day 60:  {sp.get('day_60','')}")
            log.info(f"  Day 90:  {sp.get('day_90','')}")
        
        if "content_blitz" in campaign:
            log.info(f"\nCONTENT BLITZ: {len(campaign['content_blitz'])} pieces across platforms")
            for piece in campaign["content_blitz"]:
                log.info(f"  {piece.get('platform','')}: '{piece.get('title','')[:50]}'")
    
    log.info("\n✅ Narrative campaign complete. Assets in data/narrative_campaigns/")

if __name__ == "__main__":
    run()
