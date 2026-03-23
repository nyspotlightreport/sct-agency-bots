#!/usr/bin/env python3
"""
Blake Sutton ΓÇö Finance Director\nAgentic Super-intelligence for financial intelligence.\nAutonomous: Pull Stripe ΓåÆ Track expenses ΓåÆ Calculate burn rate ΓåÆ Forecast runway ΓåÆ Unit economics
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

log = logging.getLogger("blake")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [BLAKE] %(message)s")

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

SYSTEM = """You are Blake Sutton, Finance Director. Agentic Super-intelligence. Mental models: Buffett intrinsic value, Dalio all-weather, Graham margin of safety. Cash flow > income statement. Runway is life. Every expense justifies its ROI.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

def pull_financial_data():
    """Comprehensive financial picture."""
    fin = {"date": str(date.today()), "revenue": {"stripe_mtd": 0, "gumroad_mtd": 0, "total_mtd": 0},
        "expenses": {"apollo_pro": 99, "elevenlabs": 22, "total_monthly": 121},
        "assets": {"stripe_payment_links": 7, "gumroad_products": 10, "kdp_books": 15,
            "redbubble_designs": 20, "site_pages": 126, "blog_posts": 7},
        "pipeline": {"hubspot_deals": 5, "pipeline_value": 2985},
        "burn_rate_daily": round(121/30, 2), "runway_days": "infinite (no debt)"}
    
    if STRIPE_KEY:
        try:
            auth = base64.b64encode(f"{STRIPE_KEY}:".encode()).decode()
            month_start = int(datetime(date.today().year, date.today().month, 1).timestamp())
            req = urllib.request.Request(
                f"https://api.stripe.com/v1/charges?created[gte]={month_start}&limit=100",
                headers={"Authorization": f"Basic {auth}"})
            with urllib.request.urlopen(req, timeout=15) as r:
                charges = json.loads(r.read()).get("data", [])
                fin["revenue"]["stripe_mtd"] = sum(c["amount"] for c in charges if c.get("paid")) / 100
                fin["revenue"]["total_mtd"] = fin["revenue"]["stripe_mtd"]
        except Exception as e: log.warning(f"Stripe: {e}")
    return fin

def run():
    log.info("BLAKE SUTTON ΓÇö Finance Director ΓÇö Activating")
    fin = pull_financial_data()
    log.info(f"Financial snapshot: Revenue MTD ${fin['revenue']['total_mtd']}, Expenses ${fin['expenses']['total_monthly']}/mo")
    
    analysis = claude(SYSTEM,
        f"DAILY FINANCIAL INTELLIGENCE\n{json.dumps(fin, indent=2)}\n\n"
        f"Deliver:\n1. P&L summary: revenue vs expenses this month\n"
        f"2. Unit economics: CAC, LTV estimate per offer tier\n"
        f"3. Burn rate analysis and runway\n"
        f"4. Revenue quality score (recurring vs one-time mix)\n"
        f"5. Top financial risk and mitigation\n"
        f"6. Business valuation update (market value, liquidation value)",
        max_tokens=600) or "API needed"
    
    save_output("Blake Sutton", "daily_finance", analysis, fin)
    save_to_repo(f"data/finance/blake_{date.today()}.json",
        json.dumps({"financials": fin, "analysis": analysis}, indent=2),
        f"blake: finance {date.today()}")
    push("Blake Sutton | Finance", f"MTD: ${fin['revenue']['total_mtd']} | Burn: ${fin['expenses']['total_monthly']}/mo\n{analysis[:200]}")
    log.info(f"\n{analysis}")
    return analysis



# ΓòÉΓòÉΓòÉ SUPERCORE PARALLELISM WIRING ΓòÉΓòÉΓòÉ
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="blake_sutton"
        DIRECTOR_NAME="Blake Sutton"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['buffett_value', 'dalio_allweather', 'graham_safety', 'unit_economics']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['buffett_value', 'dalio_allweather', 'graham_safety', 'unit_economics'],chain_steps=2,rank_criteria="risk_adjusted_return")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
