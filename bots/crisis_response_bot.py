#!/usr/bin/env python3
"""
Crisis Response Bot — NYSR Fixer PR
╔══════════════════════════════════════════════════════════════╗
║  OBJECTIVE: Counter negative coverage or bad SERP results  ║
║  with a coordinated wave of positive, authoritative content ║
╚══════════════════════════════════════════════════════════════╝

How it works:
When negative content ranks for your name/brand:
1. Identify the negative URLs and their DA scores
2. Publish 5-10x more positive content with higher authority
3. Build internal links pointing to positive content
4. Syndicate across all platforms simultaneously
5. Monitor weekly until negative content drops to page 2+

Timeline:
  Mild negatives (DA < 30): 2-4 weeks to displace
  Medium negatives (DA 30-60): 4-8 weeks
  Strong negatives (DA 60+): 8-16 weeks + press placement strategy

Method: Content volume + authority + freshness = SERP displacement
"""
import os, sys, json, logging, requests
from datetime import datetime, date
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CrisisBot] %(message)s")
log = logging.getLogger()

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
MEDIUM_T  = os.environ.get("MEDIUM_INTEGRATION_TOKEN","")
GH_TOKEN  = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
AHREFS    = os.environ.get("AHREFS_API_KEY","")

PR_SYSTEM = """You are a crisis communications expert and reputation management specialist.
You create strategic, factual counter-narratives and positive content campaigns.
All content must be truthful, professional, and serve legitimate reputation management goals."""

def analyze_serp(target_keyword: str) -> list:
    """Check current SERP for a keyword using Ahrefs or web."""
    if not AHREFS: return []
    r = requests.get("https://api.ahrefs.com/v3/serp-overview",
        params={"keyword": target_keyword, "country": "us",
                "select": "url,position,title,domain_rating"},
        headers={"Authorization": f"Bearer {AHREFS}"}, timeout=15)
    return r.json().get("positions",[]) if r.status_code==200 else []

def generate_counter_content(target: str, negative_angle: str, 
                              positive_facts: list, urgency: str = "normal") -> dict:
    """Generate rapid-deploy counter-content."""
    
    speed_map = {
        "emergency": "Deploy within 24 hours. Maximum volume. All platforms simultaneously.",
        "urgent":    "Deploy within 72 hours. 5-7 platforms. Weekly monitoring.",
        "normal":    "Deploy over 2 weeks. Full platform sweep. Monthly monitoring."
    }
    
    if not ANTHROPIC:
        return _static_counter_content(target, negative_angle, positive_facts)
    
    return claude_json(
        PR_SYSTEM,
        f"""Create a counter-narrative content campaign:

Target: {target}
Negative narrative to displace: {negative_angle}
Positive facts to amplify: {', '.join(positive_facts)}
Urgency level: {urgency} — {speed_map.get(urgency,'')}

Strategy: Don't attack the negative. Flood it with positive.
More content = more SERP real estate = negative pushed down.

Return JSON:
{{
  "counter_narrative_angle": "The positive story angle that counters without engaging the negative",
  "immediate_actions": [
    "Action 1 (do today)",
    "Action 2 (do today)",
    "Action 3 (do this week)"
  ],
  "content_pieces": [
    {{
      "platform": "Medium",
      "title": "Positive article title that ranks for same keyword",
      "angle": "Specific angle",
      "target_keyword": "keyword the negative content ranks for",
      "publish_priority": 1
    }},
    {{
      "platform": "LinkedIn",
      "title": "Professional post title",
      "angle": "Professional perspective",
      "target_keyword": "keyword",
      "publish_priority": 2
    }},
    {{
      "platform": "YouTube",
      "title": "Video title — ranks fast",
      "angle": "Video angle",
      "target_keyword": "keyword",
      "publish_priority": 3
    }},
    {{
      "platform": "Press Release",
      "title": "News angle that counters narrative",
      "angle": "Fresh news hook",
      "target_keyword": "keyword",
      "publish_priority": 4
    }},
    {{
      "platform": "Quora",
      "title": "Question that targets same keyword",
      "angle": "Expert answer that presents the positive view",
      "target_keyword": "keyword",
      "publish_priority": 5
    }}
  ],
  "monitoring_keywords": ["kw1","kw2","kw3"],
  "displacement_timeline": {{
    "week_1": "Expected SERP change",
    "week_4": "Expected SERP change",
    "week_8": "Expected SERP change"
  }},
  "escalation_triggers": [
    "If negative content gains traction, do X",
    "If DA of negative source increases, do Y"
  ]
}}""",
        max_tokens=2500
    ) or _static_counter_content(target, negative_angle, positive_facts)

def _static_counter_content(target, negative_angle, facts):
    return {
        "counter_narrative_angle": f"The real story of {target} — built on documented results, not opinions",
        "immediate_actions": [
            f"Publish a Medium article titled: '{target}: The Results Speak for Themselves'",
            f"Post a LinkedIn article with 3 verified results + client quotes",
            f"Submit a press release to EINPresswire with measurable outcomes"
        ],
        "content_pieces": [
            {"platform":"Medium","title":f"What {target} Actually Built (with Real Numbers)","publish_priority":1},
            {"platform":"LinkedIn","title":f"{target}: 90 Days of Documented Results","publish_priority":2},
            {"platform":"YouTube","title":f"The True Story of {target}","publish_priority":3},
        ]
    }

def run():
    log.info("Crisis Response Bot ready")
    log.info("Usage: Set CRISIS_TARGET, CRISIS_NEGATIVE, CRISIS_FACTS env vars")
    
    target   = os.environ.get("CRISIS_TARGET", "")
    negative = os.environ.get("CRISIS_NEGATIVE", "")
    facts    = os.environ.get("CRISIS_FACTS", "").split(",") if os.environ.get("CRISIS_FACTS") else []
    urgency  = os.environ.get("CRISIS_URGENCY", "normal")
    
    if not target:
        log.info("No CRISIS_TARGET set — bot ready, awaiting campaign trigger")
        log.info("To activate: Set CRISIS_TARGET='[name/brand]' and re-run")
        return
    
    log.info(f"Running crisis response for: {target}")
    log.info(f"Negative angle to counter: {negative}")
    log.info(f"Urgency: {urgency}")
    
    content = generate_counter_content(target, negative, facts, urgency)
    
    if content:
        # Save crisis plan
        if GH_TOKEN:
            import base64
            H2 = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
            REPO2 = "nyspotlightreport/sct-agency-bots"
            slug = target.lower().replace(" ","-")[:20]
            path = f"data/crisis_responses/{slug}_{date.today()}.json"
            payload = json.dumps({"target":target,"negative":negative,"response":content,"date":str(date.today())}, indent=2)
            body = {"message":f"feat: crisis response for {target}","content":base64.b64encode(payload.encode()).decode()}
            requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}", json=body, headers=H2)
        
        log.info(f"\nIMMEDIATE ACTIONS:")
        for action in content.get("immediate_actions",[]):
            log.info(f"  → {action}")
        
        log.info(f"\nCONTENT TO DEPLOY (in order):")
        for piece in content.get("content_pieces",[]):
            log.info(f"  {piece.get('publish_priority','?')}. [{piece.get('platform','')}] {piece.get('title','')[:60]}")
        
        log.info(f"\n✅ Crisis response plan ready — deploy in priority order")

if __name__ == "__main__":
    run()
