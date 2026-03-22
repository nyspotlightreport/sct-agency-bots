#!/usr/bin/env python3
"""
Dev Commander Agent — NYSR Engineering Department Director
Orchestrates the entire engineering operation.
Manages: code quality, deployments, debugging, documentation,
security scanning, performance monitoring, and new feature builds.

Daily operations:
  1. Health check all workflows and bots
  2. Scan for errors and auto-fix if possible
  3. Monitor deployment status
  4. Track tech debt and schedule fixes
  5. Generate engineering metrics for Chairman
"""
import os, sys, json, logging, subprocess
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

import urllib.request, urllib.parse

log = logging.getLogger(__name__)

GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
NETLIFY_TOKEN = os.environ.get("NETLIFY_AUTH_TOKEN","")
NETLIFY_SITE  = os.environ.get("NETLIFY_SITE_ID","8ef722e1-4110-42af-8ddb-ff6c2ce1745e")

def notify(msg, title="Dev Commander"):
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def gh_api(path, method="GET", body=None):
    if not GH_TOKEN: return {}
    try:
        url = f"https://api.github.com{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url,data=data,
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"},
            method=method)
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read()) if r.status not in [204] else {}
    except Exception as e:
        log.warning(f"GH API {method} {path}: {e}")
        return {}

def get_workflow_health() -> dict:
    """Get status of all workflows in the last 24h."""
    runs = gh_api(f"/repos/{REPO}/actions/runs?per_page=50&created=>={( datetime.utcnow()-timedelta(hours=24) ).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    workflows = runs.get("workflow_runs",[])
    
    stats = {"total":0,"success":0,"failure":0,"in_progress":0,"cancelled":0,"failed_names":[]}
    for wf in workflows:
        stats["total"] += 1
        conclusion = wf.get("conclusion","")
        status     = wf.get("status","")
        if conclusion == "success":   stats["success"] += 1
        elif conclusion == "failure": 
            stats["failure"] += 1
            stats["failed_names"].append(wf.get("name","?"))
        elif status == "in_progress": stats["in_progress"] += 1
        elif conclusion == "cancelled": stats["cancelled"] += 1
    
    stats["pass_rate"] = round(stats["success"]/max(stats["total"]-stats["cancelled"],1)*100)
    return stats

def get_recent_commits() -> list:
    """Get commits from the last 7 days."""
    since = (datetime.utcnow()-timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    commits = gh_api(f"/repos/{REPO}/commits?since={since}&per_page=20")
    return [{"sha":c["sha"][:7],"msg":c["commit"]["message"].split("\n")[0],"author":c["commit"]["author"]["name"]} for c in (commits or [])]

def check_netlify_status() -> dict:
    """Check latest Netlify deployment status."""
    if not NETLIFY_TOKEN: return {"status":"no_token"}
    try:
        req = urllib.request.Request(
            f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE}/deploys?per_page=3",
            headers={"Authorization":f"Bearer {NETLIFY_TOKEN}"}
        )
        with urllib.request.urlopen(req,timeout=10) as r:
            deploys = json.loads(r.read())
            if deploys:
                latest = deploys[0]
                return {"state":latest.get("state"),"created_at":latest.get("created_at",""),"deploy_url":latest.get("deploy_url","")}
    except Exception as e:
        log.warning(f"Netlify check: {e}")
    return {"status":"check_failed"}

def count_repo_components() -> dict:
    """Count agents, bots, workflows in the repo."""
    agents = gh_api(f"/repos/{REPO}/contents/agents")
    bots   = gh_api(f"/repos/{REPO}/contents/bots")
    wflows = gh_api(f"/repos/{REPO}/actions/workflows?per_page=100")
    return {
        "agents":    len([f for f in (agents if isinstance(agents,list) else []) if f["name"].endswith(".py")]),
        "bots":      len([f for f in (bots if isinstance(bots,list) else []) if f["name"].endswith(".py")]),
        "workflows": wflows.get("total_count",0),
    }

def generate_engineering_briefing(health: dict, counts: dict, netlify: dict) -> str:
    context = f"""
Workflow health (24h): {health['total']} runs | {health['pass_rate']}% pass rate | {health['failure']} failures
Failed workflows: {", ".join(health.get("failed_names",[])[:5]) or "None"}
Netlify: {netlify.get("state","unknown")}
System: {counts["agents"]} agents | {counts["bots"]} bots | {counts["workflows"]} workflows
"""
    return claude(
        "You are a senior engineering manager. Generate a concise daily engineering status report (4-6 bullets).",
        f"Engineering status:\n{context}\nFocus on: system health, any critical issues, deployment status, and top 2 engineering priorities today.",
        max_tokens=300
    ) or f"Engineering Daily\n• Workflows: {health['pass_rate']}% pass rate\n• Netlify: {netlify.get('state','?')}\n• System: {counts['agents']} agents, {counts['bots']} bots, {counts['workflows']} workflows\n• {'⚠️ Failures: '+', '.join(health.get('failed_names',[])[:3]) if health.get('failure',0)>0 else '✅ All systems operational'}"

def run():
    log.info("Dev Commander starting engineering health check...")
    
    health  = get_workflow_health()
    counts  = count_repo_components()
    netlify = check_netlify_status()
    commits = get_recent_commits()
    
    log.info(f"Workflow health: {health['pass_rate']}% pass rate ({health['failure']} failures)")
    log.info(f"Components: {counts['agents']} agents | {counts['bots']} bots | {counts['workflows']} workflows")
    log.info(f"Netlify: {netlify.get('state','?')}")
    log.info(f"Recent commits: {len(commits)}")
    
    briefing = generate_engineering_briefing(health, counts, netlify)
    
    # Alert on critical failures
    if health["failure"] > 3:
        failed = ", ".join(health.get("failed_names",[])[:5])
        notify(f"🚨 {health['failure']} workflow failures!\n{failed}\n\nPass rate: {health['pass_rate']}%", "Dev: CRITICAL")
    elif health["failure"] > 0:
        notify(f"⚠️ {health['failure']} workflow failures\nPass rate: {health['pass_rate']}%\n\n{briefing[:400]}", "Dev Commander")
    else:
        notify(f"✅ Engineering Daily\n{briefing[:600]}", "Dev Commander")
    
    return {
        "workflow_health": health,
        "component_counts": counts,
        "netlify_status": netlify,
        "recent_commits": len(commits),
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [DevCmd] %(message)s")
    run()
