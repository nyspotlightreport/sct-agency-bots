#!/usr/bin/env python3
"""
Journalist & Influencer Tracker — NYSR Fixer PR
Monitors what reporters in our industry are writing about.
When a journalist covers a topic we should be in — we pitch them
BEFORE they finish the article (the best time to get quoted).

Tracks:
- Journalists who cover AI tools, content marketing, passive income
- What they published recently (topics + outlets)
- When they ask for sources (HARO-style requests)
- Their editorial calendar patterns (when they publish what topics)
- Engagement signals (when they ask questions on Twitter = pitchable moment)
"""
import os, sys, json, logging, requests, time
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [JournalistTracker] %(message)s")
log = logging.getLogger()

NEWSAPI_KEY  = os.environ.get("NEWSAPI_KEY","")
ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
GMAIL_USER   = os.environ.get("GMAIL_USER","")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")

# Known journalists who cover our niche
TARGET_JOURNALISTS = [
    # AI / Tech journalists
    {"name":"Karissa Bell",       "outlet":"Engadget",    "beat":"AI tools",         "twitter":"@karissabell",   "email":""},
    {"name":"Janko Roettgers",    "outlet":"Protocol",    "beat":"AI/tech",          "twitter":"@janko",         "email":""},
    {"name":"Will Douglas Heaven","outlet":"MIT Tech Review","beat":"AI",             "twitter":"@willDH",        "email":""},
    
    # Entrepreneur/Business journalists
    {"name":"Valentina Zarya",    "outlet":"Fortune",     "beat":"entrepreneurship", "twitter":"@vzarya",        "email":"tips@fortune.com"},
    {"name":"Arianne Cohen",      "outlet":"Bloomberg",   "beat":"work/startups",    "twitter":"@ariannecohen",  "email":""},
    {"name":"Leigh Buchanan",     "outlet":"Inc Magazine","beat":"small business",   "twitter":"@leighbuchanan", "email":"tips@inc.com"},
    
    # Content/Marketing journalists
    {"name":"Digiday Staff",      "outlet":"Digiday",     "beat":"media/marketing",  "twitter":"@Digiday",       "email":"tips@digiday.com"},
    {"name":"Joe Pulizzi",        "outlet":"Content Inc","beat":"content marketing", "twitter":"@JoePulizzi",    "email":""},
    
    # Passive income / personal finance
    {"name":"Zack Friedman",      "outlet":"Forbes",      "beat":"personal finance", "twitter":"@zackfriedman", "email":"forbesstaff@forbes.com"},
    {"name":"Chris Guillebeau",   "outlet":"Side Hustle","beat":"side hustles",      "twitter":"@chrisguillebeau","email":"chris@sidehustleschool.com"},
]

# HARO / Qwoted query patterns to watch
SOURCE_REQUEST_PATTERNS = [
    "AI content tools",
    "content automation",
    "passive income",
    "AI entrepreneur",
    "solopreneur",
    "content marketing automation",
    "replace content team",
    "AI writing tools",
]

def fetch_journalist_recent_articles(journalist: dict) -> list:
    """Get what a journalist published recently."""
    if not NEWSAPI_KEY: return []
    r = requests.get("https://newsapi.org/v2/everything",
        params={"q": journalist["name"], "sources": journalist["outlet"].lower().replace(" ","-"),
                "sortBy": "publishedAt", "pageSize": 5, "apiKey": NEWSAPI_KEY,
                "from": (date.today()-timedelta(days=14)).isoformat()},
        timeout=15)
    return r.json().get("articles",[]) if r.status_code==200 else []

def check_haro_patterns() -> list:
    """Check if any journalists are asking for sources in our niche."""
    # HARO sends 3x daily. We scan NewsAPI for journalist asks.
    opportunities = []
    for pattern in SOURCE_REQUEST_PATTERNS:
        r = requests.get("https://newsapi.org/v2/everything",
            params={"q": f"{pattern} source expert quote",
                    "sortBy":"publishedAt","pageSize":5,
                    "apiKey":NEWSAPI_KEY,
                    "from":(date.today()-timedelta(days=2)).isoformat()},
            timeout=15) if NEWSAPI_KEY else type("R",(),{"status_code":0})()
        if getattr(r,"status_code",0) == 200:
            for article in r.json().get("articles",[]):
                if any(ask in article.get("title","").lower() for ask in ["expert","source","comment","opinion"]):
                    opportunities.append({
                        "pattern": pattern,
                        "article": article.get("title",""),
                        "outlet": article.get("source",{}).get("name",""),
                        "url": article.get("url",""),
                        "published": article.get("publishedAt",""),
                        "pitch_window": "24-48h"
                    })
    return opportunities

def identify_pitch_windows(journalist: dict, recent_articles: list) -> dict:
    """
    Identify the optimal time to pitch a journalist.
    - When they just covered a related topic (they're in the story)
    - When their outlet has an editorial gap we can fill
    - When they're asking questions on Twitter (source hunting)
    """
    if not recent_articles:
        return {"window": "cold", "reason": "No recent articles found", "suggested_angle": ""}
    
    recent_topics = [a.get("title","") for a in recent_articles[:3]]
    
    return {
        "window": "warm",
        "reason": f"Published {len(recent_articles)} articles in last 14 days",
        "recent_coverage": recent_topics,
        "suggested_angle": f"SC Thomas perspective on {journalist.get('beat','')} — complement to their recent coverage"
    }

def generate_pitch(journalist: dict, window: dict) -> dict:
    """Write a personalized pitch based on their recent coverage."""
    if not ANTHROPIC or window.get("window") == "cold":
        return {
            "subject": f"Source for {journalist['outlet']} story on AI content automation",
            "body": f"Hi {journalist['name'].split()[0]},

I saw your recent work on {journalist['beat']} — I've been building in that space.

I'm SC Thomas, founder of NY Spotlight Report. I've replaced an entire content marketing team with 63 AI bots for $70/month. Happy to be a source if you're covering AI tools, content automation, or the future of solopreneurship.

Full system breakdown: nyspotlightreport.com

— SC Thomas"
        }
    
    return claude_json(
        "You write expert journalist pitches. 80 words max. Reference their recent work specifically. Lead with the story value.",
        f"""Write a journalist pitch to {journalist['name']} at {journalist['outlet']}.
Their beat: {journalist['beat']}
Recent coverage: {window.get('recent_coverage',[])}
My angle: {window.get('suggested_angle','')}

Return JSON: {{subject: str (40 chars max), body: str (under 80 words)}}""",
        max_tokens=200
    ) or {}

def run():
    log.info("Journalist Tracker starting...")
    log.info(f"Tracking {len(TARGET_JOURNALISTS)} journalists across {len(set(j['outlet'] for j in TARGET_JOURNALISTS))} outlets")
    
    pitchable = []
    
    for journalist in TARGET_JOURNALISTS:
        # Get their recent work
        articles = fetch_journalist_recent_articles(journalist)
        window = identify_pitch_windows(journalist, articles)
        
        if window["window"] == "warm":
            log.info(f"🎯 PITCH WINDOW: {journalist['name']} ({journalist['outlet']}) — {window['reason']}")
            pitch = generate_pitch(journalist, window)
            if pitch:
                pitchable.append({
                    "journalist": journalist["name"],
                    "outlet": journalist["outlet"],
                    "email": journalist.get("email",""),
                    "window": window,
                    "pitch": pitch
                })
        
        time.sleep(0.5)
    
    # Check HARO-style opportunities
    haro_opps = check_haro_patterns()
    if haro_opps:
        log.info(f"📰 Source request opportunities: {len(haro_opps)}")
        for opp in haro_opps[:3]:
            log.info(f"  {opp['outlet']}: '{opp['article'][:60]}'")
    
    log.info(f"
Pitchable journalists this week: {len(pitchable)}")
    for p in pitchable:
        log.info(f"  → {p['journalist']} | {p['outlet']}")
        if p.get("pitch",{}).get("subject"):
            log.info(f"     Subject: {p['pitch']['subject']}")
    
    # Save report
    if GH_TOKEN:
        import base64
        H2 = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        REPO2 = "nyspotlightreport/sct-agency-bots"
        path = "data/intelligence/journalist_tracker.json"
        payload = json.dumps({"date":str(date.today()),"pitchable":pitchable,"haro":haro_opps},indent=2)
        body = {"message":f"intel: journalist tracker — {len(pitchable)} pitch windows",
                "content":base64.b64encode(payload.encode()).decode()}
        r = requests.get(f"https://api.github.com/repos/{REPO2}/contents/{path}", headers=H2)
        if r.status_code==200: body["sha"]=r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}",json=body,headers=H2)
    
    log.info("✅ Journalist tracker complete")
    return pitchable

if __name__ == "__main__":
    run()
