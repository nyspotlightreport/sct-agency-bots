"""
Project Management Agent — Phase 2
Manages projects, tasks, milestones. Closes Jira/Confluence gap.
Auto-creates tasks from GitHub issues, tracks velocity, alerts on blockers.
MRR Unlock: $2k-5k/mo
"""
import os, json, logging, datetime
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PM] %(message)s")
log = logging.getLogger("project_mgmt")

SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN      = os.environ.get("GH_PAT", "")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")

import urllib.request, urllib.error

def supa(method: str, table: str, data: dict = None, query: str = "") -> Any:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supabase {method} {table}: {e.code} {e.read()[:200]}")
        return None

def push(title: str, message: str, priority: int = 0):
    if not PUSHOVER_API: return
    data = json.dumps({"token": PUSHOVER_API, "user": PUSHOVER_USER,
                        "title": title, "message": message, "priority": priority}).encode()
    try:
        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                                     data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except: pass

def ai(prompt: str) -> str:
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({
        "model": "claude-sonnet-4-20250514", "max_tokens": 800,
        "system": "You are a project management AI for NYSR Agency. Return only valid JSON when asked.",
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01"
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def create_project(name: str, description: str, priority: str = "high",
                   due_date: str = None, client_id: str = None) -> dict:
    project = supa("POST", "projects", {
        "name": name, "description": description,
        "priority": priority, "due_date": due_date,
        "client_id": client_id, "status": "active"
    })
    if project and isinstance(project, list):
        project = project[0]
        log.info(f"Created project: {name} [{project['id']}]")
        milestones_raw = ai(
            f"Generate 4 milestones for: {name}. Desc: {description}. "
            f"Return JSON array only: [{{\"title\":\"...\",\"description\":\"...\",\"weeks_from_now\":2,\"revenue_impact\":\"...\"}}]"
        )
        try:
            clean = milestones_raw.strip().lstrip("```json").lstrip("```").rstrip("```")
            milestones = json.loads(clean)
            today = datetime.date.today()
            for m in milestones:
                target = today + datetime.timedelta(weeks=int(m.get("weeks_from_now", 2)))
                supa("POST", "milestones", {
                    "project_id": project["id"],
                    "title": m.get("title","Milestone"),
                    "description": m.get("description", ""),
                    "target_date": str(target),
                    "revenue_impact": m.get("revenue_impact", "TBD")
                })
        except Exception as e:
            log.warning(f"Milestone gen failed: {e}")
    return project or {}

def sync_github_issues():
    if not GH_TOKEN: return
    try:
        url = "https://api.github.com/repos/nyspotlightreport/sct-agency-bots/issues?state=open&per_page=30"
        req = urllib.request.Request(url, headers={"Authorization": f"token {GH_TOKEN}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            issues = json.loads(r.read())
        projects = supa("GET", "projects", query="?name=eq.Agency%20Operations&select=id&limit=1") or []
        if not projects:
            p = create_project("Agency Operations", "Ongoing agency ops, bugs, feature requests", "high")
            proj_id = p.get("id")
        else:
            proj_id = projects[0]["id"]
        if not proj_id: return
        for issue in issues:
            existing = supa("GET", "tasks", query=f"?meta->>github_issue_id=eq.{issue['number']}&limit=1") or []
            if existing: continue
            labels = [l["name"] for l in issue.get("labels", [])]
            priority = "high" if any(l in labels for l in ["bug","critical","urgent"]) else "medium"
            supa("POST", "tasks", {
                "project_id": proj_id,
                "title": issue["title"],
                "description": (issue.get("body") or "")[:500],
                "status": "todo", "priority": priority,
                "meta": {"github_issue_id": issue["number"], "github_url": issue["html_url"]}
            })
            log.info(f"Synced GH issue #{issue['number']}: {issue['title'][:50]}")
    except Exception as e:
        log.warning(f"GitHub sync failed: {e}")

def daily_standup():
    today = datetime.date.today().isoformat()
    in_progress = supa("GET", "tasks", query="?status=eq.in_progress&select=title") or []
    blocked     = supa("GET", "tasks", query="?status=eq.blocked&select=title") or []
    due_today   = supa("GET", "tasks", query=f"?due_date=eq.{today}&status=neq.done&select=title") or []
    overdue     = supa("GET", "tasks", query=f"?due_date=lt.{today}&status=neq.done&select=title,due_date") or []
    active_proj = supa("GET", "projects", query="?status=eq.active&select=name") or []
    lines = [
        f"📊 PM Standup {today}",
        f"Projects Active: {len(active_proj)}",
        f"In Progress: {len(in_progress)}  Due Today: {len(due_today)}",
        f"Blocked: {len(blocked)}  Overdue: {len(overdue)}",
    ]
    if blocked:   lines.append("🚨 " + ", ".join(t["title"][:40] for t in blocked[:3]))
    if overdue:   lines.append("⚠️  " + ", ".join(t["title"][:40] for t in overdue[:3]))
    report = "\n".join(lines)
    log.info(report)
    if blocked or overdue:
        push("⚠️ NYSR PM Alert", f"Blocked:{len(blocked)} Overdue:{len(overdue)}", priority=1)
    else:
        push("📊 NYSR PM Standup", "\n".join(lines[1:]))
    return report

def auto_close_completed():
    tasks = supa("GET", "tasks", query="?status=eq.in_progress&select=id,title") or []
    now = datetime.datetime.utcnow().isoformat()
    for t in tasks:
        subtasks = supa("GET", "tasks", query=f"?parent_id=eq.{t['id']}&select=status") or []
        if subtasks and all(s["status"] == "done" for s in subtasks):
            supa("PATCH", "tasks", {"status": "done", "completed_at": now}, query=f"?id=eq.{t['id']}")
            log.info(f"Auto-closed: {t['title'][:50]}")

def seed_phase_projects():
    """Seed Phase 2 and Phase 3 as tracked projects on first run."""
    existing = supa("GET", "projects", query="?name=eq.Phase%202%20-%20Project%20Management&select=id&limit=1") or []
    if not existing:
        create_project("Phase 2 - Project Management", "Jira/Confluence replacement. $2k-5k MRR unlock.", "critical",
                        str(datetime.date.today() + datetime.timedelta(days=14)))
        create_project("Phase 3 - Shopify Storefront", "E-commerce storefront. 3-8x conversion lift.", "critical",
                        str(datetime.date.today() + datetime.timedelta(days=30)))
        log.info("Seeded Phase 2 + Phase 3 projects")

def run():
    log.info("=== Project Management Agent ===")
    seed_phase_projects()
    sync_github_issues()
    auto_close_completed()
    daily_standup()
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
