#!/usr/bin/env python3
"""
Netlify Blog Publisher Bot — NYSR Agency
Replaces WordPress — pushes blog posts directly to site/blog/
Each post = SEO-optimized HTML file → Netlify deploys in ~60 seconds
Benefits: faster, OUR domain (not wordpress.com), no platform risk

Post format: site/blog/[slug]/index.html
URL: nyspotlightreport.com/blog/[slug]/
"""
import os, sys, json, logging, requests, base64, re
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [BlogPublisher] %(message)s")
log = logging.getLogger()

GH_TOKEN  = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
REPO      = "nyspotlightreport/sct-agency-bots"
H         = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
AHREFS_KEY= os.environ.get("AHREFS_API_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

POST_TOPICS = [
    ("passive income ideas 2026",      "Passive Income",   "💰"),
    ("AI tools for entrepreneurs",     "AI Tools",         "🤖"),
    ("content automation strategy",    "Content Automation","📝"),
    ("digital products to sell online","Passive Income",   "💎"),
    ("how to start a newsletter",      "Content Automation","📧"),
    ("side hustle ideas 2026",         "Entrepreneurship", "🚀"),
    ("make money blogging 2026",       "Passive Income",   "💵"),
    ("best affiliate programs 2026",   "Affiliate Marketing","🔗"),
    ("youtube shorts monetization",    "Content Automation","🎬"),
    ("chatgpt for business",           "AI Tools",         "🧠"),
]

def slugify(text):
    s = re.sub(r"[^a-z0-9\-]","",re.sub(r"[^a-z0-9]+","-",text.lower())).strip("-")
    s = re.sub(r"-+","-",s)  # collapse multiple hyphens
    return s[:50] if s else "post-" + str(int(__import__("time").time()))

def get_sha(path):
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H, timeout=10)
    return r.json().get("sha") if r.status_code==200 else None

def write_post_html(title, content_md, category, emoji, keyword, date_str):
    """Wrap blog content in full SEO-optimized HTML template."""
    # Convert basic markdown to HTML
    html = content_md
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\n\n", "</p><p>", html)
    html = "<p>" + html + "</p>"
    # Extract first 160 chars for meta description
    desc = re.sub("<[^>]+>","",content_md[:300]).strip()[:160]
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — NY Spotlight Report</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{keyword}, passive income, AI automation, entrepreneurship">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<link rel="canonical" href="https://nyspotlightreport.com/blog/{slugify(title)}/">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--gold:#C9A84C;--dark:#0D1B2A;--mid:#111d2e;--border:#1a2d42;--text:#e8edf2;--muted:#7a8fa0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#060f1a;color:var(--text);line-height:1.7;}}
nav{{background:rgba(6,15,26,.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0 48px;height:68px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}}
.logo{{color:var(--gold);font-size:16px;font-weight:800;text-decoration:none;}}
.nav-cta{{background:var(--gold);color:var(--dark);padding:8px 18px;border-radius:6px;font-size:12px;font-weight:700;text-decoration:none;}}
.wrap{{max-width:740px;margin:0 auto;padding:60px 24px 80px;}}
.post-header{{margin-bottom:40px;padding-bottom:32px;border-bottom:1px solid var(--border);}}
.post-meta{{display:flex;align-items:center;gap:12px;font-size:12px;color:var(--muted);margin-bottom:16px;flex-wrap:wrap;}}
.post-cat{{background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.3);color:var(--gold);padding:3px 10px;border-radius:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;}}
h1{{font-size:clamp(26px,4vw,44px);font-weight:800;letter-spacing:-1.5px;line-height:1.15;margin-bottom:16px;}}
.post-lead{{font-size:18px;color:var(--muted);line-height:1.7;}}
.post-content h2{{font-size:24px;font-weight:700;letter-spacing:-.5px;margin:36px 0 14px;color:var(--text);}}
.post-content h3{{font-size:20px;font-weight:700;margin:28px 0 10px;color:var(--text);}}
.post-content p{{font-size:16px;color:rgba(232,237,242,.85);margin-bottom:16px;}}
.post-content strong{{color:var(--text);font-weight:700;}}
.post-content ul,.post-content ol{{margin:0 0 16px 20px;}}
.post-content li{{font-size:16px;color:rgba(232,237,242,.85);padding:4px 0;}}
.post-cta{{background:var(--mid);border:1px solid rgba(201,168,76,.3);border-radius:14px;padding:32px;text-align:center;margin:48px 0;}}
.post-cta h3{{font-size:20px;font-weight:700;margin-bottom:8px;}}
.post-cta p{{color:var(--muted);font-size:14px;margin-bottom:20px;}}
.cta-btn{{background:var(--gold);color:var(--dark);padding:12px 28px;border-radius:7px;font-size:14px;font-weight:700;text-decoration:none;display:inline-block;}}
@media(max-width:768px){{nav{{padding:0 20px;}}.wrap{{padding:40px 16px;}}}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">NY Spotlight Report</a>
  <a href="/free-plan/" class="nav-cta">Free Content Audit</a>
</nav>
<div class="wrap">
  <article>
    <header class="post-header">
      <div class="post-meta">
        <span class="post-cat">{category}</span>
        <span>Published {date_str}</span>
        <span>·</span>
        <span>NY Spotlight Report</span>
      </div>
      <h1>{title}</h1>
    </header>
    <div class="post-content">
      {html}
    </div>
    <div class="post-cta">
      <h3>Get your free 30-day content plan</h3>
      <p>We'll build a custom AI content strategy for your specific niche. Takes 60 seconds.</p>
      <a href="/free-plan/" class="cta-btn">Get Free Plan →</a>
    </div>
  </article>
</div>
</body>
</html>"""

def publish_post(title, content, category, emoji, keyword):
    """Push blog post to GitHub → auto-deploys to nyspotlightreport.com/blog/[slug]/"""
    slug = slugify(title)
    path = f"site/blog/{slug}/index.html"
    date_str = datetime.now().strftime("%B %d, %Y")
    html = write_post_html(title, content, category, emoji, keyword, date_str)
    sha = get_sha(path)
    body = {"message": f"post: {title[:60]}",
            "content": base64.b64encode(html.encode()).decode()}
    if sha: body["sha"] = sha
    r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",
        json=body, headers=H, timeout=90)
    if r.status_code in [200,201]:
        log.info(f"✅ Published: /blog/{slug}/")
        return f"https://nyspotlightreport.com/blog/{slug}/"
    else:
        log.error(f"❌ Publish failed: {r.status_code}: {r.text[:100]}")
        return None

def run():
    log.info("Blog Publisher starting...")
    from datetime import date
    day_idx = date.today().timetuple().tm_yday % len(POST_TOPICS)
    keyword, category, emoji = POST_TOPICS[day_idx]
    
    if not ANTHROPIC:
        log.warning("No ANTHROPIC_API_KEY — using fallback content")
        title = f"The Complete Guide to {keyword.title()} in 2026"
        content = f"""## What You Need to Know About {keyword.title()}

This guide covers everything entrepreneurs need to know about {keyword} in 2026.

## Why This Matters

Content automation and passive income systems are transforming how entrepreneurs build wealth online. With the right tools, you can build systems that generate revenue while you sleep.

## Getting Started

The first step is understanding the landscape. Most entrepreneurs waste time on manual tasks that could be automated.

## The NY Spotlight Report System

We've built 63 bots that handle daily blog posts, newsletters, social media, and digital product delivery — all on autopilot.

Get your free 30-day automated content plan at nyspotlightreport.com/free-plan/"""
    else:
        log.info(f"Writing Claude-powered post about: {keyword}")
        content = claude(
            "You write for NY Spotlight Report. Direct, expert, no fluff. Audience: entrepreneurs 25-45.",
            f"""Write a complete 1,500-word SEO blog post about: {keyword}

H1 title: Create a compelling, specific title with the keyword
Structure: Introduction, 4-5 H2 sections, conclusion with CTA

Requirements:
- Specific numbers, examples, and actionable steps
- Mention ProFlow AI or nyspotlightreport.com/free-plan/ naturally once
- No generic advice — specific, real, tested insights
- Include at least one stat or data point per section

Write the full post now. Start with # Title""",
            max_tokens=3000
        )
        # Extract title
        lines = content.split("\n")
        title = lines[0].replace("# ","").strip() if lines else f"Complete Guide to {keyword.title()}"
    
    url = publish_post(title, content, category, emoji, keyword)
    if url:
        log.info(f"Live at: {url}")
    
    # Trigger Netlify deploy
    r = requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/248728558/dispatches",
        json={"ref":"main"}, headers=H, timeout=15)
    log.info(f"Deploy triggered: {r.status_code}")

if __name__ == "__main__":
    run()
