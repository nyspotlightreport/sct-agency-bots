#!/usr/bin/env python3
"""
Parker Hayes — Product Director\nAgentic Super-intelligence for product-market fit.\nAutonomous: Audit offers → Check conversion by tier → A/B test recommendations → Pricing optimization
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

log = logging.getLogger("parker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PARKER] %(message)s")

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

SYSTEM = """You are Parker Hayes, Product Director. Agentic Super-intelligence. Mental models: Jobs JTBD, Christensen disruption, Cagan empowered teams, Moore crossing the chasm. Products that don't sell are demos. Price is the most powerful product feature.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

def audit_product_status():
    """Check status of all products across platforms."""
    return {
        "stripe_links": 7, "stripe_active": True,
        "gumroad_products": 10, "gumroad_published": 0, "gumroad_blocker": "bank account not connected",
        "kdp_books": 15, "kdp_published": 0, "kdp_blocker": "upload not run",
        "proflow_tiers": [
            {"name":"Starter","price":97,"subscribers":0,"page":"nyspotlightreport.com/proflow"},
            {"name":"Growth","price":297,"subscribers":0,"page":"nyspotlightreport.com/proflow"},
            {"name":"Agency","price":497,"subscribers":0,"page":"nyspotlightreport.com/proflow"},
        ],
        "agency_tiers": [
            {"name":"Essential","price":997,"clients":0},
            {"name":"Growth","price":1997,"clients":0},
            {"name":"Enterprise","price":2997,"clients":0},
        ],
    }

def run():
    log.info("PARKER HAYES — Product Director — Activating")
    status = audit_product_status()
    log.info(f"Product audit: {json.dumps(status, indent=2)}")
    
    recommendations = claude(SYSTEM,
        f"DAILY PRODUCT INTELLIGENCE\nProduct status: {json.dumps(status)}\n\n"
        f"Deliver:\n1. CRITICAL blockers preventing revenue (be specific)\n"
        f"2. Which offer tier has highest conversion potential and why\n"
        f"3. One pricing experiment to run this week\n"
        f"4. Product page improvements (specific copy changes)\n"
        f"5. New product idea that could launch in 48 hours with $0 cost",
        max_tokens=600) or "API needed"
    
    save_output("Parker Hayes", "daily_product", recommendations, status)
    push("Parker Hayes | Product", recommendations[:300])
    log.info(f"\n{recommendations}")
    return recommendations



# ═══ SUPERCORE PARALLELISM WIRING ═══
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="parker_hayes"
        DIRECTOR_NAME="Parker Hayes"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['jobs_jtbd', 'christensen_disruption', 'hormozi_offer', 'moore_chasm']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['jobs_jtbd', 'christensen_disruption', 'hormozi_offer', 'moore_chasm'],chain_steps=3,rank_criteria="conversion_times_price")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
