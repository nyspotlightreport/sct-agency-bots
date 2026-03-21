#!/usr/bin/env python3
"""
Threat Intelligence Feed — NYSR Fixer PR
Monitors the threat landscape BEFORE it reaches us.

What it watches:
1. Industry regulatory changes (FTC, Google, platform policies)
2. Competitor crises (learn from theirs before ours happens)
3. Backlash trends in our space (AI content, passive income)
4. Platform algorithm changes that could affect our reach
5. Legal/IP activity against similar businesses
6. Negative trend cycles in entrepreneur/AI niche

Why this matters:
The best PR crises to handle are the ones that never happen.
By watching what hits competitors and tracking regulatory signals,
we position AHEAD of incoming headwinds — not react to them.
"""
import os, sys, json, logging, requests, time
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ThreatFeed] %(message)s")
log = logging.getLogger()

NEWSAPI_KEY  = os.environ.get("NEWSAPI_KEY","")
ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")

# Threat vectors to monitor
THREAT_FEEDS = {
    "regulatory": [
        "FTC AI disclosure requirements",
        "FTC influencer marketing rules",
        "Google AI content policy",
        "Google spam update 2026",
        "passive income regulation FTC",
        "AI disclosure law",
    ],
    "platform_changes": [
        "Google algorithm update",
        "LinkedIn algorithm change",
        "Reddit API changes",
        "Medium policy update",
        "YouTube monetization policy",
        "newsletter spam filter",
    ],
    "competitor_crisis": [
        "Jasper AI controversy",
        "Copy.ai complaint",
        "AI content tool fraud",
        "content automation scam",
        "passive income fraud",
    ],
    "industry_backlash": [
        "AI content spam Google",
        "AI generated content banned",
        "passive income misleading",
        "content automation complaints",
        "automated blog spam penalty",
    ],
    "legal_ip": [
        "AI copyright lawsuit",
        "automated content copyright",
        "newsletter unsubscribe lawsuit",
        "cold email CAN-SPAM lawsuit",
        "scraping legal action",
    ]
}

def fetch_threat_news(queries: list, days: int = 3) -> list:
    if not NEWSAPI_KEY: return []
    results = []
    for query in queries[:3]:  # Rate limit
        r = requests.get("https://newsapi.org/v2/everything",
            params={"q": query, "sortBy": "relevancy", "pageSize": 5,
                    "language": "en", "apiKey": NEWSAPI_KEY,
                    "from": (date.today()-timedelta(days=days)).isoformat()},
            timeout=15)
        if r.status_code == 200:
            for article in r.json().get("articles",[]):
                results.append({"query": query, **article})
        time.sleep(0.3)
    return results

def assess_threat_relevance(article: dict) -> dict:
    """Score relevance of a threat signal to our specific business."""
    title = article.get("title","")
    desc  = article.get("description","")[:200]
    query = article.get("query","")
    
    if not ANTHROPIC:
        # Keyword relevance scoring
        relevance = 5
        if any(w in title.lower() for w in ["google","ftc","ban","lawsuit","penalty"]): relevance += 3
        if any(w in title.lower() for w in ["ai content","content automation","passive income"]): relevance += 2
        return {
            "relevance_score": min(10, relevance),
            "threat_category": query.split()[0],
            "impact_on_nysr": "Monitor" if relevance < 7 else "Action required",
            "time_to_impact": "30-90 days" if "regulatory" in query else "immediate"
        }
    
    return claude_json(
        "You assess PR threats for NY Spotlight Report — AI content, passive income, newsletter business.",
        f"""Rate this news item's threat relevance:

Headline: {title}
Description: {desc}
Threat category: {query}

NY Spotlight Report: AI content automation, passive income, newsletter, cold email

Return JSON:
{{
  "relevance_score": 0-10,
  "threat_category": "regulatory|platform|legal|reputation|competitor",
  "impact_on_nysr": "specific impact if this trend continues",
  "time_to_impact": "immediate|1-4 weeks|1-3 months|6+ months",
  "recommended_action": "what to do proactively right now",
  "risk_level": "low|medium|high|critical"
}}""",
        max_tokens=250
    ) or {"relevance_score":3,"impact_on_nysr":"Low relevance","time_to_impact":"6+ months"}

def generate_pre_emptive_response(threat: dict) -> str:
    """Generate pre-emptive positioning to get ahead of a threat."""
    if not ANTHROPIC: return ""
    
    return claude(
        "You write pre-emptive PR positioning — get ahead of threats before they hit.",
        f"""This threat signal was detected:
Headline: {threat.get('title','')}
Impact: {threat.get('assessment',{}).get('impact_on_nysr','')}
Risk: {threat.get('assessment',{}).get('risk_level','')}

Write ONE pre-emptive action NY Spotlight Report should take THIS WEEK to be ahead of this if it materializes.
Be specific. Under 50 words. E.g. "Publish a transparency post about how our AI content works" or "Add disclosure language to all blog posts now".""",
        max_tokens=100
    )

def run():
    log.info("Threat Intelligence Feed starting...")
    
    threats_detected = []
    
    for category, queries in THREAT_FEEDS.items():
        log.info(f"Scanning: {category} ({len(queries)} queries)")
        articles = fetch_threat_news(queries, days=7)
        
        for article in articles:
            assessment = assess_threat_relevance(article)
            
            if assessment.get("relevance_score",0) >= 6:
                threat = {
                    "category": category,
                    "headline": article.get("title",""),
                    "outlet": article.get("source",{}).get("name",""),
                    "url": article.get("url",""),
                    "published": article.get("publishedAt",""),
                    "assessment": assessment
                }
                
                # Get pre-emptive action for high relevance threats
                if assessment.get("relevance_score",0) >= 8:
                    threat["pre_emptive_action"] = generate_pre_emptive_response(threat)
                
                threats_detected.append(threat)
                log.warning(f"⚠️  THREAT [{assessment.get('risk_level','?').upper()}]: {article.get('title','')[:70]}")
    
    log.info(f"
Threats detected: {len(threats_detected)}")
    
    # Sort by relevance
    threats_detected.sort(key=lambda x: x.get("assessment",{}).get("relevance_score",0), reverse=True)
    
    # Alert on high relevance threats
    critical = [t for t in threats_detected if t.get("assessment",{}).get("risk_level") in ["high","critical"]]
    if critical:
        msg = f"⚠️ {len(critical)} HIGH RELEVANCE threats detected

"
        for t in critical[:3]:
            msg += f"• {t['headline'][:60]}
  Impact: {t['assessment'].get('impact_on_nysr','')[:60]}

"
        if PUSHOVER_KEY:
            requests.post("https://api.pushover.net/1/messages.json",
                data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                      "message":msg,"title":"🛡️ NYSR Threat Intelligence"},timeout=5)
    
    # Save report
    if GH_TOKEN:
        import base64
        H2 = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        REPO2 = "nyspotlightreport/sct-agency-bots"
        path = "data/intelligence/threat_feed.json"
        payload = json.dumps({"date":str(date.today()),"threats":threats_detected[:20]},indent=2)
        body = {"message":f"intel: threat feed — {len(threats_detected)} signals",
                "content":base64.b64encode(payload.encode()).decode()}
        r = requests.get(f"https://api.github.com/repos/{REPO2}/contents/{path}", headers=H2)
        if r.status_code==200: body["sha"]=r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}",json=body,headers=H2)
    
    log.info("✅ Threat Intelligence Feed complete")
    return threats_detected

if __name__ == "__main__":
    run()
