#!/usr/bin/env python3
"""
NYSR Affiliate Content Bot
- Generates SEO-optimized articles with embedded affiliate links
- Publishes to nyspotlightreport.com via GitHub → Netlify
- Targets $200+/month from affiliate commissions alone
- Runs daily via GitHub Actions
"""
import os, json, requests, base64, time, logging
from datetime import datetime
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("AffiliateBot")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN      = os.environ.get("GH_TOKEN",os.environ.get("GH_TOKEN",""))
GH_REPO       = "nyspotlightreport/sct-agency-bots"
NTFY_TOPIC    = "nysr-chairman1sct"

# High-commission affiliate programs — all free to join
AFFILIATE_PROGRAMS = {
    "HubSpot":       {"url":"https://hubspot.com/?via=nysr",          "commission":"up to $1,000/sale"},
    "Shopify":       {"url":"https://shopify.com/?ref=nysr",           "commission":"$150/referral"},
    "Kinsta":        {"url":"https://kinsta.com/?ref=nysr",            "commission":"10% recurring"},
    "SEMrush":       {"url":"https://semrush.com/?ref=nysr",           "commission":"$200/sale"},
    "ConvertKit":    {"url":"https://convertkit.com/?ref=nysr",        "commission":"30% recurring"},
    "WP Engine":     {"url":"https://wpengine.com/?ref=nysr",          "commission":"$200+/sale"},
    "Ahrefs":        {"url":"https://ahrefs.com/?ref=nysr",            "commission":"$200/sale"},
    "ElevenLabs":    {"url":"https://elevenlabs.io/?ref=nysr",         "commission":"22% recurring"},
    "Jasper AI":     {"url":"https://jasper.ai/?ref=nysr",             "commission":"25% recurring"},
    "Beehiiv":       {"url":"https://beehiiv.com/?via=nysr",           "commission":"25% recurring"},
    "NordVPN":       {"url":"https://nordvpn.com/?ref=nysr",           "commission":"$40/sale"},
    "Bluehost":      {"url":"https://bluehost.com/?ref=nysr",          "commission":"$65/referral"},
    "Grammarly":     {"url":"https://grammarly.com/?ref=nysr",         "commission":"$20/activation"},
    "Canva":         {"url":"https://canva.com/?ref=nysr",             "commission":"per signup"},
    "Teachable":     {"url":"https://teachable.com/?ref=nysr",         "commission":"30% recurring"},
    "EarnApp":       {"url":"https://earnapp.com/i/NYSR",              "commission":"10% of referral earnings"},
    "Honeygain":     {"url":"https://r.honeygain.me/NYSPOTLIGHT",      "commission":"10% of referral earnings"},
}

# High-traffic article topics that naturally embed affiliate links
ARTICLE_TOPICS = [
    {"title":"Best AI Tools for Entrepreneurs in 2026","affiliates":["Jasper AI","ElevenLabs","Grammarly","HubSpot"],"keyword":"AI tools entrepreneurs"},
    {"title":"How to Start a Newsletter and Make Money in 2026","affiliates":["Beehiiv","ConvertKit","Grammarly"],"keyword":"start newsletter make money"},
    {"title":"Best Web Hosting for Small Businesses 2026","affiliates":["Bluehost","WP Engine","Kinsta"],"keyword":"best web hosting small business"},
    {"title":"How to Build Passive Income Online — 15 Real Methods","affiliates":["EarnApp","Honeygain","Teachable","ConvertKit"],"keyword":"passive income online"},
    {"title":"Best SEO Tools That Actually Work in 2026","affiliates":["Ahrefs","SEMrush","HubSpot"],"keyword":"best SEO tools 2026"},
    {"title":"How to Start an Online Store — Complete Guide","affiliates":["Shopify","HubSpot","Grammarly"],"keyword":"how to start online store"},
    {"title":"Best Email Marketing Tools for Creators 2026","affiliates":["ConvertKit","Beehiiv","HubSpot"],"keyword":"email marketing tools creators"},
    {"title":"How to Use AI to Make Money Online in 2026","affiliates":["Jasper AI","ElevenLabs","Beehiiv","Teachable"],"keyword":"AI make money online"},
    {"title":"CRM Software Comparison — Which is Worth It","affiliates":["HubSpot","SEMrush"],"keyword":"best CRM software"},
    {"title":"VPN Comparison Guide — Privacy & Speed in 2026","affiliates":["NordVPN"],"keyword":"best VPN comparison 2026"},
]

def generate_article(topic, client):
    affiliates_str = "\n".join([f"- {name}: {AFFILIATE_PROGRAMS[name]['url']} ({AFFILIATE_PROGRAMS[name]['commission']})"
                                 for name in topic['affiliates'] if name in AFFILIATE_PROGRAMS])
    
    prompt = f"""Write a comprehensive, SEO-optimized article for nyspotlightreport.com.

Title: {topic['title']}
Target keyword: {topic['keyword']}
Affiliate links to naturally embed (use anchor text, not raw URLs):
{affiliates_str}

Requirements:
- 800-1200 words
- Natural, helpful tone — not salesy
- H2 and H3 subheadings  
- Each affiliate link mentioned 1-2 times max, naturally in context
- Include a "Bottom Line" summary section
- Format as clean HTML (article body only, no html/head/body tags)
- Add proper anchor tags: <a href="URL" rel="sponsored nofollow" target="_blank">anchor text</a>
- Do NOT use markdown, only HTML

Return ONLY the HTML article body."""

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role":"user","content":prompt}]
    )
    return resp.content[0].text

def push_article_to_github(slug, title, html_content, keyword):
    """Creates a new HTML page in the site and updates the sitemap"""
    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | NY Spotlight Report</title>
<meta name="description" content="NY Spotlight Report covers {keyword}. Expert analysis and recommendations.">
<meta name="keywords" content="{keyword}, NY Spotlight Report">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://nyspotlightreport.com/{slug}">
<meta property="og:title" content="{title}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://nyspotlightreport.com/{slug}">
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#1a1a1a;line-height:1.6}}
h1{{font-size:2rem;font-weight:800;margin-bottom:0.5rem}}
h2{{font-size:1.4rem;font-weight:700;margin-top:2rem;color:#111}}
h3{{font-size:1.1rem;font-weight:600;color:#333}}
a{{color:#0066cc}}a:hover{{color:#0044aa}}
.back{{font-size:0.9rem;margin-bottom:2rem}}.back a{{color:#666;text-decoration:none}}
.date{{color:#666;font-size:0.9rem;margin-bottom:2rem}}
</style>
</head>
<body>
<div class="back"><a href="/">← NY Spotlight Report</a></div>
<h1>{title}</h1>
<p class="date">Published by NY Spotlight Report | {datetime.now().strftime('%B %d, %Y')}</p>
{html_content}
<hr style="margin-top:3rem">
<p style="font-size:0.85rem;color:#666">NY Spotlight Report may earn commissions from links on this page. This does not affect our editorial independence.</p>
</body>
</html>"""

    # Push to GitHub
    headers = {"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json"}
    path = f"site/{slug}/index.html"
    url  = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    
    # Check if exists
    existing = requests.get(url, headers=headers)
    sha = existing.json().get("sha","") if existing.ok else ""
    
    payload = {
        "message": f"Add affiliate article: {title[:50]}",
        "content": base64.b64encode(page_html.encode()).decode()
    }
    if sha: payload["sha"] = sha
    
    r = requests.put(url, headers=headers, json=payload)
    return r.ok, r.json().get("content",{}).get("name","error")

def run():
    if not ANTHROPIC_KEY:
        log.warning("ANTHROPIC_API_KEY not set")
        return
    
    client = Anthropic(api_key=ANTHROPIC_KEY)
    
    # Pick today's article (rotate through topics)
    day_index = datetime.now().timetuple().tm_yday % len(ARTICLE_TOPICS)
    topic = ARTICLE_TOPICS[day_index]
    slug = topic['keyword'].replace(' ','-').replace(',','').lower()[:50]
    
    log.info(f"Generating: {topic['title']}")
    html = generate_article(topic, client)
    
    ok, result = push_article_to_github(slug, topic['title'], html, topic['keyword'])
    
    if ok:
        url = f"https://nyspotlightreport.com/{slug}"
        log.info(f"✅ Published: {url}")
        # Phone notification
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
            headers={"Title":"📝 New Affiliate Article Live","Tags":"money_with_wings","Priority":"default"},
            data=f"Published: {topic['title'][:60]}\n{url}")
    else:
        log.error(f"Failed: {result}")

if __name__ == "__main__":
    run()
