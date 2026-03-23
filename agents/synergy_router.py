#!/usr/bin/env python3
"""
agents/synergy_router.py — NYSR Cross-Department Synergy Router
The missing brain that connects all departments.
Reads every director's output → routes insights to relevant departments → triggers actions.
Omega Brain orchestration made real.
"""
import os, sys, json, logging, time
from datetime import datetime, timedelta
sys.path.insert(0, ".")
log = logging.getLogger("synergy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SYNERGY] %(message)s")
import urllib.request as urlreq, urllib.parse

SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
GH_PAT = os.environ.get("GH_PAT", "")

def push(t, m, p=0):
    if not PUSH_API: return
    try: urlreq.urlopen("https://api.pushover.net/1/messages.json", urllib.parse.urlencode({"token": PUSH_API, "user": PUSH_USER, "title": t[:100], "message": m[:1000], "priority": p}).encode(), timeout=5)
    except Exception:  # noqa: bare-except

        pass
def supa_get(table, query=""):
    if not SUPA_URL: return []
    try:
        req = urlreq.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"})
        with urlreq.urlopen(req, timeout=15) as r: return json.loads(r.read())
    except: return []

def gh_trigger(workflow):
    if not GH_PAT: return
    try:
        data = json.dumps({"ref": "main"}).encode()
        req = urlreq.Request(f"https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/workflows/{workflow}/dispatches",
            data=data, headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
        urlreq.urlopen(req, timeout=15)
        log.info(f"  TRIGGERED: {workflow}")
    except Exception:  # noqa: bare-except

        pass
# ═══ SYNERGY ROUTES ═══
# Each route defines: source director → action → target
ROUTES = [
    {"source": "Nina Caldwell", "keyword": "highest-ROI", "action": "Feed ROI analysis to Alex Mercer daily directive", "target_workflow": "nysr_autonomous_master.yml"},
    {"source": "Drew Sinclair", "keyword": "conversion", "action": "Feed analytics to Sloane Pierce prospecting", "target_workflow": "opportunity_discovery_daily.yml"},
    {"source": "Hayden Cross", "keyword": "grade", "action": "QC gate-check Cameron Reed content", "target_workflow": "cameron_daily.yml"},
    {"source": "Elliot Shaw", "keyword": "campaign", "action": "Feed campaign data to Drew Sinclair analytics", "target_workflow": "drew_daily.yml"},
    {"source": "Jeff Banks", "keyword": "close", "action": "Coordinate with Sloane Pierce on deal closure", "target_workflow": "jeff_banks_cro.yml"},
    {"source": "Ultra Watchdog", "keyword": "FAIL", "action": "Alert all agents and trigger repairs", "target_workflow": "guardian_self_healing.yml"},
    {"source": "Opportunity Discovery", "keyword": "outreach", "action": "Feed new leads to outreach engine", "target_workflow": None},
    {"source": "Security Scanner", "keyword": "CRITICAL", "action": "Alert Reese Morgan for engineering fix", "target_workflow": "engineering_build.yml"},
]

def run():
    log.info("="*60)
    log.info("SYNERGY ROUTER — Connecting all departments")
    log.info("="*60)
    # Get last 24h of director outputs
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    outputs = supa_get("director_outputs", f"?created_at=gt.{cutoff}&order=created_at.desc&limit=100")
    if not isinstance(outputs, list): outputs = []
    log.info(f"Found {len(outputs)} director outputs in last 24h")
    triggered = []
    for output in outputs:
        director = output.get("director", "")
        content = output.get("content", "")
        for route in ROUTES:
            if route["source"] in director and route["keyword"].lower() in content.lower():
                if route["target_workflow"]:
                    gh_trigger(route["target_workflow"])
                    triggered.append(f"{route['source']} → {route['action']}")
                    log.info(f"  SYNERGY: {route['source']} → {route['action']}")
    # Generate synthesis report
    directors_active = list(set(o.get("director", "") for o in outputs))
    report = f"Synergy Router: {len(outputs)} outputs from {len(directors_active)} directors, {len(triggered)} cross-department triggers"
    if triggered:
        report += "\nTriggers:\n" + "\n".join(f"  {t}" for t in triggered[:10])
    log.info(f"\n{report}")
    push("Synergy Router", report[:300], -1)
    return {"outputs_processed": len(outputs), "triggers": len(triggered), "directors_active": directors_active}

if __name__ == "__main__":
    run()
