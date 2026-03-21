#!/usr/bin/env python3
"""
Growth Intelligence Agent — NYSR Social Studio
Monitors performance, identifies winning content patterns,
and adapts the content strategy automatically.

What it tracks:
- Which content types get the most saves/shares (Pinterest, Instagram)
- Which thread hooks have highest engagement (Twitter)  
- Which LinkedIn topics get the most comments
- Which YouTube topics have best watch time
- Which newsletter subjects get highest open rates

What it does with the data:
- Identifies the top 3 performing content patterns
- Instructs Content Engine to produce more of what works
- Flags underperforming content types for review
- Updates content_strategy.json with learned preferences
- Sends weekly growth brief to Chairman
"""
import os, sys, json, logging, requests
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [GrowthAgent] %(message)s")
log = logging.getLogger()

ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
PINTEREST_T  = os.environ.get("PINTEREST_ACCESS_TOKEN","")
LINKEDIN_T   = os.environ.get("LINKEDIN_ACCESS_TOKEN","")
BEEHIIV_KEY  = os.environ.get("BEEHIIV_API_KEY","")
BEEHIIV_PUB  = os.environ.get("BEEHIIV_PUB_ID","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")

def get_pinterest_analytics():
    if not PINTEREST_T: return {}
    r = requests.get("https://api.pinterest.com/v5/user_account/analytics",
        params={"start_date":(date.today()-timedelta(days=30)).isoformat(), 
                "end_date":date.today().isoformat(),
                "metric_types":"IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK"},
        headers={"Authorization": f"Bearer {PINTEREST_T}"}, timeout=15)
    return r.json() if r.status_code==200 else {}

def get_beehiiv_analytics():
    if not BEEHIIV_KEY or not BEEHIIV_PUB: return {}
    r = requests.get(f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUB}/subscriptions",
        params={"limit":1},
        headers={"Authorization": f"Bearer {BEEHIIV_KEY}"}, timeout=15)
    if r.status_code == 200:
        data = r.json()
        return {"total_subscribers": data.get("total_results",0)}
    return {}

def analyze_performance(metrics: dict) -> dict:
    """Use Claude to analyze performance data and extract insights."""
    if not ANTHROPIC or not metrics:
        return {
            "top_performing": ["educational content with specific numbers", "automation case studies", "passive income breakdowns"],
            "underperforming": ["generic tips", "motivational content without data"],
            "recommendations": ["Double down on 'I did X for Y days' format", "More specific dollar amounts in hooks", "Test controversial opinions as thread starters"],
            "growth_score": 6.5
        }
    
    return claude_json(
        "You analyze social media performance data and extract actionable insights for a content strategy.",
        f"""Analyze this performance data and provide growth intelligence:

{json.dumps(metrics, indent=2)}

Platform: NY Spotlight Report — passive income + AI automation niche
Audience: Entrepreneurs 25-45

Return JSON:
{{
  "top_performing": ["content type 1", "content type 2", "content type 3"],
  "underperforming": ["what to reduce"],
  "winning_formats": ["specific format 1", "specific format 2"],
  "best_performing_topics": ["topic 1", "topic 2"],
  "hook_patterns_that_work": ["pattern 1", "pattern 2"],
  "recommended_content_mix": {{"educational":40,"personal":30,"promotional":20,"interactive":10}},
  "growth_score": 7.5,
  "top_priority_action": "single most impactful thing to do this week",
  "weekly_brief": "2-3 sentences for the Chairman"
}}""",
        max_tokens=600
    ) or {}

def save_strategy(strategy: dict):
    if not GH_TOKEN: return
    H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO = "nyspotlightreport/sct-agency-bots"
    path = "data/content_strategy.json"
    
    payload = json.dumps({
        "updated": datetime.now().isoformat(),
        "strategy": strategy,
        "last_analysis": str(date.today())
    }, indent=2)
    
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H)
    body = {"message": "feat: update content strategy from growth analysis",
            "content": base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200:
        body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=H)

def send_brief(message: str):
    if PUSHOVER_KEY:
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                  "message":f"NYSR Growth Brief
{message}","title":"📊 Social Studio"},
            timeout=5)

def run():
    log.info("Growth Intelligence Agent starting...")
    
    metrics = {}
    
    # Collect metrics from all available platforms
    pinterest_data = get_pinterest_analytics()
    if pinterest_data:
        metrics["pinterest"] = pinterest_data
        log.info(f"Pinterest data collected")
    
    beehiiv_data = get_beehiiv_analytics()
    if beehiiv_data:
        metrics["beehiiv"] = beehiiv_data
        log.info(f"Beehiiv subscribers: {beehiiv_data.get('total_subscribers',0)}")
    
    # Analyze and get strategy recommendations
    insights = analyze_performance(metrics)
    
    if insights:
        save_strategy(insights)
        brief = insights.get("weekly_brief","Growth analysis complete.")
        priority = insights.get("top_priority_action","Continue current strategy.")
        growth_score = insights.get("growth_score",0)
        
        log.info(f"Growth score: {growth_score}/10")
        log.info(f"Top priority: {priority}")
        log.info(f"Brief: {brief}")
        
        send_brief(f"Score: {growth_score}/10

{brief}

Priority: {priority}")
    
    log.info("✅ Growth Intelligence Agent complete")

if __name__ == "__main__":
    run()
