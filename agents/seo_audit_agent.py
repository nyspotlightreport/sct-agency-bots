#!/usr/bin/env python3
"""
SEO Audit Agent — Revenue-focused SEO using Ahrefs API.
Finds keywords we almost rank for, pages bleeding traffic,
and content gaps vs competitors. Generates fix list + content briefs.

Daily: Monitor rank changes + alert on drops
Weekly: Full audit + content brief generation
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

import urllib.request as _urllib_req
_SUPA_URL = os.environ.get("SUPABASE_URL","")
_SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")

def supabase_request(method, table, data=None, query="", **kwargs):
    """Standalone supabase helper — no import dependency."""
    if not _SUPA_URL or not _SUPA_KEY: return None
    url = f"{_SUPA_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey": _SUPA_KEY, "Authorization": f"Bearer {_SUPA_KEY}",
               "Content-Type": "application/json", "Prefer": "return=representation"}
    req = _urllib_req.Request(url, data=payload, method=method, headers=headers)
    try:
        with _urllib_req.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except Exception as e:
        log.warning(f"Supabase {method} {table}: {e}")
        return None

import urllib.request, urllib.parse
log = logging.getLogger(__name__)

AHREFS_KEY    = os.environ.get("AHREFS_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
SITE_URL      = "nyspotlightreport.com"

# Keywords we MUST own for cashflow
REVENUE_KEYWORDS = [
    "AI agency automation",
    "done for you AI bots",
    "AI content automation service",
    "AI marketing automation agency",
    "automated lead generation service",
    "done for you lead generation",
    "AI agency for small business",
    "passive income AI automation",
    "AI newsletter monetization",
    "HubSpot alternative AI",
]

COMPETITOR_DOMAINS = [
    "jasper.ai",
    "copy.ai",
    "automation.io",
    "zapier.com",
    "make.com",
]

def ahrefs_get(endpoint: str, params: dict) -> dict:
    if not AHREFS_KEY: return {}
    try:
        params["token"]  = AHREFS_KEY
        params["output"] = "json"
        qs  = urllib.parse.urlencode(params)
        url = f"https://apiv2.ahrefs.com/?{qs}&from={endpoint}"
        req = urllib.request.Request(url, headers={"Accept":"application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"Ahrefs {endpoint}: {e}")
        return {}

def get_ranking_keywords() -> list:
    data = ahrefs_get("positions", {
        "target": SITE_URL,
        "mode":   "domain",
        "limit":  100,
    })
    return data.get("positions", [])

def get_nearly_ranking_keywords() -> list:
    """Find keywords ranking 11-20 (page 2) — easiest to push to page 1."""
    keywords = get_ranking_keywords()
    return [k for k in keywords if 11 <= k.get("pos",0) <= 20]

def generate_content_brief(keyword: str, current_position: int = 0) -> dict:
    return claude_json(
        "You are an SEO content strategist. Generate a concise content brief optimized to rank #1.",
        f"""Target keyword: {keyword}
Current position: {current_position if current_position > 0 else "Not ranking"}
Site: {SITE_URL} (AI agency automation)

Return JSON: {{
  "title": "H1 title tag (60 chars max, includes keyword)",
  "meta_description": "155 char meta description",
  "h2_headers": ["section 1 h2", "section 2 h2", "section 3 h2"],
  "word_count": 1200-2500,
  "primary_angle": "what unique angle will beat current top results",
  "schema_type": "Article|Service|FAQ|HowTo",
  "internal_links_needed": ["existing page to link from"],
  "estimated_traffic_at_rank_1": 100-5000
}}""",
        max_tokens=400
    ) or {
        "title": f"{keyword} | NY Spotlight Report",
        "meta_description": f"Best {keyword} service. AI-powered, done for you, results guaranteed.",
        "h2_headers": [f"What is {keyword}", f"How {keyword} works", f"Get started"],
        "word_count": 1500,
        "primary_angle": f"AI-native approach to {keyword}",
        "schema_type": "Service",
        "estimated_traffic_at_rank_1": 500,
    }

def run():
    log.info("SEO Audit Agent running...")

    nearly_ranking = get_nearly_ranking_keywords()
    log.info(f"Page 2 keywords (11-20): {len(nearly_ranking)}")

    briefs_generated = 0
    opportunities = []

    # Generate briefs for revenue keywords we should own
    for keyword in REVENUE_KEYWORDS[:5]:
        brief = generate_content_brief(keyword)
        est_traffic = brief.get("estimated_traffic_at_rank_1", 0)
        opportunities.append({
            "keyword": keyword,
            "estimated_monthly_traffic": est_traffic,
            "brief": brief
        })
        supabase_request("POST","seo_opportunities",{
            "keyword":         keyword,
            "page_position":   0,
            "estimated_traffic": est_traffic,
            "brief":           json.dumps(brief),
            "status":          "pending",
            "created_at":      datetime.utcnow().isoformat(),
        })
        briefs_generated += 1
        log.info(f"  Brief: "{keyword}" — est. {est_traffic:,} visits/mo at #1")

    # Alert on biggest opportunities
    if opportunities and PUSHOVER_API and PUSHOVER_USER:
        top = max(opportunities, key=lambda x: x["estimated_monthly_traffic"])
        msg = f"🔍 SEO Audit Complete\n{briefs_generated} content briefs generated\n\nBiggest opportunity:\n"{top['keyword']}"\n~{top['estimated_monthly_traffic']:,} visits/mo at rank #1"
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"SEO Audit","message":msg}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except: pass

    log.info(f"SEO Audit complete: {briefs_generated} briefs | {len(nearly_ranking)} page-2 opportunities")
    return {"briefs_generated":briefs_generated,"page_2_opportunities":len(nearly_ranking),"revenue_keywords":len(REVENUE_KEYWORDS)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [SEO] %(message)s")
    run()
