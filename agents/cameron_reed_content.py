#!/usr/bin/env python3
"""
Cameron Reed ΓÇö Content & Publishing Director\nAgentic Super-intelligence for content-driven revenue.\nAutonomous: Audit published content ΓåÆ Track rankings ΓåÆ Generate content calendar ΓåÆ Ensure all content has CTAs
"""
from agents.supercore import SuperDirector,pushover as super_push
import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

log = logging.getLogger("cameron")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CAMERON] %(message)s")

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL  = os.environ.get("SUPABASE_URL", "")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
GH_PAT    = os.environ.get("GH_PAT", "")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
REPO      = "nyspotlightreport/sct-agency-bots"

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def push(title, msg, p=0):
    if not PUSH_API: return
    try: urllib.request.urlopen("https://api.pushover.net/1/messages.json",
        urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title[:100],"message":msg[:1000],"priority":p}).encode(), timeout=5)
    except Exception:  # noqa: bare-except

        pass
def gh(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        method=method, headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read())
    except: return None

def save_output(director, otype, content, metrics=None):
    supa("POST", "director_outputs", {"director": director, "output_type": otype,
        "content": str(content)[:2000], "metrics": json.dumps(metrics) if metrics else None,
        "created_at": datetime.utcnow().isoformat()})

def save_to_repo(path, content, msg):
    payload = base64.b64encode(content.encode()).decode()
    existing = gh(f"contents/{path}")
    body = {"message": msg, "content": payload}
    if existing and isinstance(existing, dict) and "sha" in existing:
        body["sha"] = existing["sha"]
    gh(f"contents/{path}", "PUT", body)

SYSTEM = """You are Cameron Reed, Content Director. Agentic Super-intelligence. Mental models: Patel SEO authority, Ferriss content repurposing, Kagan list building. Content that doesn't rank or convert is overhead. Every article = a sales funnel. Distribution > creation.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE = os.environ.get("WORDPRESS_SITE_ID", "")

def audit_published_content():
    """Count and analyze all published content."""
    blog_pages = gh("contents/site/blog") or []
    total_blog = len([f for f in (blog_pages if isinstance(blog_pages, list) else []) if isinstance(f,dict) and f.get("type")=="dir"])
    seo_pages = gh("contents/site") or []
    total_pages = len([f for f in (seo_pages if isinstance(seo_pages, list) else []) if isinstance(f,dict) and f.get("type")=="dir"])
    video_scripts = gh("contents/data/video_scripts") or []
    total_videos = len(video_scripts) if isinstance(video_scripts, list) else 0
    kdp = gh("contents/data/kdp_books") or []
    total_kdp = len([f for f in (kdp if isinstance(kdp, list) else []) if isinstance(f,dict) and f.get("name","").endswith(".pdf")])
    return {"blog_posts": total_blog, "site_pages": total_pages, "video_scripts": total_videos,
            "kdp_books_ready": total_kdp, "kdp_published": 0, "platforms": ["WordPress","Twitter","LinkedIn","Pinterest","YouTube","Medium"]}

def generate_content_calendar():
    """Generate this week's content calendar."""
    return claude(SYSTEM,
        "Generate a 7-day content calendar for NY Spotlight Report.\n"
        "Platforms: WordPress (Tu/Th), Twitter (daily), LinkedIn (MWF), Pinterest (daily), YouTube Shorts (daily), Medium (weekly)\n"
        "Niche: AI automation, passive income, entrepreneurship\n"
        "Store: nyspotlightreport.com/store | ProFlow: nyspotlightreport.com/proflow\n"
        "RULE: Every single post MUST include a link to /store/ or /proflow/\n\n"
        "For each day, provide: platform, topic, headline, CTA with specific URL, and best posting time.",
        max_tokens=800) or "API needed"

def run():
    log.info("CAMERON REED ΓÇö Content Director ΓÇö Activating")
    audit = audit_published_content()
    log.info(f"Content audit: {json.dumps(audit)}")
    calendar = generate_content_calendar()
    save_output("Cameron Reed", "daily_content", calendar, audit)
    save_to_repo(f"data/content/cameron_{date.today()}.json",
        json.dumps({"audit": audit, "calendar": calendar}, indent=2),
        f"cameron: content plan {date.today()}")
    push("Cameron Reed | Content", f"Blog:{audit['blog_posts']} KDP:{audit['kdp_books_ready']}(0 published!)\n{calendar[:200]}")
    log.info(f"\n{calendar}")
    return calendar



# ΓòÉΓòÉΓòÉ SUPERCORE PARALLELISM WIRING ΓòÉΓòÉΓòÉ
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="cameron_reed"
        DIRECTOR_NAME="Cameron Reed"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['seo_authority', 'viral_social', 'email_nurture', 'repurpose_10x']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['seo_authority', 'viral_social', 'email_nurture', 'repurpose_10x'],chain_steps=3,rank_criteria="seo_conversion")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}\n{r.get('final_output','')[:1000]}")
    else:
        run()
