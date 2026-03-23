#!/usr/bin/env python3
"""
Nina Caldwell ΓÇö Strategy & ROI Director\nFully Developed Agentic Super-intelligence for unit economics.\nAutonomous: Pull revenue ΓåÆ Calculate ROI all initiatives ΓåÆ Forecast 30/60/90 ΓåÆ Recommend highest-ROI action ΓåÆ Store to Supabase ΓåÆ Brief Chairman
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

log = logging.getLogger("nina")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NINA] %(message)s")

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

SYSTEM = """You are Nina Caldwell, Strategy & ROI Director. Agentic Super-intelligence. Mental models: Buffett ROIC, Thiel power law, Porter value chain, BCG growth-share, Kaplan balanced scorecard. Every dollar must return 10x. Every strategy has a cashflow timeline. You calculate ROI on EVERYTHING. ALWAYS provide specific dollar amounts.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

def gather_financials():
    data = {"date": str(date.today()), "revenue_today": 0, "revenue_mtd": 0,
            "expenses_monthly": 121, "pipeline_value": 2985, "affiliate_pending": 17,
            "offers": {"proflow_starter": 97, "proflow_growth": 297, "dfy_setup": 1497, "dfy_agency": 4997}}
    if STRIPE_KEY:
        try:
            auth = base64.b64encode(f"{STRIPE_KEY}:".encode()).decode()
            req = urllib.request.Request("https://api.stripe.com/v1/balance", 
                headers={"Authorization": f"Basic {auth}"})
            with urllib.request.urlopen(req, timeout=10) as r:
                bal = json.loads(r.read())
                data["stripe_balance"] = bal.get("available", [{}])[0].get("amount", 0) / 100
        except Exception as e: log.warning(f"Stripe: {e}")
    contacts = supa("GET", "contacts", query="?select=stage,score&order=score.desc&limit=100") or []
    data["total_contacts"] = len(contacts) if isinstance(contacts, list) else 0
    return data

def roi_analysis(financials):
    initiatives = [
        {"name":"KDP Books (15 ready)","cost":0,"projected_monthly":80,"days_to_revenue":7,"status":"NOT_PUBLISHED","roi":"infinite"},
        {"name":"Gumroad Products (10 ready)","cost":0,"projected_monthly":120,"days_to_revenue":7,"status":"NEEDS_BANK","roi":"infinite"},
        {"name":"Affiliate Programs","cost":0,"projected_monthly":500,"days_to_revenue":60,"status":"17_pending"},
        {"name":"Cold Outreach (Apollo)","cost":99,"projected_monthly":1500,"days_to_revenue":30,"status":"active"},
        {"name":"SEO Content","cost":0,"projected_monthly":200,"days_to_revenue":90,"status":"34_pages_live"},
        {"name":"ProFlow SaaS","cost":0,"projected_monthly":970,"days_to_revenue":60,"status":"0_customers"},
        {"name":"DFY Agency","cost":0,"projected_monthly":4997,"days_to_revenue":45,"status":"0_customers"},
        {"name":"Bandwidth Sharing","cost":0,"projected_monthly":35,"days_to_revenue":0,"status":"running_$2"},
    ]
    return initiatives

def run():
    log.info("NINA CALDWELL ΓÇö Strategy & ROI Director ΓÇö Activating")
    fin = gather_financials()
    initiatives = roi_analysis(fin)
    log.info(f"Financials: {json.dumps(fin, indent=2)}")
    
    analysis = claude(SYSTEM,
        f"DAILY STRATEGIC ANALYSIS\nFinancials: {json.dumps(fin)}\nInitiatives by ROI: {json.dumps(initiatives)}\n\n"
        f"Deliver:\n1. #1 highest-ROI action executable in 60 minutes (specific $)\n"
        f"2. 30/60/90 forecast: conservative/moderate/aggressive (specific $)\n"
        f"3. Kill recommendation: lowest ROI initiative\n"
        f"4. Double-down recommendation: highest ROI initiative\n"
        f"5. Fastest path to next dollar received\nEvery sentence must contain a number.",
        max_tokens=800) or "ANTHROPIC_API_KEY required for analysis"
    
    save_output("Nina Caldwell", "daily_strategy", analysis, fin)
    save_to_repo(f"data/strategy/nina_{date.today()}.json",
        json.dumps({"analysis": analysis, "financials": fin, "initiatives": initiatives}, indent=2),
        f"nina: strategy {date.today()}")
    push("Nina Caldwell | Strategy", analysis[:300])
    log.info(f"\n{analysis}")
    return analysis



# ΓòÉΓòÉΓòÉ SUPERCORE PARALLELISM WIRING ΓòÉΓòÉΓòÉ
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="nina_caldwell"
        DIRECTOR_NAME="Nina Caldwell"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['buffett_roic', 'thiel_power_law', 'porter_value_chain', 'kaplan_scorecard']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['buffett_roic', 'thiel_power_law', 'porter_value_chain', 'kaplan_scorecard'],chain_steps=3,rank_criteria="roi_multiple")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
