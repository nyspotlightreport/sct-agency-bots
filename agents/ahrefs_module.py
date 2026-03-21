#!/usr/bin/env python3
"""
Ahrefs Intelligence Module — NYSR Agency
Feeds real keyword data to Content Agent.
With Ahrefs: every post targets verified search volume.
Without: guessing. Difference = 3-5x more organic traffic.
"""
import os, requests, json, logging
log = logging.getLogger("AhrefsModule")

AHREFS_KEY = os.environ.get("AHREFS_API_KEY","")
BASE = "https://api.ahrefs.com/v3"

def get_keyword_data(keyword: str) -> dict:
    """Get real search volume + difficulty for a keyword."""
    if not AHREFS_KEY:
        return {"keyword": keyword, "volume": 0, "difficulty": 0, "available": False}
    r = requests.get(f"{BASE}/keywords-explorer/overview",
        params={"select":"keyword,volume,difficulty,cpc","keywords":keyword,"country":"us"},
        headers={"Authorization": f"Bearer {AHREFS_KEY}"}, timeout=15)
    if r.status_code == 200:
        data = r.json().get("data",[{}])[0]
        return {
            "keyword": keyword,
            "volume": data.get("volume",0),
            "difficulty": data.get("difficulty",0),
            "cpc": data.get("cpc",0),
            "available": True
        }
    return {"keyword": keyword, "volume": 0, "difficulty": 0, "available": False}

def get_content_ideas(niche="passive income", limit=10) -> list:
    """Get keyword ideas ranked by opportunity score."""
    if not AHREFS_KEY:
        log.warning("No AHREFS_API_KEY — using fallback topics")
        return []
    r = requests.get(f"{BASE}/keywords-explorer/matching-terms",
        params={"select":"keyword,volume,difficulty","query":niche,"country":"us",
                "volume_min":200,"volume_max":10000,"difficulty_max":40,"limit":limit},
        headers={"Authorization": f"Bearer {AHREFS_KEY}"}, timeout=20)
    if r.status_code == 200:
        items = r.json().get("data",[])
        # Sort by opportunity: high volume, low difficulty
        return sorted(items, key=lambda x: x.get("volume",0)/max(x.get("difficulty",1),1), reverse=True)
    return []

def get_top_pages_for_competitor(domain="smartpassiveincome.com") -> list:
    """Find what content gets traffic for competitors."""
    if not AHREFS_KEY: return []
    r = requests.get(f"{BASE}/site-explorer/top-pages",
        params={"select":"url,traffic,top_keyword","target":domain,"limit":10},
        headers={"Authorization": f"Bearer {AHREFS_KEY}"}, timeout=20)
    return r.json().get("data",[]) if r.status_code==200 else []

def get_daily_content_brief() -> dict:
    """Full daily content brief powered by Ahrefs data."""
    ideas = get_content_ideas("passive income", 20)
    competitor_gaps = get_top_pages_for_competitor()
    
    if ideas:
        best = ideas[0]
        log.info(f"Top keyword: '{best.get('keyword')}' — {best.get('volume',0)}/mo searches, KD {best.get('difficulty',0)}")
    
    return {
        "keyword_ideas": ideas[:10],
        "competitor_opportunities": competitor_gaps[:5],
        "available": bool(AHREFS_KEY)
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    brief = get_daily_content_brief()
    print(f"Keywords found: {len(brief['keyword_ideas'])}")
    for kw in brief['keyword_ideas'][:5]:
        print(f"  {kw.get('keyword')}: {kw.get('volume',0)}/mo | KD {kw.get('difficulty',0)}")
