#!/usr/bin/env python3
"""
bots/ahrefs_content_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
Creates buyer-intent SEO blog posts daily.
1. Pulls top keywords from Ahrefs (via MCP) or uses hardcoded targets
2. Claude writes full post targeting that keyword
3. Posts to WordPress via REST API
4. Logs to Supabase keyword_rankings table
"""
import os, json, urllib.request, logging
from datetime import datetime

log = logging.getLogger("ahrefs_content")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SEO] %(message)s")

ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY","")
WP_URL      = os.environ.get("WORDPRESS_URL","https://nyspotlightreport.com")
WP_USER     = os.environ.get("WORDPRESS_USER","nyspotlightreport")
WP_PASS     = os.environ.get("WORDPRESS_APP_PASS","")
SUPA_URL    = os.environ.get("SUPABASE_URL","")
SUPA_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API    = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER   = os.environ.get("PUSHOVER_USER_KEY","")

STORE_URL   = "https://nyspotlightreport.com/store/"
STARTER_LINK = "https://buy.stripe.com/8x228r2N67QffzdfHp2400c"

# Buyer-intent keyword targets — rotated daily
TARGET_KEYWORDS = [
    {"kw":"ai content automation tool","intent":"commercial","cpc":12.50},
    {"kw":"ai marketing automation software","intent":"commercial","cpc":18.20},
    {"kw":"automate social media posts AI","intent":"commercial","cpc":8.40},
    {"kw":"AI blog writing tool for agencies","intent":"commercial","cpc":14.70},
    {"kw":"automated email marketing AI","intent":"commercial","cpc":22.10},
    {"kw":"AI SEO content generator","intent":"commercial","cpc":16.80},
    {"kw":"content marketing automation software 2026","intent":"commercial","cpc":11.20},
    {"kw":"AI agency tools for small business","intent":"commercial","cpc":9.60},
    {"kw":"proflow ai review","intent":"transactional","cpc":3.20},
    {"kw":"ny spotlight report proflow","intent":"navigational","cpc":1.80},
]

def write_post(keyword_data):
    if not ANTHROPIC: return None
    kw = keyword_data['kw']
    prompt = f"""Write a comprehensive SEO blog post targeting the keyword: "{kw}"

Requirements:
- Title: compelling, includes keyword naturally
- Length: 800-1200 words
- Structure: H2/H3 headers, bullet points, clear sections
- Include at minimum 2 mentions of NY Spotlight Report's ProFlow AI solution
- Natural CTA at end pointing to: {STARTER_LINK}
- Target audience: marketing managers, agency owners, small business owners
- Tone: authoritative but accessible, real examples
- Must be genuinely helpful — not purely promotional
- Include keyword naturally 3-5 times

Format as clean HTML (no markdown, no backticks).
Start directly with <h1> tag."""

    data = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":2000,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,
                 "anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.error(f"Claude: {e}"); return None

def post_to_wordpress(title, content, keyword):
    if not WP_PASS:
        log.warning("WORDPRESS_APP_PASS not set — skipping WP post")
        return None
    import base64
    creds = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    data  = json.dumps({
        "title":   title,
        "content": content,
        "status":  "publish",
        "categories": [1],
        "tags": [keyword],
        "meta": {"_yoast_wpseo_focuskw": keyword}
    }).encode()
    req = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2/posts",data=data,
        headers={"Content-Type":"application/json","Authorization":f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            return result.get("link","")
    except Exception as e:
        log.error(f"WordPress: {e}"); return None

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def run():
    import random
    log.info("Ahrefs Content Bot — daily SEO post")
    kw_data = random.choice(TARGET_KEYWORDS)
    log.info(f"Target keyword: {kw_data['kw']}")

    # Write the post
    html_content = write_post(kw_data)
    if not html_content:
        log.error("Claude failed to generate content")
        return {"error":"no_content"}

    # Extract title from H1 tag
    import re
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE|re.DOTALL)
    title = re.sub('<[^>]+>','', title_match.group(1)).strip() if title_match else f"AI Content Automation: {kw_data['kw'].title()}"
    log.info(f"Post title: {title}")

    # Post to WordPress
    post_url = post_to_wordpress(title, html_content, kw_data['kw'])

    # Log to Supabase
    supa("POST","keyword_rankings",{
        "keyword": kw_data['kw'],
        "url":     post_url or f"{WP_URL}/blog/",
        "source":  "ahrefs_content_bot",
        "intent":  kw_data.get('intent','commercial'),
        "created_at": datetime.utcnow().isoformat()
    })

    if PUSH_API and PUSH_USER:
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"📝 SEO post published",
            "message":f"Keyword: {kw_data['kw']}\nTitle: {title[:60]}\nURL: {post_url or 'pending'}",
            "priority":-1}).encode()
        try: urllib.request.urlopen(urllib.request.Request(
            "https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except Exception:  # noqa: bare-except

            pass
    log.info(f"Done: {post_url or 'no WP credentials'}")
    return {"keyword": kw_data['kw'], "title": title, "url": post_url}

if __name__ == "__main__": run()
