#!/usr/bin/env python3
"""
Affiliate Content Publisher — generates and publishes one SEO article daily
Uses Anthropic API for content generation
Commits to site/ directory via GitHub API
"""
import os, requests, base64, json
from datetime import datetime, date

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN = os.environ.get("GH_TOKEN","") or os.environ.get("GITHUB_TOKEN","")
REPO = "nyspotlightreport/sct-agency-bots"
GH_HDR = {"Authorization": f"Bearer {GH_TOKEN}", "Content-Type": "application/json"}
SITE_URL = "https://nyspotlightreport.com"

TOPICS = [
    ("how-to-make-money-blogging-2026", "How to Make Money Blogging in 2026 — What Actually Works",
     "affiliate marketing blogging passive income",
     ["beehiiv.com/?via=nysr", "ahrefs.com/?ref=nysr", "jasper.ai/?ref=nysr"]),
    ("best-productivity-tools-2026", "Best Productivity Tools for Entrepreneurs 2026",
     "productivity tools entrepreneurs small business",
     ["hubspot.com/?via=nysr", "grammarly.com/?ref=nysr", "jasper.ai/?ref=nysr"]),
    ("social-media-tools-2026", "Best Social Media Management Tools 2026",
     "social media tools scheduling automation",
     ["beehiiv.com/?via=nysr", "semrush.com/?ref=nysr", "hubspot.com/?via=nysr"]),
    ("email-marketing-guide-2026", "Email Marketing Complete Guide 2026 — Build and Monetize a List",
     "email marketing guide build email list 2026",
     ["convertkit.com/?ref=nysr", "beehiiv.com/?via=nysr", "hubspot.com/?via=nysr"]),
    ("best-website-builders-2026", "Best Website Builders for Small Business 2026",
     "best website builder small business 2026",
     ["kinsta.com/?ref=nysr", "bluehost.com/?ref=nysr", "shopify.com/?ref=nysr"]),
]

def generate_article(topic_data):
    slug, title, keyword, affiliates = topic_data
    aff_list = ", ".join(f"https://{a}" for a in affiliates)
    
    if not ANTHROPIC_KEY:
        # Fallback: template article without API
        return slug, title, keyword, f"""
<p>For entrepreneurs and small business owners looking to grow in 2026, the right tools make all the difference. This guide covers the most important options for {keyword}.</p>
<h2>Why This Matters in 2026</h2>
<p>The competitive landscape for {keyword} has evolved dramatically. Businesses that leverage the right platforms and tools are consistently outperforming those that don't.</p>
<h2>Top Recommended Tools</h2>
<p>Based on extensive research and real-world testing, these are the tools delivering the most value for businesses focused on {keyword} in 2026. Each has been evaluated for ROI, ease of use, and support quality.</p>
<p>For a complete breakdown and comparison, see our <a href="{SITE_URL}/best-ai-tools-entrepreneurs-2026/">full tools roundup for 2026</a>.</p>
<h2>Getting Started</h2>
<p>The most important step is choosing tools that match your current stage and budget. Most of the top platforms offer free tiers that let you validate fit before committing to paid plans. Start there.</p>
<p><em>S.C. Thomas is the Editor-in-Chief of NY Spotlight Report, covering New York business and technology.</em></p>
"""
    
    # Use Anthropic API
    resp = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1200,
              "messages": [{"role": "user", "content": f"""Write a 600-word expert article for NY Spotlight Report about: {title}
Target keyword: {keyword}
Author: S.C. Thomas, Editor-in-Chief

Include 2-3 naturally embedded affiliate links to: {aff_list}
Use rel="sponsored nofollow" on affiliate links.

Format: HTML paragraphs and h2 headers only. No markdown.
Tone: Expert journalist, helpful, data-driven.
End with a byline: S.C. Thomas, NY Spotlight Report."""}]},
        timeout=30)
    
    if resp.ok:
        body = resp.json()["content"][0]["text"]
    else:
        body = f"<p>Expert guide to {title} — full analysis coming soon at NY Spotlight Report.</p>"
    
    return slug, title, keyword, body

def build_page(slug, title, keyword, body):
    url = f"{SITE_URL}/{slug}/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} | NY Spotlight Report</title>
<meta name="description" content="{title} — expert analysis from NY Spotlight Report.">
<meta name="keywords" content="{keyword}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<meta name="author" content="S.C. Thomas">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"NewsArticle","headline":"{title}","datePublished":"{date.today().isoformat()}","dateModified":"{date.today().isoformat()}","author":{{"@type":"Person","name":"S.C. Thomas"}},"publisher":{{"@type":"Organization","name":"NY Spotlight Report","url":"https://nyspotlightreport.com"}}}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=EB+Garamond&family=Barlow:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div class="top-bar"><div class="top-bar-inner"><span class="top-date" id="js-date"></span><span class="top-tag">New York Business &amp; Tech Intelligence</span><div class="top-social"><a href="https://twitter.com/NYSpotlightRpt" target="_blank">Twitter</a><a href="/newsletter/">Subscribe</a></div></div></div>
<header class="nameplate"><div class="nameplate-inner"><a href="/"><h1>NY Spotlight Report</h1></a><p class="tagline">New York Business &bull; Technology &bull; Finance</p></div></header>
<nav class="primary-nav"><div class="nav-inner"><a href="/">Home</a><a href="/business/">Business</a><a href="/technology/">Technology</a><a href="/money/">Money</a><a href="/about/">About</a><a href="/newsletter/" class="nav-cta">Subscribe Free</a></div></nav>
<div style="background:#f9f9f7;border-bottom:1px solid #e5e5e5;padding:8px 0;font-family:Barlow,sans-serif;font-size:12px;color:#6b7280">
  <div class="site-container"><a href="/">Home</a> &rsaquo; {title[:60]}</div>
</div>
<div class="article-wrap">
<div class="art-cat">Analysis</div>
<h1 class="art-hed">{title}</h1>
<div class="art-meta">
  <span>By <strong>S.C. Thomas</strong></span>
  <span>Editor-in-Chief, NY Spotlight Report</span>
  <span>{date.today().strftime("%B %d, %Y")}</span>
  <span>5 min read</span>
</div>
<img src="https://picsum.photos/seed/{slug}/1200/675" alt="{title}" style="width:100%;aspect-ratio:16/9;object-fit:cover;margin-bottom:8px" loading="eager">
<p style="font-family:Barlow,sans-serif;font-size:11px;color:#6b7280;margin-bottom:26px">Photo: NY Spotlight Report</p>
<div class="art-body">{body}</div>
<div class="art-share">
  <span>Share:</span>
  <a href="https://twitter.com/intent/tweet?url={url}&via=NYSpotlightRpt" target="_blank" rel="noopener nofollow" class="shr shr-tw">𝕏 Twitter</a>
  <a href="https://www.facebook.com/sharer/sharer.php?u={url}" target="_blank" rel="noopener nofollow" class="shr shr-fb">Facebook</a>
  <button onclick="navigator.clipboard.writeText('{url}');this.textContent='Copied!';setTimeout(()=>this.textContent='Copy Link',2000)" class="shr shr-cp">Copy Link</button>
</div>
<div class="author-box">
  <img src="https://picsum.photos/seed/sct-headshot/144/144" alt="S.C. Thomas" loading="lazy">
  <div><div class="author-name">S.C. Thomas</div><div class="author-title">Editor-in-Chief &amp; Founder, NY Spotlight Report</div>
  <div class="author-bio">S.C. Thomas covers New York business, technology, and entrepreneurship. Follow: <a href="https://twitter.com/NYSpotlightRpt" target="_blank" rel="noopener" style="color:#c0392b">@NYSpotlightRpt</a></div></div>
</div>
<div class="nl-box">
  <h3>Stay Ahead of New York Business</h3>
  <p>The NY Spotlight Report newsletter — free, every week.</p>
  <div class="nl-form"><input type="email" placeholder="Your email" id="nle"><button onclick="window.open('https://proflowdigital.beehiiv.com/subscribe?email='+document.getElementById('nle').value,'_blank')">Subscribe Free</button></div>
</div>
<div style="margin:36px 0">
  <div style="font-family:Barlow,sans-serif;font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#c0392b;border-bottom:2px solid #c0392b;padding-bottom:7px;margin-bottom:18px">More From NY Spotlight Report</div>
  <ul style="list-style:none;padding:0">
    <li style="padding:10px 0;border-bottom:1px solid #e5e5e5"><a href="/passive-income-guide-2026/" style="font-family:'Playfair Display',serif;font-size:17px;font-weight:700;color:#1a1a1a">The Real Guide to Building Passive Income in 2026</a></li>
    <li style="padding:10px 0;border-bottom:1px solid #e5e5e5"><a href="/nyc-tech-ecosystem-2026/" style="font-family:'Playfair Display',serif;font-size:17px;font-weight:700;color:#1a1a1a">NYC Tech Ecosystem Just Had Its Best Quarter Since 2021</a></li>
    <li style="padding:10px 0;border-bottom:1px solid #e5e5e5"><a href="/newsletter-economy-2026/" style="font-family:'Playfair Display',serif;font-size:17px;font-weight:700;color:#1a1a1a">The Newsletter Economy Is Growing — NY Writers Are Leading It</a></li>
  </ul>
</div>
</div>
<footer class="site-footer"><div class="footer-inner">
<div class="footer-brand">NY Spotlight Report</div>
<div class="footer-bottom"><p>&copy; 2026 NY Spotlight Report. Founded by S.C. Thomas. <a href="/disclosure/" style="color:#666">Affiliate Disclosure</a></p></div>
</div></footer>
<script>var d=new Date();var el=document.getElementById("js-date");if(el)el.textContent=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"][d.getDay()]+", "+["January","February","March","April","May","June","July","August","September","October","November","December"][d.getMonth()]+" "+d.getDate()+", "+d.getFullYear();</script>
</body></html>"""

def push_page(slug, html):
    content = base64.b64encode(html.encode("utf-8")).decode()
    apipath = f"site/{slug}/index.html"
    url = f"https://api.github.com/repos/{REPO}/contents/{apipath}"
    ex = requests.get(url, headers=GH_HDR)
    sha = ex.json().get("sha","") if ex.ok else ""
    pl = {"message": f"Publish article: {slug}", "content": content}
    if sha: pl["sha"] = sha
    r = requests.put(url, headers=GH_HDR, json=pl)
    return r.ok, r.status_code

def run():
    today_num = date.today().timetuple().tm_yday
    topic = TOPICS[today_num % len(TOPICS)]
    slug = topic[0]
    
    print(f"Generating article: {topic[1]}")
    slug, title, keyword, body = generate_article(topic)
    html = build_page(slug, title, keyword, body)
    
    ok, code = push_page(slug, html)
    print(f"Published: {ok} ({code}) — https://nyspotlightreport.com/{slug}/")
    
    if not ok:
        print("Push failed — check GH_TOKEN / GITHUB_TOKEN secret")
        return 1
    return 0

if __name__ == "__main__":
    exit(run())
