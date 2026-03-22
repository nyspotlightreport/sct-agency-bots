#!/usr/bin/env python3
"""
Vivian Cole ΓÇö PR & Reputation Director\nAgentic Super-intelligence for brand authority.\nAutonomous: Monitor mentions ΓåÆ Track domain authority ΓåÆ Generate press pitches ΓåÆ Build media list
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

log = logging.getLogger("vivian")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [VIVIAN] %(message)s")

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

SYSTEM = """You are Vivian Cole, PR Director. Agentic Super-intelligence. Mental models: Godin tribes, Ries PR over ads, Gladwell tipping point. One Forbes mention > 1,000 cold emails. Engineer coverage.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


AHREFS_KEY = os.environ.get("AHREFS_API_KEY", "")

def check_brand_signals():
    """Check current brand presence and authority signals."""
    signals = {"domain": "nyspotlightreport.com", "site_live": False, "pages": 0}
    try:
        req = urllib.request.Request("https://nyspotlightreport.com", headers={"User-Agent":"NYSR-Bot"})
        with urllib.request.urlopen(req, timeout=10) as r:
            signals["site_live"] = r.status == 200
            signals["site_size_kb"] = len(r.read()) // 1024
    except: pass
    site = gh("contents/site") or []
    signals["pages"] = len([f for f in (site if isinstance(site, list) else []) if isinstance(f,dict) and f.get("type")=="dir"])
    return signals

def generate_pr_pitches():
    """Generate 3 media pitches for this week."""
    return claude(SYSTEM,
        "Generate 3 media pitch emails for NY Spotlight Report.\n"
        "Company: AI-powered content agency in Coram, NY. Chairman: S.C. Thomas.\n"
        "Angle 1: 'Solo founder builds 96-agent AI agency that runs 222 bots autonomously'\n"
        "Angle 2: 'How AI is replacing $60k/year content teams for entrepreneurs'\n"
        "Angle 3: 'NY-based startup automates entire business operations with Claude AI'\n\n"
        "For each pitch: subject line, 150-word email body, 3 target outlet types (tech, business, local).\n"
        "Make them newsworthy, not salesy. Include a specific data point in each.",
        max_tokens=800) or "API needed"

def run():
    log.info("VIVIAN COLE ΓÇö PR Director ΓÇö Activating")
    signals = check_brand_signals()
    pitches = generate_pr_pitches()
    save_output("Vivian Cole", "weekly_pr", pitches, signals)
    push("Vivian Cole | PR", f"Site live: {signals['site_live']}, Pages: {signals['pages']}\n{pitches[:200]}")
    log.info(f"\n{pitches}")
    return pitches



# ΓòÉΓòÉΓòÉ SUPERCORE PARALLELISM WIRING ΓòÉΓòÉΓòÉ
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="vivian_cole"
        DIRECTOR_NAME="Vivian Cole"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['earned_media', 'thought_leadership', 'crisis_prevention', 'authority_build']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['earned_media', 'thought_leadership', 'crisis_prevention', 'authority_build'],chain_steps=3,rank_criteria="media_pickup")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
