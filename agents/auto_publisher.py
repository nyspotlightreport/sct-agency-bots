#!/usr/bin/env python3
"""
agents/auto_publisher.py — Daily Auto-Publisher
Generates a blog post via Claude, commits to BOTH repos, deploys automatically.
This is the missing link: Content Engine → Live Site.
"""
import os,sys,json,logging,time,hashlib,re
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),".."))
log=logging.getLogger("auto_publisher")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [PUBLISH] %(message)s")
import urllib.request as urlreq,urllib.parse,base64

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
GH_PAT=os.environ.get("GH_PAT","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")

LIVE_REPO = "nyspotlightreport/NY-Spotlight-Report-good"
SOURCE_REPO = "nyspotlightreport/sct-agency-bots"

def claude(prompt, max_tokens=2000):
    if not ANTHROPIC: return ""
    try:
        data=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":max_tokens,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req=urlreq.Request("https://api.anthropic.com/v1/messages",data=data,
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
        with urlreq.urlopen(req,timeout=60) as r: return json.loads(r.read())["content"][0]["text"]
    except: return ""

def gh_commit(repo, path, content, message):
    """Commit a file to a GitHub repo."""
    if not GH_PAT: return False
    encoded = base64.b64encode(content.encode()).decode()
    # Check if file exists first
    try:
        req=urlreq.Request(f"https://api.github.com/repos/{repo}/contents/{path}",
            headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json"})
        with urlreq.urlopen(req,timeout=10) as r:
            existing=json.loads(r.read())
            sha=existing.get("sha","")
    except Exception:  # noqa: bare-except
        sha=""
    data={"message":message,"content":encoded}
    if sha: data["sha"]=sha
    try:
        req=urlreq.Request(f"https://api.github.com/repos/{repo}/contents/{path}",
            data=json.dumps(data).encode(),method="PUT",
            headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
        urlreq.urlopen(req,timeout=15)
        log.info(f"  Committed to {repo}: {path}")
        return True
    except Exception as e:
        log.info(f"  Commit failed: {str(e)[:100]}")
        return False

def push(t,m):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000]}).encode(),timeout=5)
    except Exception:  # noqa: bare-except

        pass
def generate_blog_post():
    """Generate a full SEO-optimized blog post."""
    topics = [
        "How AI Content Automation Saves Agencies $4,000 Per Month",
        "5 Signs Your Agency Needs an AI Content Engine in 2026",
        "The Complete Guide to Automated Content Marketing for Small Businesses",
        "Why Manual Content Creation is Costing Your Agency Clients",
        "AI Voice Agents: The Future of Business Phone Systems",
        "How to Build a Content Pipeline That Runs While You Sleep",
        "ProFlow vs Hiring a Content Team: Real Cost Comparison",
        "The Agency Owner's Guide to AI-Powered Client Acquisition",
    ]
    import random
    topic = random.choice(topics)
    slug = re.sub(r'[^a-z0-9]+','-',topic.lower()).strip('-')
    
    log.info(f"Generating: {topic}")
    content = claude(f"""Write a complete, SEO-optimized blog post for NY Spotlight Report about: "{topic}"

Requirements:
- 1,500-2,000 words
- Include H1, H2, H3 headers
- Natural keyword density for the topic
- Include a meta description (under 160 chars)
- Include 3-5 internal links to nyspotlightreport.com/proflow/ and nyspotlightreport.com/pricing/
- Professional, authoritative tone
- Include actionable takeaways
- End with a clear CTA to try ProFlow
- Format as a complete HTML page with styling that matches the NY Spotlight Report editorial look

Use this HTML template wrapper:
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>[TITLE] | NY Spotlight Report</title>
<meta name="description" content="[META DESC]">
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Outfit',sans-serif;background:#f7f5f0;color:#141413}}nav{{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(247,245,240,.92);backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,0,0,.08);padding:0 clamp(24px,5vw,80px);height:64px;display:flex;align-items:center;justify-content:space-between}}.nl{{font-family:'Instrument Serif',serif;font-size:18px}}.nl i{{color:#c9a84c;font-style:italic}}article{{max-width:720px;margin:0 auto;padding:120px clamp(24px,5vw,80px) 80px}}h1{{font-family:'Instrument Serif',serif;font-size:clamp(32px,5vw,48px);line-height:1.1;margin-bottom:16px}}h2{{font-family:'Instrument Serif',serif;font-size:24px;margin:32px 0 12px}}h3{{font-size:18px;font-weight:600;margin:24px 0 8px}}p{{font-size:16px;line-height:1.8;margin-bottom:16px;color:#3d3929}}a{{color:#c9a84c}}.meta{{font-size:13px;color:#8a8578;margin-bottom:32px}}.cta{{background:#141413;border-radius:16px;padding:48px;text-align:center;margin:48px 0}}.cta h2{{color:#f7f5f0;font-size:28px;margin-bottom:12px}}.cta p{{color:rgba(247,245,240,.6)}}.cta a{{background:#c9a84c;color:#141413;padding:14px 32px;border-radius:100px;font-weight:700;text-decoration:none;display:inline-block;margin-top:16px}}</style>
</head><body>
<nav><a href="/" class="nl">NY Spotlight <i>Report</i></a><div><a href="/blog/" style="font-size:13px;color:#8a8578;margin-right:24px">Blog</a><a href="/login/" style="font-size:13px;color:#c9a84c;border:1px solid #c9a84c;padding:8px 20px;border-radius:100px">Log In</a></div></nav>
<article>
[CONTENT HERE]
</article>
</body></html>
""", 3000)
    return topic, slug, content

def run():
    log.info("="*60)
    log.info("AUTO-PUBLISHER — Daily Blog Post Generator")
    log.info(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    log.info("="*60)
    
    topic, slug, html = generate_blog_post()
    if not html or len(html) < 500:
        log.info("  FAILED: Blog post generation returned empty/short content")
        return {"status":"failed","reason":"empty content"}
    
    log.info(f"  Generated: {len(html)} chars")
    
    # Commit to LIVE repo (this triggers Netlify deploy)
    live_path = f"blog/{slug}/index.html"
    live_ok = gh_commit(LIVE_REPO, live_path, html, f"AUTO-PUBLISH: {topic}")
    
    # Also commit to source repo
    source_path = f"site/blog/{slug}/index.html"
    source_ok = gh_commit(SOURCE_REPO, source_path, html, f"AUTO-PUBLISH: {topic}")
    
    # Log to Supabase
    if SUPA_URL:
        try:
            record={"director":"Auto Publisher","output_type":"blog_post",
                "content":json.dumps({"topic":topic,"slug":slug,"chars":len(html),"live":live_ok,"source":source_ok})[:4000],
                "created_at":datetime.utcnow().isoformat()}
            req=urlreq.Request(f"{SUPA_URL}/rest/v1/director_outputs",data=json.dumps(record).encode(),method="POST",
                headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=minimal"})
            urlreq.urlopen(req,timeout=10)
        except Exception:  # noqa: bare-except

            pass
    push("Blog Published",f"{topic}\n{len(html)} chars | Live: {live_ok}")
    log.info(f"\n  Topic: {topic}")
    log.info(f"  Slug: {slug}")
    log.info(f"  Live repo: {'OK' if live_ok else 'FAILED'}")
    log.info(f"  Source repo: {'OK' if source_ok else 'FAILED'}")
    return {"status":"published","topic":topic,"slug":slug,"chars":len(html),"live":live_ok}

if __name__=="__main__":
    run()
