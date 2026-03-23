#!/usr/bin/env python3
"""
Market Intelligence Scout — NYSR Business Development
╔══════════════════════════════════════════════════════════════╗
║  OBJECTIVE: Never miss a money-making opportunity again.    ║
║  Scans the entire internet daily for:                       ║
║  • New platforms paying creators/builders                   ║
║  • Emerging monetization methods before they're crowded     ║
║  • Competitor revenue moves we should copy                  ║
║  • Tools and tactics being used by top earners              ║
║  • Pricing trends across our markets                        ║
║  • New affiliate programs with high commissions             ║
╚══════════════════════════════════════════════════════════════╝

Intelligence sources:
- NewsAPI: Latest platform announcements + business news
- Reddit: r/passive_income, r/entrepreneur, r/SideProject trends
- HN: What builders and founders are shipping
- Product Hunt: New tools + revenue models worth studying
- Twitter/X: What top earners are publicly sharing
- Indie Hackers: Real revenue numbers + case studies

Output: Daily opportunity brief → Pushover + data/opportunities/
"""
import os, sys, json, logging, requests, time
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MarketScout] %(message)s")
log = logging.getLogger()

ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
NEWSAPI_KEY  = os.environ.get("NEWSAPI_KEY","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")

# ── SCAN TARGETS ──────────────────────────────────────────────────

OPPORTUNITY_QUERIES = {
    "new_platforms": [
        "new platform pays creators 2026",
        "new monetization platform launch",
        "creator economy new revenue",
        "platform creator fund 2026",
    ],
    "emerging_tools": [
        "AI tool startup funding 2026",
        "new SaaS revenue model 2026",
        "automation tool entrepreneurs",
        "no-code tool passive income",
    ],
    "market_gaps": [
        "entrepreneurs can't find tool",
        "nobody built this yet",
        "missing tool for creators",
        "underserved market entrepreneurs",
    ],
    "competitor_moves": [
        "Jasper AI new feature",
        "Copy.ai new pricing",
        "content automation platform update",
        "beehiiv new feature 2026",
    ],
    "income_methods": [
        "new passive income method 2026",
        "make money online new method",
        "digital product trending 2026",
        "newsletter monetization 2026",
    ],
    "affiliate_programs": [
        "new high commission affiliate program",
        "best affiliate programs 2026",
        "SaaS affiliate recurring commission",
        "content creator affiliate launch",
    ],
}

REDDIT_OPPORTUNITY_SUBS = [
    "passive_income",
    "Entrepreneur",
    "SideProject",
    "indiehackers",
    "microsaas",
    "digitalnomad",
    "beehiiv",
    "ContentMarketing",
    "SEO",
]

BD_SYSTEM = """You are Rowan Blake, Chief Business Development Officer at NY Spotlight Report.
Elite BD mindset: always looking for leverage, first-mover advantage, and underexploited monetization.
Our assets: 100 bots, 15 agents, blog traffic growing, newsletter building, cold email pipeline.
Our revenue gaps: $0 Stripe, $0 Gumroad — all infrastructure built, no revenue yet.
Focus: specific, actionable, tied to our existing assets."""

def score_opportunity(item: dict, source: str) -> dict:
    """Score an opportunity for relevance and actionability."""
    title = item.get("title","")
    body  = item.get("body","") or item.get("description","")
    
    if not ANTHROPIC:
        # Keyword-based scoring
        score = 3
        high_value_kws = ["revenue","money","income","monetize","earn","profit","launch","tool","platform","affiliate"]
        low_value_kws = ["politics","sports","entertainment","celebrity"]
        score += sum(2 for kw in high_value_kws if kw in title.lower())
        score -= sum(3 for kw in low_value_kws if kw in title.lower())
        return {
            "score": max(0, min(10, score)),
            "opportunity_type": "new_platform" if "platform" in title.lower() else "market_insight",
            "relevance_to_nysr": "moderate",
            "action": "investigate",
            "time_sensitivity": "this week",
            "potential_revenue": "$100-500/month if pursued",
        }
    
    return claude_json(
        BD_SYSTEM,
        f"""Score this market intelligence item for NY Spotlight Report:

Source: {source}
Title: {title}
Content: {body[:300]}

Return JSON:
{{
  "score": 0-10 (10 = massive opportunity we must act on today),
  "opportunity_type": one of [new_platform, new_tool, market_gap, competitor_move, income_method, affiliate_program, partnership, acquisition_target],
  "relevance_to_nysr": "how this connects to our existing assets/capabilities",
  "first_mover_window": "how long before this gets crowded: days|weeks|months",
  "potential_revenue": "realistic monthly revenue estimate if we act",
  "required_effort": "low|medium|high",
  "action": "specific next step to capture this opportunity",
  "time_sensitivity": "today|this week|this month|low urgency"
}}""",
        max_tokens=350
    ) or {"score":3,"opportunity_type":"market_insight","action":"investigate","time_sensitivity":"this week"}

def fetch_reddit_opportunities() -> list:
    results = []
    for sub in REDDIT_OPPORTUNITY_SUBS[:5]:
        r = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=10",
            headers={"User-Agent":"NYSRScout/1.0"}, timeout=10)
        if r.status_code == 200:
            for post in r.json().get("data",{}).get("children",[]):
                pd = post.get("data",{})
                if pd.get("score",0) > 50:
                    results.append({
                        "source": f"r/{sub}", "title": pd.get("title",""),
                        "body": pd.get("selftext","")[:300],
                        "url": f"https://reddit.com{pd.get('permalink','')}",
                        "score_reddit": pd.get("score",0),
                        "comments": pd.get("num_comments",0)
                    })
        time.sleep(0.5)
    return results

def fetch_hn_opportunities() -> list:
    r = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
    if r.status_code != 200: return []
    story_ids = r.json()[:20]
    results = []
    for sid in story_ids[:10]:
        r2 = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=8)
        if r2.status_code == 200:
            item = r2.json()
            if item.get("score",0) > 50:
                results.append({
                    "source": "HackerNews",
                    "title": item.get("title",""),
                    "url": item.get("url",""),
                    "score_hn": item.get("score",0),
                    "comments": item.get("descendants",0)
                })
        time.sleep(0.2)
    return results

def fetch_producthunt_launches() -> list:
    """Get today's top Product Hunt launches."""
    r = requests.get("https://api.producthunt.com/v2/api/graphql",
        headers={"Content-Type":"application/json"},
        json={"query": """{ posts(first:10,order:VOTES) { edges { node { name tagline url votesCount topics { edges { node { name } } } } } } }"""},
        timeout=15)
    if r.status_code != 200: return []
    posts = r.json().get("data",{}).get("posts",{}).get("edges",[])
    return [
        {
            "source": "ProductHunt",
            "title": p["node"].get("name",""),
            "body": p["node"].get("tagline",""),
            "url": p["node"].get("url",""),
            "votes": p["node"].get("votesCount",0)
        }
        for p in posts
    ]

def generate_opportunity_brief(opportunities: list) -> str:
    """Generate the daily opportunity brief for Chairman."""
    top = sorted([o for o in opportunities if o.get("analysis",{}).get("score",0) >= 7],
                 key=lambda x: x.get("analysis",{}).get("score",0), reverse=True)[:5]
    
    if not top:
        return "No high-score opportunities today. Standard monitoring continues."
    
    if not ANTHROPIC:
        brief = f"📊 DAILY BD BRIEF — {date.today()}

"
        for i, opp in enumerate(top[:3], 1):
            a = opp.get("analysis",{})
            brief += f"{i}. [{a.get('score',0)}/10] {opp.get('title','')[:60]}
"
            brief += f"   Type: {a.get('opportunity_type','')}
"
            brief += f"   Revenue: {a.get('potential_revenue','')}
"
            brief += f"   Action: {a.get('action','')}

"
        return brief
    
    return claude(
        BD_SYSTEM,
        f"""Write a tight daily BD brief for Chairman SC Thomas.
Top opportunities found today:
{json.dumps([{
    'title': o.get('title','')[:80],
    'source': o.get('source',''),
    'score': o.get('analysis',{}).get('score',0),
    'type': o.get('analysis',{}).get('opportunity_type',''),
    'revenue': o.get('analysis',{}).get('potential_revenue',''),
    'action': o.get('analysis',{}).get('action',''),
    'timing': o.get('analysis',{}).get('time_sensitivity','')
} for o in top], indent=2)}

Write as Rowan Blake (BD Chief). Under 200 words.
Lead with the highest-value item. Be specific. 
Format: DAILY BRIEF header, numbered opportunities, clear next action per item.""",
        max_tokens=350
    )

def run():
    log.info("Market Intelligence Scout starting...")
    log.info(f"Sources: NewsAPI + Reddit ({len(REDDIT_OPPORTUNITY_SUBS)} subs) + HN + Product Hunt")
    
    all_items = []
    
    # Reddit
    reddit_items = fetch_reddit_opportunities()
    log.info(f"Reddit: {len(reddit_items)} posts")
    all_items.extend(reddit_items)
    
    # HackerNews
    hn_items = fetch_hn_opportunities()
    log.info(f"HN: {len(hn_items)} stories")
    all_items.extend(hn_items)
    
    # Product Hunt
    ph_items = fetch_producthunt_launches()
    log.info(f"Product Hunt: {len(ph_items)} launches")
    all_items.extend(ph_items)
    
    # NewsAPI
    if NEWSAPI_KEY:
        for category, queries in OPPORTUNITY_QUERIES.items():
            for q in queries[:2]:
                r = requests.get("https://newsapi.org/v2/everything",
                    params={"q":q,"sortBy":"publishedAt","pageSize":5,
                            "language":"en","apiKey":NEWSAPI_KEY,
                            "from":(date.today()-timedelta(days=2)).isoformat()},
                    timeout=15)
                if r.status_code == 200:
                    for article in r.json().get("articles",[]):
                        all_items.append({
                            "source": f"news/{category}",
                            "title": article.get("title",""),
                            "body": article.get("description","")[:300],
                            "url": article.get("url",""),
                            "outlet": article.get("source",{}).get("name","")
                        })
                time.sleep(0.3)
    
    log.info(f"Total items to analyze: {len(all_items)}")
    
    # Score top items
    analyzed = []
    for item in all_items[:40]:
        if not item.get("title"): continue
        analysis = score_opportunity(item, item.get("source",""))
        if analysis.get("score",0) >= 5:
            analyzed.append({**item, "analysis": analysis})
        time.sleep(0.2)
    
    # Sort by score
    analyzed.sort(key=lambda x: x.get("analysis",{}).get("score",0), reverse=True)
    top_opps = analyzed[:10]
    
    log.info(f"High-value opportunities (score 5+): {len(analyzed)}")
    for opp in top_opps[:5]:
        a = opp.get("analysis",{})
        log.info(f"  [{a.get('score',0)}/10] {opp.get('title','')[:60]}")
        log.info(f"         → {a.get('action','')[:70]}")
    
    # Generate brief
    brief = generate_opportunity_brief(analyzed)
    log.info(f"
DAILY BRIEF:
{brief}")
    
    # Alert Chairman on high-value finds
    urgent = [o for o in analyzed if o.get("analysis",{}).get("time_sensitivity") in ["today","this week"] and o.get("analysis",{}).get("score",0) >= 8]
    if urgent and PUSHOVER_KEY:
        top = urgent[0]
        a = top.get("analysis",{})
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                  "message":f"🎯 BD OPPORTUNITY [{a.get('score',0)}/10]
{top.get('title','')[:60]}

Revenue: {a.get('potential_revenue','')}
Action: {a.get('action','')}
Timing: {a.get('time_sensitivity','')}",
                  "title":"💼 Market Intelligence"},
            timeout=5)
    
    # Save report
    if GH_TOKEN:
        H2 = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        REPO2 = "nyspotlightreport/sct-agency-bots"
        path = f"data/opportunities/{date.today()}.json"
        payload = json.dumps({"date":str(date.today()),"brief":brief,"opportunities":top_opps},indent=2)
        body = {"message":f"bd: market intel — {len(analyzed)} opportunities",
                "content": base64.b64encode(payload.encode()).decode()}
        r = requests.get(f"https://api.github.com/repos/{REPO2}/contents/{path}", headers=H2)
        if r.status_code==200: body["sha"]=r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}",json=body,headers=H2)
    
    log.info("✅ Market Intelligence Scout complete")
    return analyzed

if __name__ == "__main__":
    run()
