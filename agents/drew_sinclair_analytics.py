#!/usr/bin/env python3
"""
Drew Sinclair — Analytics Director\nAgentic Super-intelligence for data intelligence.\nAutonomous: Pull all metrics → Compare forecasts vs actuals → Identify winning patterns → Generate insights
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

log = logging.getLogger("drew")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DREW] %(message)s")

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

SYSTEM = """You are Drew Sinclair, Analytics Director. Agentic Super-intelligence. Mental models: Kahneman System 1/2, Taleb black swan detection, Pareto distribution. Data without action is trivia. Every metric points to a decision.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


def gather_all_metrics():
    """Pull metrics from every available source."""
    metrics = {"date": str(date.today()), "sources": []}
    # Workflow performance
    runs = gh("actions/runs?per_page=50") or {}
    wf_runs = runs.get("workflow_runs", [])
    success = len([r for r in wf_runs if r.get("conclusion")=="success"])
    failure = len([r for r in wf_runs if r.get("conclusion")=="failure"])
    metrics["workflows"] = {"success": success, "failure": failure, "total": len(wf_runs),
        "success_rate": round(success/max(len(wf_runs),1)*100)}
    metrics["sources"].append("github_actions")
    
    # Contact metrics
    contacts = supa("GET", "contacts", query="?select=stage,score,created_at") or []
    if isinstance(contacts, list):
        metrics["contacts"] = {"total": len(contacts),
            "by_stage": {}, "avg_score": round(sum(c.get("score",0) for c in contacts if isinstance(c,dict))/max(len(contacts),1))}
        for c in contacts:
            if isinstance(c, dict):
                stage = c.get("stage","unknown")
                metrics["contacts"]["by_stage"][stage] = metrics["contacts"]["by_stage"].get(stage, 0) + 1
        metrics["sources"].append("supabase_contacts")
    
    # Director outputs
    outputs = supa("GET", "director_outputs", query=f"?created_at=gte.{date.today()}T00:00:00&select=director,output_type") or []
    metrics["director_activity"] = len(outputs) if isinstance(outputs, list) else 0
    
    return metrics

def run():
    log.info("DREW SINCLAIR — Analytics Director — Activating")
    metrics = gather_all_metrics()
    log.info(f"Metrics gathered from {len(metrics.get('sources',[]))} sources")
    
    insights = claude(SYSTEM,
        f"DAILY ANALYTICS INTELLIGENCE\nMetrics: {json.dumps(metrics, indent=2)}\n\n"
        f"Deliver:\n1. Top insight from today's data (what changed, what matters)\n"
        f"2. Prediction: what will happen in the next 7 days based on trends\n"
        f"3. Anomaly detection: anything unusual in the data\n"
        f"4. Revenue attribution: which activities are closest to producing revenue\n"
        f"5. Recommended A/B test based on current data",
        max_tokens=600) or "API needed"
    
    save_output("Drew Sinclair", "daily_analytics", insights, metrics)
    save_to_repo(f"data/analytics/drew_{date.today()}.json",
        json.dumps({"metrics": metrics, "insights": insights}, indent=2),
        f"drew: analytics {date.today()}")
    push("Drew Sinclair | Analytics", insights[:300])
    log.info(f"\n{insights}")
    return insights



# ═══ SUPERCORE PARALLELISM WIRING ═══
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="drew_sinclair"
        DIRECTOR_NAME="Drew Sinclair"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['pareto_80_20', 'cohort_analysis', 'bayesian_updating', 'causal_inference']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['pareto_80_20', 'cohort_analysis', 'bayesian_updating', 'causal_inference'],chain_steps=3,rank_criteria="decision_quality")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
