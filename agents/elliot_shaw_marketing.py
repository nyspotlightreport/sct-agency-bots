#!/usr/bin/env python3
"""
Elliot Shaw — Marketing Director\nFully Developed Agentic Super-intelligence for demand generation.\nAutonomous: Audit all content → Check social links for store CTAs → SEO keyword gaps → Campaign recommendations → Store to Supabase
"""
from agents.supercore import SuperDirector,pushover as super_push
import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

log = logging.getLogger("elliot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ELLIOT] %(message)s")

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
    except: pass

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

SYSTEM = """You are Elliot Shaw, Marketing Director. Agentic Super-intelligence. Mental models: Godin permission marketing, Halbert copywriting, Ogilvy brand building, Cialdini persuasion, Hormozi offer creation, Brunson funnel architecture. Marketing without conversion is decoration. Every piece of content must drive a click to a payment link.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


AHREFS_KEY = os.environ.get("AHREFS_API_KEY", "")
WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE = os.environ.get("WORDPRESS_SITE_ID", "")

def audit_content_ctas():
    """Check if published content has store/payment CTAs."""
    issues = []
    # Check site pages for payment links
    site_data = gh("contents/site") or []
    if isinstance(site_data, list):
        pages_checked = len([f for f in site_data if f.get("type") == "dir"])
        issues.append(f"Site has {pages_checked} page directories")
    # Check if social posts include store links
    social_bot = gh("contents/bots/social_scheduler_bot.py")
    if social_bot:
        content = base64.b64decode(social_bot.get("content","")).decode("utf-8", errors="ignore")
        has_store_link = "nyspotlightreport.com/store" in content or "nyspotlightreport.com/proflow" in content
        if not has_store_link:
            issues.append("CRITICAL: Social posts do NOT contain store/payment links")
    return issues

def generate_campaign_plan():
    """Generate today's marketing campaign plan."""
    return claude(SYSTEM,
        "Generate today's marketing action plan.\n"
        "Current state: 34 SEO pages live, social posting daily (Twitter/LinkedIn/Pinterest/WordPress), "
        "0 paid ads running, Ahrefs connected, 126 site pages.\n"
        "Store: https://nyspotlightreport.com/store/\n"
        "ProFlow: https://nyspotlightreport.com/proflow/\n\n"
        "Deliver:\n1. 3 specific social posts to write TODAY (with exact copy and CTA links)\n"
        "2. 1 SEO keyword to target this week (with search volume estimate)\n"
        "3. 1 conversion optimization to implement today\n"
        "4. Which existing page needs a stronger CTA added\n"
        "5. Projected traffic impact of today's actions (specific number)",
        max_tokens=800) or "API key needed"

def run():
    log.info("ELLIOT SHAW — Marketing Director — Activating")
    issues = audit_content_ctas()
    for i in issues: log.info(f"  AUDIT: {i}")
    
    campaign = generate_campaign_plan()
    save_output("Elliot Shaw", "daily_marketing", campaign, {"issues": issues})
    save_to_repo(f"data/marketing/elliot_{date.today()}.json",
        json.dumps({"campaign": campaign, "audit_issues": issues, "date": str(date.today())}, indent=2),
        f"elliot: marketing plan {date.today()}")
    push("Elliot Shaw | Marketing", f"Issues: {len(issues)}\n{campaign[:200]}")
    log.info(f"\n{campaign}")
    return campaign



# ═══ SUPERCORE PARALLELISM WIRING ═══
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="elliot_shaw"
        DIRECTOR_NAME="Elliot Shaw"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['hormozi_offer', 'ogilvy_brand', 'cialdini_persuasion', 'brunson_funnel']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['hormozi_offer', 'ogilvy_brand', 'cialdini_persuasion', 'brunson_funnel'],chain_steps=3,rank_criteria="conversion_rate")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
