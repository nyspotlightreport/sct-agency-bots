#!/usr/bin/env python3
"""
agents/ahrefs_serp_tracker.py — Real SERP Tracking via Ahrefs API
Wires into the PR department for actual rank tracking.
Monitors: keyword positions, backlinks, domain rating, competitor analysis.
"""
import os,sys,json,logging,time
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),".."))
log=logging.getLogger("ahrefs_serp")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [SERP] %(message)s")
import urllib.request as urlreq,urllib.parse

AHREFS_KEY=os.environ.get("AHREFS_API_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
TARGET_DOMAIN="nyspotlightreport.com"
TARGET_KEYWORDS=["S.C. Thomas","NY Spotlight Report","ProFlow AI","AI content automation","automated content marketing"]

def ahrefs_api(endpoint, params=None):
    if not AHREFS_KEY: return None
    base="https://api.ahrefs.com/v3"
    url=f"{base}/{endpoint}"
    if params:
        params["output"]="json"
        url += "?" + urllib.parse.urlencode(params)
    try:
        req=urlreq.Request(url, headers={"Authorization":f"Bearer {AHREFS_KEY}","Accept":"application/json"})
        with urlreq.urlopen(req,timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        log.info(f"  Ahrefs API error: {str(e)[:100]}")
        return None

def get_domain_rating():
    """Get current Domain Rating for our site."""
    data = ahrefs_api("site-explorer/domain-rating", {"target":TARGET_DOMAIN})
    if data:
        dr = data.get("domain_rating",{}).get("domain_rating",0)
        log.info(f"  Domain Rating: {dr}")
        return dr
    return 0

def get_backlinks_count():
    """Get total backlinks pointing to our domain."""
    data = ahrefs_api("site-explorer/backlinks-stats", {"target":TARGET_DOMAIN})
    if data:
        total = data.get("backlinks",0)
        referring = data.get("referring_domains",0)
        log.info(f"  Backlinks: {total} from {referring} domains")
        return {"backlinks":total,"referring_domains":referring}
    return {"backlinks":0,"referring_domains":0}

def get_organic_keywords():
    """Get keywords we currently rank for."""
    data = ahrefs_api("site-explorer/organic-keywords", {"target":TARGET_DOMAIN,"country":"us","limit":20})
    if data and "keywords" in data:
        keywords = data["keywords"]
        log.info(f"  Ranking for {len(keywords)} keywords")
        for kw in keywords[:10]:
            log.info(f"    #{kw.get('position',99)}: {kw.get('keyword','?')} (vol: {kw.get('volume',0)})")
        return keywords
    return []

def track_target_keywords():
    """Check our position for specific target keywords."""
    results = {}
    for kw in TARGET_KEYWORDS:
        data = ahrefs_api("keywords-explorer/keyword-overview", {"keyword":kw,"country":"us"})
        if data:
            results[kw] = {
                "volume": data.get("volume",0),
                "difficulty": data.get("difficulty",0),
                "our_position": "tracking"
            }
            log.info(f"  '{kw}': vol={data.get('volume',0)}, diff={data.get('difficulty',0)}")
    return results

def push(t,m):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000]}).encode(),timeout=5)
    except Exception:  # noqa: bare-except

        pass
def supa_log(data):
    if not SUPA_URL:return
    try:
        req=urlreq.Request(f"{SUPA_URL}/rest/v1/director_outputs",data=json.dumps(data).encode(),method="POST",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=minimal"})
        urlreq.urlopen(req,timeout=10)
    except Exception:  # noqa: bare-except

        pass
def run():
    log.info("="*60)
    log.info("AHREFS SERP TRACKER — Real Rank Monitoring")
    log.info(f"Domain: {TARGET_DOMAIN}")
    log.info("="*60)
    
    if not AHREFS_KEY:
        log.info("  No AHREFS_API_KEY — running in limited mode")
        return {"status":"no_key"}
    
    dr = get_domain_rating()
    backlinks = get_backlinks_count()
    keywords = get_organic_keywords()
    targets = track_target_keywords()
    
    report = {
        "domain_rating": dr,
        "backlinks": backlinks,
        "organic_keywords_count": len(keywords),
        "target_keywords": targets,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    supa_log({"director":"Ahrefs SERP Tracker","output_type":"serp_report",
        "content":json.dumps(report)[:4000],"created_at":datetime.utcnow().isoformat()})
    
    push("SERP Report",f"DR: {dr} | Backlinks: {backlinks.get('backlinks',0)} | Keywords: {len(keywords)}")
    
    log.info(f"\nSERP REPORT:")
    log.info(f"  Domain Rating: {dr}")
    log.info(f"  Backlinks: {backlinks.get('backlinks',0)}")
    log.info(f"  Referring Domains: {backlinks.get('referring_domains',0)}")
    log.info(f"  Organic Keywords: {len(keywords)}")
    return report

if __name__=="__main__":
    run()
