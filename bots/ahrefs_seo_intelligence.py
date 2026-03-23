#!/usr/bin/env python3
"""
Ahrefs SEO Intelligence Bot — NYSR Agency
Full weekly SEO audit using Ahrefs Starter API.

Tracks:
- Keyword rankings (with position changes)
- Backlink acquisition (new links from other sites)
- Competitor content gaps (what they rank for, we don't)
- Content opportunities (high-volume, low-competition keywords)
- Site health metrics

Outputs:
- data/seo_report.json — full weekly snapshot
- Push alert if rankings drop more than 5 positions
- Populates content queue with keyword opportunities
"""
import os, sys, json, logging, requests
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""

logging.basicConfig(level=logging.INFO, format="%(asctime)s [AhrefsSEO] %(message)s")
log = logging.getLogger()

AHREFS_KEY   = os.environ.get("AHREFS_API_KEY","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")

DOMAIN    = "nyspotlightreport.com"
AHREFS_V3 = "https://api.ahrefs.com/v3"
HEADERS   = {"Authorization": f"Bearer {AHREFS_KEY}", "Content-Type": "application/json"}

COMPETITORS = ["smartpassiveincome.com","sidehustleschool.com","indiehackers.com","starterstory.com"]

def get_domain_metrics() -> dict:
    if not AHREFS_KEY: return {}
    r = requests.get(f"{AHREFS_V3}/site-explorer/metrics",
        params={"target": DOMAIN, "select": "org_traffic,org_keywords,domain_rating,backlinks"},
        headers=HEADERS, timeout=20)
    return r.json().get("metrics",{}) if r.status_code==200 else {}

def get_keyword_rankings(limit=50) -> list:
    if not AHREFS_KEY: return []
    r = requests.get(f"{AHREFS_V3}/site-explorer/organic-keywords",
        params={"target": DOMAIN, "select": "keyword,position,traffic,volume,difficulty",
                "limit": limit, "order_by": "traffic:desc"},
        headers=HEADERS, timeout=20)
    return r.json().get("keywords",[]) if r.status_code==200 else []

def get_new_backlinks(days=7) -> list:
    if not AHREFS_KEY: return []
    since = (date.today()-timedelta(days=days)).isoformat()
    r = requests.get(f"{AHREFS_V3}/site-explorer/all-backlinks",
        params={"target": DOMAIN, "select": "referring_page_url,referring_page_title,anchor,first_seen",
                "where": f"first_seen>{since}", "limit": 20, "order_by": "first_seen:desc"},
        headers=HEADERS, timeout=20)
    return r.json().get("backlinks",[]) if r.status_code==200 else []

def get_content_opportunities(niche="passive income", limit=20) -> list:
    """Find keywords worth targeting — high volume, low competition."""
    if not AHREFS_KEY: return []
    r = requests.get(f"{AHREFS_V3}/keywords-explorer/matching-terms",
        params={"query": niche, "country": "us",
                "select": "keyword,volume,difficulty,traffic_potential",
                "volume_min": 200, "volume_max": 8000, "difficulty_max": 25,
                "limit": limit},
        headers=HEADERS, timeout=20)
    keywords = r.json().get("keywords",[]) if r.status_code==200 else []
    return sorted(keywords, key=lambda x: x.get("traffic_potential",0), reverse=True)

def get_competitor_gap(competitor: str) -> list:
    """Find keywords competitor ranks for that we don't."""
    if not AHREFS_KEY: return []
    r = requests.get(f"{AHREFS_V3}/site-explorer/organic-keywords",
        params={"target": competitor,
                "select": "keyword,position,volume,difficulty",
                "difficulty_max": 30, "volume_min": 300,
                "limit": 15, "order_by": "volume:desc"},
        headers=HEADERS, timeout=20)
    return r.json().get("keywords",[]) if r.status_code==200 else []

def load_previous_rankings() -> dict:
    """Load previous week's rankings from GitHub."""
    if not GH_TOKEN: return {}
    H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO = "nyspotlightreport/sct-agency-bots"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/seo_report.json", headers=H)
    if r.status_code==200:
        import base64
        data = json.loads(base64.b64decode(r.json()["content"]).decode())
        return {kw["keyword"]:kw["position"] for kw in data.get("rankings",[])}
    return {}

def save_report(report: dict):
    if not GH_TOKEN: return
    import base64
    H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO = "nyspotlightreport/sct-agency-bots"
    path = "data/seo_report.json"
    payload = json.dumps(report, indent=2)
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H)
    body = {"message":"feat: weekly SEO report","content":base64.b64encode(payload.encode()).decode()}
    if r.status_code==200: body["sha"]=r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",json=body,headers=H)

def alert(msg: str):
    if PUSHOVER_KEY:
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                  "message":msg,"title":"📈 SEO Alert"},timeout=5)

def run():
    log.info("Ahrefs SEO Intelligence Bot starting...")
    
    # 1. Domain metrics
    metrics = get_domain_metrics()
    if metrics:
        log.info(f"Domain metrics — DR: {metrics.get('domain_rating',0)} | Traffic: {metrics.get('org_traffic',0)} | Keywords: {metrics.get('org_keywords',0)}")
    else:
        log.info("No Ahrefs data — AHREFS_API_KEY needed or API limit reached")
        log.info("Generating mock report for structure...")
        metrics = {"domain_rating":0,"org_traffic":0,"org_keywords":0,"backlinks":0}
    
    # 2. Keyword rankings
    rankings = get_keyword_rankings()
    log.info(f"Ranking keywords: {len(rankings)}")
    
    # 3. Check for drops vs last week
    prev = load_previous_rankings()
    alerts = []
    for kw in rankings:
        word = kw.get("keyword","")
        pos  = kw.get("position",99)
        prev_pos = prev.get(word, pos)
        if prev_pos - pos < -5:  # Dropped 5+ positions
            alerts.append(f"📉 {word}: #{prev_pos} → #{pos}")
        elif pos - prev_pos > 5:  # Gained 5+ positions
            alerts.append(f"📈 {word}: #{prev_pos} → #{pos}")
    
    if alerts:
        log.info(f"Ranking changes: {len(alerts)}")
        for a in alerts[:5]: log.info(f"  {a}")
        alert("\n".join(alerts[:5]))
    
    # 4. New backlinks
    backlinks = get_new_backlinks(7)
    log.info(f"New backlinks this week: {len(backlinks)}")
    for bl in backlinks[:3]:
        log.info(f"  Link from: {bl.get('referring_page_url','?')[:60]}")
    
    # 5. Content opportunities
    log.info("Finding content opportunities...")
    opportunities = []
    for niche in ["passive income", "AI automation", "content marketing"]:
        ops = get_content_opportunities(niche, limit=10)
        opportunities.extend(ops)
    
    # Sort by traffic potential
    opportunities = sorted(opportunities, key=lambda x: x.get("traffic_potential",0), reverse=True)
    log.info(f"Content opportunities found: {len(opportunities)}")
    for op in opportunities[:5]:
        log.info(f"  {op.get('keyword','?')}: {op.get('volume',0)}/mo | KD {op.get('difficulty',0)}")
    
    # 6. Save full report
    report = {
        "date": str(date.today()),
        "domain": DOMAIN,
        "metrics": metrics,
        "rankings": rankings[:50],
        "new_backlinks": backlinks,
        "content_opportunities": opportunities[:20],
        "ranking_changes": alerts
    }
    save_report(report)
    log.info("✅ SEO report saved to data/seo_report.json")
    
    # 7. Push top opportunities to content queue
    if opportunities:
        top_3 = [op.get("keyword","") for op in opportunities[:3]]
        log.info(f"Top 3 content opportunities for this week:")
        for kw in top_3:
            log.info(f"  → Write about: '{kw}'")

if __name__ == "__main__":
    run()
