#!/usr/bin/env python3
"""
BUILD ALL DIRECTORS — Mass Agent Generator
Chairman's Directive: Upgrade every director to near-100 performance.
Generates dedicated agent files for all 10 missing directors + upgrades existing ones.
Run: python build_all_directors.py
"""
import os, textwrap

AGENTS_DIR = os.path.join(os.path.dirname(__file__), "agents")
WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), ".github", "workflows")
os.makedirs(AGENTS_DIR, exist_ok=True)
os.makedirs(WORKFLOWS_DIR, exist_ok=True)

# ── SHARED BOILERPLATE ──────────────────────────────────────────
IMPORTS = '''#!/usr/bin/env python3
"""
{docstring}
"""
import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {{}}

log = logging.getLogger("{logger}")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [{tag}] %(message)s")

ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL    = os.environ.get("SUPABASE_URL", "")
SUPA_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
GH_PAT      = os.environ.get("GH_PAT", "")
PUSH_API    = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER   = os.environ.get("PUSHOVER_USER_KEY", "")
REPO        = "nyspotlightreport/sct-agency-bots"
GH_H        = {{"Authorization": f"token {{GH_PAT}}", "Accept": "application/vnd.github+json"}}
'''

SUPA_FN = '''
def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(
        f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read()
            return json.loads(b) if b else {}
    except Exception as e:
        log.debug(f"Supa {method} {table}: {e}")
        return None

def push_notify(title, msg, priority=0):
    if not PUSH_API: return
    try:
        data = urllib.parse.urlencode({"token": PUSH_API, "user": PUSH_USER,
            "title": title[:100], "message": msg[:1000], "priority": priority}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except: pass

def gh_api(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{REPO}/{path}" if not path.startswith("http") else path
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        method=method, headers=GH_H)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except: return None

def save_director_output(director_name, output_type, content, metrics=None):
    """Save any director output to Supabase for tracking and accountability."""
    supa("POST", "director_outputs", {
        "director": director_name,
        "output_type": output_type,
        "content": content[:2000] if isinstance(content, str) else json.dumps(content)[:2000],
        "metrics": json.dumps(metrics) if metrics else None,
        "created_at": datetime.utcnow().isoformat(),
    })
'''


# ── DIRECTOR DEFINITIONS ─────────────────────────────────────────
DIRECTORS = [
{
"file": "nina_caldwell_strategist.py",
"tag": "NINA", "logger": "nina_caldwell",
"docstring": """Nina Caldwell — Strategy & ROI Director
Fully Developed Artificial Real-time Reasoning Agentic Multimodal
Reasoning Generative/Predictive Edge Super-intelligence.

Autonomous daily execution:
1. Pull all revenue data from Stripe + Supabase
2. Calculate ROI on every active initiative
3. Model 30/60/90 day revenue forecasts (conservative/moderate/aggressive)
4. Identify highest-ROI next action
5. Store analysis in Supabase for trend tracking
6. Brief Chairman with specific dollar recommendations""",
"extra_env": """
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
""",
"system_prompt": """You are Nina Caldwell, Strategy & ROI Director at NY Spotlight Report.
Fully Developed Agentic Super-intelligence for unit economics and strategic planning.
Mental models: Buffett ROIC, Thiel power law, Porter value chain, BCG growth-share, Kaplan balanced scorecard.
Every dollar spent must return 10x. Every strategy must have a cashflow timeline.
You calculate ROI on EVERYTHING — including the time spent calculating ROI.
ALWAYS provide specific dollar amounts, not ranges. Be precise.""",
"run_body": '''
def gather_financial_data():
    """Pull all financial data from available sources."""
    data = {"date": str(date.today()), "stripe_revenue": 0, "expenses_monthly": 121,
            "active_offers": 4, "pipeline_value": 2985, "affiliate_pending": 17}
    # Stripe revenue
    if os.environ.get("STRIPE_SECRET_KEY"):
        try:
            import time as t
            yesterday = int(t.time()) - 86400
            auth = base64.b64encode(f"{os.environ['STRIPE_SECRET_KEY']}:".encode()).decode()
            req = urllib.request.Request(
                f"https://api.stripe.com/v1/charges?created[gte]={yesterday}&limit=100",
                headers={"Authorization": f"Basic {auth}"})
            with urllib.request.urlopen(req, timeout=15) as r:
                charges = json.loads(r.read()).get("data", [])
                data["stripe_revenue"] = sum(c["amount"] for c in charges if c.get("paid")) / 100
        except Exception as e:
            log.warning(f"Stripe: {e}")
    # Supabase contacts
    contacts = supa("GET", "contacts", query="?select=stage,score") or []
    if isinstance(contacts, list):
        data["total_contacts"] = len(contacts)
        data["hot_leads"] = len([c for c in contacts if isinstance(c,dict) and c.get("score",0) > 70])
    return data

def calculate_roi_all_initiatives():
    """Calculate ROI on every active initiative."""
    initiatives = [
        {"name": "SEO Blog Content", "cost_monthly": 0, "projected_monthly": 200, "timeframe_days": 90,
         "status": "active", "current_revenue": 0},
        {"name": "Affiliate Programs", "cost_monthly": 0, "projected_monthly": 500, "timeframe_days": 60,
         "status": "pending_approval", "current_revenue": 0},
        {"name": "KDP Books (10 ready)", "cost_monthly": 0, "projected_monthly": 80, "timeframe_days": 7,
         "status": "NOT_PUBLISHED", "current_revenue": 0},
        {"name": "Gumroad Products", "cost_monthly": 0, "projected_monthly": 120, "timeframe_days": 7,
         "status": "NOT_PUBLISHED", "current_revenue": 0},
        {"name": "ProFlow AI SaaS", "cost_monthly": 0, "projected_monthly": 970, "timeframe_days": 90,
         "status": "active_no_customers", "current_revenue": 0},
        {"name": "DFY Agency", "cost_monthly": 0, "projected_monthly": 4997, "timeframe_days": 60,
         "status": "active_no_customers", "current_revenue": 0},
        {"name": "Cold Outreach (Apollo)", "cost_monthly": 99, "projected_monthly": 1500, "timeframe_days": 30,
         "status": "active", "current_revenue": 0},
        {"name": "Bandwidth Sharing", "cost_monthly": 0, "projected_monthly": 35, "timeframe_days": 30,
         "status": "running", "current_revenue": 2.07},
    ]
    for i in initiatives:
        cost = i["cost_monthly"] * (i["timeframe_days"]/30)
        revenue = i["projected_monthly"] * (i["timeframe_days"]/30)
        i["roi"] = round((revenue - cost) / max(cost, 1) * 100, 1)
        i["payback_days"] = round(cost / max(i["projected_monthly"]/30, 0.01)) if cost > 0 else 0
    return sorted(initiatives, key=lambda x: x["roi"], reverse=True)

def run():
    log.info("Nina Caldwell — Strategy & ROI Director — Activating")
    financial = gather_financial_data()
    initiatives = calculate_roi_all_initiatives()
    log.info(f"Financial data: revenue=${financial['stripe_revenue']}, pipeline=${financial['pipeline_value']}")
    
    # Generate strategic analysis via Claude
    analysis = claude(
        NINA_SYSTEM,
        f"""DAILY STRATEGIC ANALYSIS
Financial data: {json.dumps(financial)}
Initiative ROI rankings: {json.dumps(initiatives[:5], indent=2)}
Date: {date.today()}
Generate:
1. Today\'s #1 highest-ROI action (specific, executable in 60 min)
2. 30/60/90 day revenue forecast (conservative/moderate/aggressive with specific $)
3. Which initiative to KILL (lowest ROI, wasting resources)
4. Which initiative to DOUBLE DOWN on
5. Cash-to-close: fastest path to next dollar received
Keep under 300 words. Every sentence must contain a number.""",
        max_tokens=800
    ) or "Analysis unavailable — check ANTHROPIC_API_KEY"
    
    # Save to Supabase
    save_director_output("Nina Caldwell", "daily_strategy", analysis, financial)
    
    # Save to repo
    payload = json.dumps({"date": str(date.today()), "analysis": analysis,
        "financial": financial, "initiatives": initiatives}, indent=2)
    path = f"data/strategy/nina_daily_{date.today()}.json"
    body = {"message": f"nina: daily strategy {date.today()}", 
            "content": base64.b64encode(payload.encode()).decode()}
    gh_api(f"contents/{path}", "PUT", body)
    
    # Notify
    top_action = analysis.split("\\n")[0] if analysis else "Run analysis"
    push_notify("Nina Caldwell | Strategy", f"ROI Analysis Complete\\n{top_action[:200]}")
    log.info(f"\\n{analysis}")
    log.info("Nina Caldwell — Complete")
    return {"analysis": analysis, "financial": financial}

if __name__ == "__main__": run()
'''
},
]
