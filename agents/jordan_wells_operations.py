#!/usr/bin/env python3
"""
Jordan Wells — Operations Director\nAgentic Super-intelligence for execution excellence.\nAutonomous: Audit all 133 workflows → Identify bottlenecks → Track completion rates → Optimize scheduling
"""
import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

log = logging.getLogger("jordan")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [JORDAN] %(message)s")

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

SYSTEM = """You are Jordan Wells, Operations Director. Agentic Super-intelligence. Mental models: Goldratt Theory of Constraints, Lean Six Sigma, Toyota Production System, Deming PDCA. The bottleneck determines speed. Find it. Remove it.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


def audit_workflow_health():
    """Pull GitHub Actions workflow run data and analyze health."""
    runs = gh("actions/runs?per_page=100") or {}
    wf_runs = runs.get("workflow_runs", [])
    health = {}
    for r in wf_runs:
        name = r.get("name", "unknown")
        if name not in health:
            health[name] = {"success": 0, "failure": 0, "total": 0, "last": r.get("updated_at","")}
        health[name]["total"] += 1
        if r.get("conclusion") == "success": health[name]["success"] += 1
        elif r.get("conclusion") == "failure": health[name]["failure"] += 1
    
    for n, s in health.items():
        s["rate"] = round(s["success"]/max(s["total"],1)*100)
        s["status"] = "green" if s["rate"] >= 80 else "yellow" if s["rate"] >= 50 else "red"
    
    return health

def identify_bottlenecks(health):
    """Find the top bottlenecks in the system."""
    failing = sorted([(n,s) for n,s in health.items() if s["status"]=="red"], key=lambda x: x[1]["rate"])
    stale = sorted([(n,s) for n,s in health.items() if s["total"] < 2], key=lambda x: x[1]["total"])
    return {"failing_workflows": [n for n,_ in failing[:5]], "stale_workflows": [n for n,_ in stale[:5]],
            "total_workflows": len(health), "healthy": len([n for n,s in health.items() if s["status"]=="green"]),
            "degraded": len([n for n,s in health.items() if s["status"]=="yellow"]),
            "broken": len([n for n,s in health.items() if s["status"]=="red"])}

def run():
    log.info("JORDAN WELLS — Operations Director — Activating")
    health = audit_workflow_health()
    bottlenecks = identify_bottlenecks(health)
    log.info(f"Workflows: {bottlenecks['total_workflows']} total, {bottlenecks['healthy']} healthy, {bottlenecks['broken']} broken")
    
    ops_plan = claude(SYSTEM,
        f"DAILY OPERATIONS INTELLIGENCE\nWorkflow health: {json.dumps(bottlenecks)}\n"
        f"Failing workflows: {json.dumps(bottlenecks['failing_workflows'])}\n\n"
        f"Deliver:\n1. #1 bottleneck in the system right now and how to fix it\n"
        f"2. Which workflows should be disabled (wasting Actions minutes)\n"
        f"3. Schedule optimization: what should run more/less frequently\n"
        f"4. Revenue impact of fixing the top 3 broken workflows",
        max_tokens=600) or "API needed"
    
    save_output("Jordan Wells", "daily_ops", ops_plan, bottlenecks)
    save_to_repo(f"data/ops/jordan_{date.today()}.json",
        json.dumps({"bottlenecks": bottlenecks, "plan": ops_plan}, indent=2),
        f"jordan: ops report {date.today()}")
    push("Jordan Wells | Operations", f"Healthy: {bottlenecks['healthy']}/{bottlenecks['total_workflows']}\n{ops_plan[:200]}")
    log.info(f"\n{ops_plan}")
    return ops_plan


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
