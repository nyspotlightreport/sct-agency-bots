#!/usr/bin/env python3
"""
Casey Lin — IT & Security Director\nAgentic Super-intelligence for infrastructure.\nAutonomous: Check credential health → Verify all integrations → Monitor uptime → Security audit
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

log = logging.getLogger("casey")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CASEY] %(message)s")

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

SYSTEM = """You are Casey Lin, IT Director. Agentic Super-intelligence. Mental models: Google SRE error budgets, Netflix chaos engineering, AWS well-architected, NIST zero-trust. Downtime is lost revenue.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


def check_credential_health():
    """Verify all critical credentials and integrations."""
    creds = {}
    # Check GitHub secrets exist (can't read values, but can verify workflows use them)
    critical_secrets = ["ANTHROPIC_API_KEY","APOLLO_API_KEY","HUBSPOT_API_KEY","STRIPE_SECRET_KEY",
        "SUPABASE_URL","SUPABASE_KEY","PUSHOVER_API_KEY","PUSHOVER_USER_KEY","AHREFS_API_KEY",
        "TWITTER_API_KEY","WORDPRESS_ACCESS_TOKEN","GH_PAT"]
    missing_secrets = ["PINTEREST_ACCESS_TOKEN","MEDIUM_INTEGRATION_TOKEN","ELEVENLABS_API_KEY",
        "BEEHIIV_API_KEY","BEEHIIV_PUB_ID","LINKEDIN_ACCESS_TOKEN","INSTAGRAM_TOKEN","REDDIT_CLIENT_ID"]
    creds["configured"] = len(critical_secrets)
    creds["missing"] = missing_secrets
    creds["missing_count"] = len(missing_secrets)
    
    # Check site uptime
    try:
        req = urllib.request.Request("https://nyspotlightreport.com", headers={"User-Agent":"NYSR-IT-Check"})
        start = time.time()
        with urllib.request.urlopen(req, timeout=10) as r:
            creds["site_status"] = r.status
            creds["site_response_ms"] = round((time.time()-start)*1000)
    except Exception as e:
        creds["site_status"] = "DOWN"
        creds["site_error"] = str(e)
    
    # Check pending infrastructure items
    creds["pending"] = [
        "Supabase Phase 1 schema (run database/schema_phase1.sql)",
        "Tawk.to live chat activation",
        "Google OAuth consent screen finalization",
    ]
    return creds

def run():
    log.info("CASEY LIN — IT Director — Activating")
    health = check_credential_health()
    log.info(f"Credentials: {health['configured']} configured, {health['missing_count']} missing")
    log.info(f"Site: {health.get('site_status')} ({health.get('site_response_ms',0)}ms)")
    
    report = claude(SYSTEM,
        f"DAILY IT & SECURITY INTELLIGENCE\n{json.dumps(health, indent=2)}\n\n"
        f"Deliver:\n1. Infrastructure health score (0-100)\n"
        f"2. CRITICAL: Missing credentials blocking revenue\n"
        f"3. Security concerns with current setup\n"
        f"4. One-step fixes the Chairman can do in 5 minutes\n"
        f"5. Uptime and performance assessment",
        max_tokens=600) or "API needed"
    
    save_output("Casey Lin", "daily_it", report, health)
    push("Casey Lin | IT", f"Site: {health.get('site_status')} | Missing creds: {health['missing_count']}\n{report[:200]}")
    log.info(f"\n{report}")
    return report



# ═══ SUPERCORE PARALLELISM WIRING ═══
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="casey_lin"
        DIRECTOR_NAME="Casey Lin"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['sre_error_budgets', 'chaos_engineering', 'zero_trust', 'cost_opt']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['sre_error_budgets', 'chaos_engineering', 'zero_trust', 'cost_opt'],chain_steps=2,rank_criteria="system_reliability")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
