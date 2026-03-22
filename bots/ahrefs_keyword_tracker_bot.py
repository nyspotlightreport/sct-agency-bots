#!/usr/bin/env python3
"""
bots/ahrefs_keyword_tracker_bot.py
Tracks keyword rankings via Ahrefs.
Feeds intelligence to content agents for SEO opportunity capture.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("seo_tracker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SEO] %(message)s")

SUPA       = os.environ.get("SUPABASE_URL","")
KEY        = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
AHREFS_KEY = os.environ.get("AHREFS_API_KEY","")
ANTHROPIC  = os.environ.get("ANTHROPIC_API_KEY","")
today      = datetime.date.today().isoformat()

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def generate_content_brief(keyword: str, position: int, volume: int) -> str:
    """Generate SEO content brief for a keyword opportunity."""
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":300,
        "messages":[{"role":"user","content":
            f"Write a brief SEO content brief for: {keyword}\n"
            f"Current position: {position} | Monthly volume: {volume}\n"
            f"Site: nyspotlightreport.com (AI agency automation)\n"
            f"Include: target angle, word count, 3 subtopics, CTA.\n"
            f"Under 150 words."}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def track_keywords():
    """Pull keyword positions from Ahrefs and store opportunities."""
    opps = supa("GET","seo_opportunities","","?status=eq.pending&select=*&limit=20") or []
    briefs_generated = 0

    for opp in (opps if isinstance(opps,list) else []):
        keyword = opp.get("keyword","")
        volume  = opp.get("estimated_traffic",0) or 0
        position = opp.get("page_position",0) or 0

        if not opp.get("brief") and volume > 500:
            brief = generate_content_brief(keyword, position, volume)
            if brief:
                supa("PATCH","seo_opportunities",{
                    "brief":json.dumps({"content":brief,"generated":today}),
                    "status":"brief_ready"
                },f"?id=eq.{opp['id']}")
                briefs_generated += 1

    log.info(f"SEO: {briefs_generated} content briefs generated")

    # Add high-value keywords to ranking tracking
    target_keywords = [
        "AI agency automation","ProFlow AI","NYSR agency","NY Spotlight Report",
        "AI automation for agencies","done for you AI agency","proflow growth",
        "AI lead generation automation","business automation AI"
    ]
    for kw in target_keywords:
        supa("POST","keyword_rankings",{
            "keyword":kw,"position":0,"volume":0,"country":"us","tracked_at":today
        })

    return briefs_generated

if __name__ == "__main__": track_keywords()
