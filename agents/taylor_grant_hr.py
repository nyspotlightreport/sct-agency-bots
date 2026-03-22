#!/usr/bin/env python3
"""
Taylor Grant ΓÇö HR / Workforce Director\nAgentic Super-intelligence for AI workforce management.\nAutonomous: Audit agent/bot performance ΓåÆ Track output per agent ΓåÆ Identify underperformers ΓåÆ Recommend scaling
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

log = logging.getLogger("taylor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [TAYLOR] %(message)s")

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

SYSTEM = """You are Taylor Grant, HR Director. Agentic Super-intelligence. Mental models: Grove high-output management, Kim radical candor, Drucker knowledge worker. In an AI-first company, every agent must justify its existence with output.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


def audit_workforce():
    """Count and categorize the entire AI workforce."""
    agents_dir = gh("contents/agents") or []
    bots_dir = gh("contents/bots") or []
    wf_dir = gh("actions/workflows?per_page=200") or {}
    
    agent_count = len([f for f in (agents_dir if isinstance(agents_dir, list) else []) if isinstance(f,dict) and f.get("name","").endswith(".py")])
    bot_count = len([f for f in (bots_dir if isinstance(bots_dir, list) else []) if isinstance(f,dict) and f.get("name","").endswith(".py")])
    wf_count = wf_dir.get("total_count", 0) if isinstance(wf_dir, dict) else 0
    
    # Check recent activity
    runs = gh("actions/runs?per_page=100") or {}
    active_wfs = set()
    for r in runs.get("workflow_runs", []):
        active_wfs.add(r.get("name",""))
    
    return {"agents": agent_count, "bots": bot_count, "workflows": wf_count,
            "active_workflows_24h": len(active_wfs), "dormant_estimate": max(0, wf_count - len(active_wfs))}

def run():
    log.info("TAYLOR GRANT ΓÇö HR Director ΓÇö Activating")
    workforce = audit_workforce()
    log.info(f"Workforce: {workforce['agents']} agents, {workforce['bots']} bots, {workforce['workflows']} workflows")
    
    report = claude(SYSTEM,
        f"AI WORKFORCE INTELLIGENCE\n{json.dumps(workforce)}\n\n"
        f"Deliver:\n1. Workforce efficiency score (output per agent)\n"
        f"2. Which agents/bots should be retired (no output, wasting Actions minutes)\n"
        f"3. Which departments are understaffed (need more bots)\n"
        f"4. Scaling plan: what to add for Phase 2\n"
        f"5. Prompt optimization opportunities (which agents have weak prompts)",
        max_tokens=600) or "API needed"
    
    save_output("Taylor Grant", "daily_hr", report, workforce)
    push("Taylor Grant | HR", f"Agents:{workforce['agents']} Bots:{workforce['bots']} Active:{workforce['active_workflows_24h']}\n{report[:200]}")
    log.info(f"\n{report}")
    return report



# ΓòÉΓòÉΓòÉ SUPERCORE PARALLELISM WIRING ΓòÉΓòÉΓòÉ
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="taylor_grant"
        DIRECTOR_NAME="Taylor Grant"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['grove_high_output', 'radical_candor', 'right_people_bus', 'ai_workforce_opt']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['grove_high_output', 'radical_candor', 'right_people_bus', 'ai_workforce_opt'],chain_steps=2,rank_criteria="workforce_roi")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
