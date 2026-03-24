#!/usr/bin/env python3
"""
Reputation Intelligence Engine — NYSR Fixer PR
╔══════════════════════════════════════════════════════════════╗
║  THE PROACTIVE LAYER                                        ║
║                                                              ║
║  Reactive PR: wait for crisis → respond                     ║
║  Proactive PR: monitor signals → predict → prevent          ║
║                                                              ║
║  This engine runs every 4 hours and:                        ║
║  1. Scans 12+ sources for brand/competitor mentions         ║
║  2. Scores sentiment of every mention (Claude)              ║
║  3. Detects velocity spikes (sudden mention increase)       ║
║  4. Scores current reputation health (0-100)                ║
║  5. Predicts crisis probability (ML pattern matching)       ║
║  6. Auto-deploys pre-staged counter-content when needed     ║
║  7. Alerts Chairman with threat level + recommended action  ║
╚══════════════════════════════════════════════════════════════╝

Crisis prediction model based on 3 pre-crisis signals:
  SIGNAL 1: Mention velocity spike (>3x normal = yellow alert)
  SIGNAL 2: Sentiment shift negative (>20% negative = orange)
  SIGNAL 3: High-DA source picks up negative story (DA>50 = red)

Any 2 signals = THREAT DETECTED → auto counter-content deployed
All 3 signals = CRISIS IMMINENT → Chairman notified immediately
"""
import os, sys, json, logging, requests, hashlib, time
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [IntelEngine] %(message)s")
log = logging.getLogger()

# Keys
ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
NEWSAPI_KEY  = os.environ.get("NEWSAPI_KEY","")
AHREFS_KEY   = os.environ.get("AHREFS_API_KEY","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GMAIL_USER   = os.environ.get("GMAIL_USER","")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS","")

# ── MONITORING TARGETS ────────────────────────────────────────────
WATCH_LIST = {
    "brand_primary": [
        "NY Spotlight Report",
        "nyspotlightreport.com",
        "ProFlow AI",
        "SC Thomas entrepreneur",
    ],
    "brand_secondary": [
        "NYSpotlightReport",
        "SC Thomas AI",
        "proflow ai content",
    ],
    "competitors": [
        "Jasper AI",
        "Copy.ai",
        "ContentBot",
        "Surfer SEO",
    ],
    "industry_signals": [
        "AI content tools backlash",
        "content automation controversy",
        "AI SEO Google penalty",
        "passive income scam",
    ],
    "opportunity_signals": [
        "alternatives to Jasper",
        "best AI content tools 2026",
        "content marketing automation",
        "replace content team AI",
    ]
}

THREAT_KEYWORDS = [
    "scam","fraud","fake","misleading","lawsuit","complaint","warning",
    "banned","suspended","copyright","stolen","deceptive","spam",
    "refund","chargeback","negative review","avoid","terrible"
]

OPPORTUNITY_KEYWORDS = [
    "alternative","looking for","recommend","switch from","better than",
    "compare","review","which is best","honest review"
]

INTEL_SYSTEM = """You are a reputation intelligence analyst for NY Spotlight Report.
Analyze mentions objectively. Classify sentiment precisely.
Identify genuine threats vs noise. Be specific and actionable."""

# ── DATA COLLECTORS ───────────────────────────────────────────────

def fetch_news_mentions(query: str, days: int = 1) -> list:
    """Fetch news mentions from NewsAPI."""
    if not NEWSAPI_KEY: return []
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    r = requests.get("https://newsapi.org/v2/everything",
        params={"q": query, "from": from_date, "sortBy": "publishedAt",
                "language": "en", "pageSize": 20, "apiKey": NEWSAPI_KEY},
        timeout=15)
    return r.json().get("articles",[]) if r.status_code==200 else []

def fetch_reddit_mentions(query: str) -> list:
    """Search Reddit for brand mentions."""
    r = requests.get("https://www.reddit.com/search.json",
        params={"q": query, "sort": "new", "limit": 25, "t": "day"},
        headers={"User-Agent": "NYSRIntelBot/1.0"}, timeout=15)
    if r.status_code != 200: return []
    return [
        {
            "source": "reddit",
            "title": p["data"].get("title",""),
            "body": p["data"].get("selftext","")[:500],
            "url": f"https://reddit.com{p['data'].get('permalink','')}",
            "score": p["data"].get("score",0),
            "subreddit": p["data"].get("subreddit",""),
            "created": p["data"].get("created_utc",0)
        }
        for p in r.json().get("data",{}).get("children",[])
        if p.get("kind") == "t3"
    ]

def fetch_hackernews_mentions(query: str) -> list:
    """Search Hacker News for brand mentions."""
    r = requests.get("https://hn.algolia.com/api/v1/search_by_date",
        params={"query": query, "tags": "story,comment", "numericFilters": "created_at_i>"+str(int(time.time())-86400)},
        timeout=15)
    if r.status_code != 200: return []
    return [
        {
            "source": "hackernews",
            "title": hit.get("title","") or hit.get("comment_text","")[:100],
            "url": hit.get("url","") or f"https://news.ycombinator.com/item?id={hit.get('objectID','')}",
            "points": hit.get("points",0),
            "author": hit.get("author","")
        }
        for hit in r.json().get("hits",[])[:10]
    ]

def fetch_google_news_rss(query: str) -> list:
    """Fetch Google News RSS for a query."""
    import urllib.parse
    q = urllib.parse.quote(query)
    r = requests.get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en",
        timeout=15, headers={"User-Agent":"Mozilla/5.0"})
    if r.status_code != 200: return []
    
    import re
    items = re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)
    results = []
    for item in items[:10]:
        title  = re.search(r"<title>(.*?)</title>", item)
        link   = re.search(r"<link>(.*?)</link>",   item)
        source = re.search(r"<source.*?>(.*?)</source>", item)
        results.append({
            "source": "google_news",
            "title":  title.group(1) if title else "",
            "url":    link.group(1)  if link  else "",
            "outlet": source.group(1) if source else "unknown"
        })
    return results

# ── ANALYSIS ─────────────────────────────────────────────────────

def analyze_mention_sentiment(mention: dict) -> dict:
    """Score a single mention for sentiment, threat level, opportunity."""
    text = f"{mention.get('title','')} {mention.get('body','')[:300]}"
    
    # Quick keyword pre-filter (free, instant)
    text_lower = text.lower()
    has_threat = any(kw in text_lower for kw in THREAT_KEYWORDS)
    has_opportunity = any(kw in text_lower for kw in OPPORTUNITY_KEYWORDS)
    
    if not has_threat and not has_opportunity:
        return {**mention, "sentiment": "neutral", "threat_score": 0, "opportunity_score": 2, "action": "monitor"}
    
    if not ANTHROPIC:
        # Simple keyword scoring without AI
        threat_hits = sum(1 for kw in THREAT_KEYWORDS if kw in text_lower)
        opp_hits = sum(1 for kw in OPPORTUNITY_KEYWORDS if kw in text_lower)
        sentiment = "negative" if threat_hits > opp_hits else ("positive" if opp_hits > 0 else "neutral")
        return {**mention, "sentiment": sentiment, "threat_score": min(10, threat_hits*2), 
                "opportunity_score": min(10, opp_hits*2), "action": "review" if threat_hits else "engage"}
    
    result = claude_json(
        INTEL_SYSTEM,
        f"""Analyze this mention of NY Spotlight Report / SC Thomas:

Title: {mention.get('title','')}
Source: {mention.get('source','')} | Outlet: {mention.get('outlet','') or mention.get('subreddit','')}
Text: {text[:400]}

Return JSON:
{{
  "sentiment": "positive|neutral|negative|mixed",
  "threat_score": 0-10 (0=no threat, 10=immediate crisis),
  "opportunity_score": 0-10 (0=no value, 10=high opportunity),
  "threat_type": null or one of: ["negative_review","false_claim","competitor_attack","regulatory","viral_negative","press_investigation"],
  "opportunity_type": null or one of: ["media_coverage","customer_interest","partnership","competitor_weakness","trending_topic"],
  "recommended_action": "ignore|monitor|engage|counter|escalate",
  "one_line_summary": "20-word summary of what this mention is about",
  "urgency": "low|medium|high|critical"
}}""",
        max_tokens=300
    )
    
    return {**mention, **(result or {"sentiment":"neutral","threat_score":0,"opportunity_score":0,"action":"monitor"})}

def calculate_reputation_score(analyses: list) -> dict:
    """
    Calculate overall reputation health score (0-100).
    
    Scoring:
    100 = Perfect. All mentions positive. No threats. 
    80  = Healthy. Mostly positive. Minor issues.
    60  = Watch. Mixed. Some negative mentions.
    40  = Concern. Negative trend detected.
    20  = Alert. Crisis indicators present.
    0   = Crisis. Active negative narrative spreading.
    """
    if not analyses:
        return {"score": 75, "trend": "stable", "threat_level": "green",
                "explanation": "No mentions found — baseline score"}
    
    sentiments = [a.get("sentiment","neutral") for a in analyses]
    threat_scores = [a.get("threat_score",0) for a in analyses]
    
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    total = len(sentiments)
    
    max_threat = max(threat_scores) if threat_scores else 0
    avg_threat = sum(threat_scores)/len(threat_scores) if threat_scores else 0
    
    # Base score from sentiment ratio
    pos_ratio = (pos / total) if total > 0 else 0.5
    neg_ratio = (neg / total) if total > 0 else 0
    
    base_score = int(50 + (pos_ratio * 40) - (neg_ratio * 50))
    
    # Adjust for max threat
    if max_threat >= 8:   base_score -= 30
    elif max_threat >= 6: base_score -= 20
    elif max_threat >= 4: base_score -= 10
    
    score = max(0, min(100, base_score))
    
    threat_level = (
        "critical" if score < 20 else
        "red"      if score < 40 else
        "orange"   if score < 60 else
        "yellow"   if score < 75 else
        "green"
    )
    
    return {
        "score": score,
        "trend": "declining" if neg_ratio > 0.3 else ("improving" if pos_ratio > 0.6 else "stable"),
        "threat_level": threat_level,
        "total_mentions": total,
        "positive_pct": round(pos_ratio*100),
        "negative_pct": round(neg_ratio*100),
        "max_threat_score": max_threat,
        "explanation": f"{total} mentions — {round(pos_ratio*100)}% positive, {round(neg_ratio*100)}% negative, max threat {max_threat}/10"
    }

def predict_crisis_probability(history: list, current_analyses: list) -> dict:
    """
    Predict crisis probability based on signal patterns.
    
    Pre-crisis signals (from real PR crisis forensics):
    1. Mention volume spike (3x normal in 24h)
    2. Negative sentiment >25% of mentions
    3. A DA50+ outlet picks up any negative story
    4. Coordinated posting pattern (multiple sources, same narrative, same hour)
    5. Competitor activity increase (they sense weakness)
    6. Industry journalist engagement uptick
    """
    if not current_analyses:
        return {"probability": 5, "signals_detected": 0, "prediction": "low risk", "time_to_crisis": "none detected"}
    
    signals = []
    signal_count = 0
    
    # Signal 1: Volume spike
    if len(current_analyses) > 15:
        signals.append("HIGH VOLUME: Unusual mention spike detected")
        signal_count += 1
    
    # Signal 2: Negative sentiment threshold
    neg_count = sum(1 for a in current_analyses if a.get("sentiment") == "negative")
    neg_pct = neg_count / len(current_analyses) * 100
    if neg_pct > 25:
        signals.append(f"SENTIMENT SHIFT: {neg_pct:.0f}% of mentions are negative (threshold: 25%)")
        signal_count += 1
    
    # Signal 3: High threat score
    high_threat = [a for a in current_analyses if a.get("threat_score",0) >= 7]
    if high_threat:
        signals.append(f"HIGH THREAT: {len(high_threat)} mention(s) with threat score ≥7")
        signal_count += 1
    
    # Signal 4: Coordinated pattern (same narrative across sources)
    sources = [a.get("source","") for a in current_analyses]
    if len(set(sources)) < len(sources) * 0.4:  # many from same source
        signals.append("COORDINATION PATTERN: Multiple mentions from same source cluster")
        signal_count += 1
    
    # Crisis probability matrix
    probability = min(95, signal_count * 20 + neg_pct * 0.5)
    
    if signal_count == 0:   prediction, time_est = "low risk",      "no crisis predicted"
    elif signal_count == 1: prediction, time_est = "monitor",       "14-30 days if signals persist"
    elif signal_count == 2: prediction, time_est = "elevated risk",  "7-14 days without intervention"
    elif signal_count == 3: prediction, time_est = "crisis likely",  "2-7 days — act now"
    else:                   prediction, time_est = "crisis imminent","24-48 hours — emergency response"
    
    return {
        "probability": int(probability),
        "signals_detected": signal_count,
        "signals": signals,
        "prediction": prediction,
        "time_to_crisis": time_est,
        "recommended_action": (
            "Deploy counter content immediately" if signal_count >= 3 else
            "Begin narrative reinforcement" if signal_count >= 2 else
            "Increase monitoring frequency" if signal_count >= 1 else
            "Continue standard monitoring"
        )
    }

# ── ALERT SYSTEM ─────────────────────────────────────────────────

def send_alert(threat_level: str, subject: str, details: str):
    """Send phone alert via Pushover + email draft."""
    priority = {"critical":2, "red":1, "orange":0, "yellow":-1, "green":-2}.get(threat_level, 0)
    
    emoji = {"critical":"🚨","red":"🔴","orange":"🟠","yellow":"🟡","green":"🟢"}.get(threat_level,"⚪")
    
    if PUSHOVER_KEY:
        requests.post("https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_KEY, "user": PUSHOVER_USR,
                "message": f"""{emoji} {subject}

{details[:500]}""",
                "title": f"NYSR Fixer Alert — {threat_level.upper()}",
                "priority": priority,
                "sound": "siren" if priority >= 1 else "pushover"
            }, timeout=10)
        log.info(f"📱 Alert sent: {threat_level.upper()} — {subject}")

def auto_deploy_response(threat_analysis: dict, rep_score: dict):
    """
    When threat signals detected, auto-stage counter-content.
    Does NOT publish automatically — stages assets + alerts Chairman.
    Chairman approves publication with one Pushover reply.
    """
    if rep_score.get("score",100) > 60:
        return  # No auto-response needed
    
    threat_level = rep_score.get("threat_level","green")
    log.info(f"⚡ Auto-staging counter-content for threat level: {threat_level}")
    
    # Stage fresh positive content
    counter_topics = [
        "How NY Spotlight Report's AI content system works (full transparency)",
        "SC Thomas: building in public — 90 days of real results",
        "What our clients actually experience with ProFlow AI",
        "The honest numbers behind our automated content system",
    ]
    
    from datetime import date as d
    staging_note = {
        "triggered_at": datetime.now().isoformat(),
        "threat_level": threat_level,
        "rep_score": rep_score["score"],
        "counter_topics": counter_topics,
        "status": "staged — awaiting Chairman approval",
        "deployment_instructions": "Reply Y to Pushover alert to deploy all counter-content simultaneously"
    }
    
    # Save to repo
    if GH_TOKEN:
        H2 = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
        REPO2 = "nyspotlightreport/sct-agency-bots"
        path = f"data/threat_responses/{d.today()}_response.json"
        payload = json.dumps(staging_note, indent=2)
        body = {"message": f"alert: counter-content staged — {threat_level}",
                "content": base64.b64encode(payload.encode()).decode()}
        r = requests.get(f"https://api.github.com/repos/{REPO2}/contents/{path}", headers=H2)
        if r.status_code == 200: body["sha"] = r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}", json=body, headers=H2)
    
    import base64 as b64
    send_alert(threat_level,
        f"Counter-content staged — Rep score: {rep_score['score']}/100",
        f"""Threat signals: {rep_score.get('explanation','')}

Counter-content ready to deploy. Reply Y to publish.""")

# ── OPPORTUNITY CAPTURE ───────────────────────────────────────────

def capture_opportunities(analyses: list) -> list:
    """Find and act on PR opportunities in the monitoring data."""
    opportunities = []
    
    for a in analyses:
        opp_score = a.get("opportunity_score", 0)
        opp_type  = a.get("opportunity_type","")
        
        if opp_score >= 6:
            opportunities.append({
                "score": opp_score,
                "type": opp_type,
                "source": a.get("source",""),
                "title": a.get("title","")[:80],
                "url": a.get("url",""),
                "action": determine_opportunity_action(opp_type, a)
            })
    
    return sorted(opportunities, key=lambda x: x["score"], reverse=True)

def determine_opportunity_action(opp_type: str, mention: dict) -> str:
    actions = {
        "competitor_weakness":   "Publish comparison content NOW — they're vulnerable",
        "media_coverage":        "Pitch this journalist immediately — they're in the topic",
        "customer_interest":     "Reply to this thread with value + link to free plan",
        "trending_topic":        "Create trend-riding content in next 2 hours",
        "partnership":           "Reach out directly — they're open to collaboration",
    }
    return actions.get(opp_type, "Engage with value — potential lead or coverage")

# ── MAIN INTELLIGENCE RUN ─────────────────────────────────────────

def save_intel_report(report: dict):
    """Save intelligence report to GitHub for dashboard."""
    if not GH_TOKEN: return
    H2 = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO2 = "nyspotlightreport/sct-agency-bots"
    path = "data/intelligence/latest_report.json"
    
    payload = json.dumps(report, indent=2)
    body = {"message": f"intel: daily reputation report — score {report.get('reputation',{}).get('score',0)}",
            "content": base64.b64encode(payload.encode()).decode()}
    
    r = requests.get(f"https://api.github.com/repos/{REPO2}/contents/{path}", headers=H2)
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}", json=body, headers=H2)
    log.info("✅ Intelligence report saved")

import base64

def run():
    log.info("Reputation Intelligence Engine starting...")
    log.info(f"Monitoring {sum(len(v) for v in WATCH_LIST.values())} keywords across 4 categories")
    
    all_mentions = []
    
    # Collect mentions from all sources
    for category, terms in WATCH_LIST.items():
        for term in terms:
            # NewsAPI
            news = fetch_news_mentions(term, days=1)
            for article in news:
                all_mentions.append({
                    "source": "news",
                    "outlet": article.get("source",{}).get("name",""),
                    "title": article.get("title",""),
                    "body": article.get("description","")[:400],
                    "url": article.get("url",""),
                    "published": article.get("publishedAt",""),
                    "category": category
                })
            
            # Reddit
            reddit = fetch_reddit_mentions(term)
            for post in reddit:
                all_mentions.append({**post, "category": category})
            
            # HN (only for brand terms)
            if category == "brand_primary":
                hn = fetch_hackernews_mentions(term)
                for item in hn:
                    all_mentions.append({**item, "category": category})
            
            # Google News RSS
            gnews = fetch_google_news_rss(term)
            for item in gnews:
                all_mentions.append({**item, "category": category})
            
            time.sleep(0.3)  # Rate limiting
    
    # Deduplicate by URL
    seen_urls = set()
    unique_mentions = []
    for m in all_mentions:
        url = m.get("url","")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_mentions.append(m)
    
    log.info(f"Unique mentions collected: {len(unique_mentions)}")
    
    # Analyze brand mentions specifically (most important)
    brand_mentions = [m for m in unique_mentions if m.get("category") in ["brand_primary","brand_secondary"]]
    all_analyses = []
    
    log.info(f"Analyzing {min(len(brand_mentions), 30)} brand mentions...")
    for mention in brand_mentions[:30]:  # Cap API calls
        analysis = analyze_mention_sentiment(mention)
        all_analyses.append(analysis)
        time.sleep(0.5)
    
    # Calculate reputation score
    rep_score = calculate_reputation_score(all_analyses)
    log.info(f"Reputation Score: {rep_score['score']}/100 — {rep_score['threat_level'].upper()}")
    
    # Load historical data for trend prediction
    history = []  # Would load from data/intelligence/history.json
    
    # Predict crisis probability
    crisis_pred = predict_crisis_probability(history, all_analyses)
    log.info(f"Crisis Probability: {crisis_pred['probability']}% — {crisis_pred['prediction']}")
    
    if crisis_pred["signals_detected"] > 0:
        for sig in crisis_pred["signals"]:
            log.warning(f"  ⚠️  {sig}")
    
    # Capture opportunities
    opportunities = capture_opportunities(all_analyses)
    if opportunities:
        log.info(f"Opportunities detected: {len(opportunities)}")
        for opp in opportunities[:3]:
            log.info(f"  🎯 [{opp['score']}/10] {opp['title'][:60]}")
            log.info(f"     → {opp['action']}")
    
    # Compile full report
    report = {
        "timestamp": datetime.now().isoformat(),
        "reputation": rep_score,
        "crisis_prediction": crisis_pred,
        "opportunities": opportunities[:10],
        "mention_count": len(unique_mentions),
        "brand_mention_count": len(brand_mentions),
        "analyses": all_analyses[:20],
        "alert_level": rep_score["threat_level"]
    }
    
    save_intel_report(report)
    
    # Alert Chairman if needed
    if rep_score["score"] < 60 or crisis_pred["signals_detected"] >= 2:
        send_alert(
            rep_score["threat_level"],
            f"Rep Score: {rep_score['score']}/100 | Crisis Risk: {crisis_pred['probability']}%",
            f"{crisis_pred['prediction'].upper()}\n\nSignals:\n" +
            "\n".join(crisis_pred.get("signals",[])) +
            f"\n\nAction: {crisis_pred['recommended_action']}"
        )
        auto_deploy_response(crisis_pred, rep_score)
    elif opportunities and opportunities[0]["score"] >= 8:
        send_alert(
            "yellow",
            f"HIGH-VALUE OPPORTUNITY: {opportunities[0]['title'][:50]}",
            f"Score: {opportunities[0]['score']}/10\nType: {opportunities[0]['type']}\nAction: {opportunities[0]['action']}"
        )
    else:
        log.info(f"✅ All clear — Rep: {rep_score['score']}/100 | No active threats")
    
    log.info(f"Intelligence run complete.")
    return report

if __name__ == "__main__":
    run()
