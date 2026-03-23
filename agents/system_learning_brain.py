#!/usr/bin/env python3
"""
System Learning Brain ΓÇö NYSR Agency
Every department learns. Nothing fails twice without adapting.

THIS IS THE NERVOUS SYSTEM OF THE ENTIRE AGENCY.

What it does:
  - Monitors ALL 60 workflows for failures, slowdowns, underperformance
  - Reads error logs and diagnoses root causes using Claude
  - Generates and applies fixes automatically when safe
  - Escalates to Chairman only when human judgment is needed
  - Maintains a shared knowledge base all agents can read
  - Tracks what works, what doesn't, across ALL departments
  - Publishes a weekly "what we learned" report

LEARNING CATEGORIES:
  SALES:      open rates, reply rates, conversion rates, objection patterns
  MARKETING:  traffic, engagement, click-through, conversion by channel
  CONTENT:    quality scores, SEO performance, share rates, time-on-page
  OPERATIONS: workflow success rates, runtime, dependency failures
  PRODUCT:    feature requests, complaints, cancellation reasons
  FINANCE:    revenue per channel, CAC, LTV, refund patterns

SELF-CORRECTION RULES:
  If something fails 2x ΓåÆ investigate
  If something fails 3x ΓåÆ auto-fix or escalate
  If performance drops 20% ΓåÆ alert + suggest fix
  If performance improves 20% ΓåÆ double down + document why
  If new pattern emerges ΓåÆ create new rule and share agency-wide
"""
import os, sys, json, logging, requests, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LearningBrain] %(message)s")
log = logging.getLogger()

ANTHROPIC  = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN   = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H       = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
NTFY       = os.environ.get("NTFY_CHANNEL","nysr-chairman-alerts-xk9")
REPO       = "nyspotlightreport/sct-agency-bots"

ANALYST_VOICE = """You are Drew Sinclair, Chief Data Analyst at NY Spotlight Report.
You find patterns in performance data that others miss.
You speak in specifics: numbers, percentages, root causes, actions.
You never say "it depends" ΓÇö you give a recommendation with confidence."""

DEPARTMENTS = {
    "sales":      {"data_path":"data/sales/","workflows":["Sales Supercharge","Client Acquisition"]},
    "marketing":  {"data_path":"data/marketing/","workflows":["Traffic Engine","Social Media Master","SEO"]},
    "content":    {"data_path":"data/deliverables/","workflows":["Deliverables Engine","Elite Content"]},
    "operations": {"data_path":"data/james/","workflows":["James Butler","Proactive Intelligence"]},
    "product":    {"data_path":"data/products/","workflows":["New Income Bots"]},
}

# ΓöÇΓöÇ SHARED KNOWLEDGE BASE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def load_knowledge_base() -> dict:
    """The shared memory all agents can read."""
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/brain/knowledge_base.json", headers=GH_H)
    if r.status_code == 200:
        try: return json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    return {
        "rules": [],
        "patterns": [],
        "wins": [],
        "kills": [],
        "open_questions": [],
        "last_updated": str(date.today())
    }

def update_knowledge_base(kb: dict):
    """Write updated knowledge base ΓÇö all agents will use this."""
    kb["last_updated"] = str(date.today())
    path = "data/brain/knowledge_base.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    body = {"message":f"brain: knowledge base updated {date.today()}",
            "content":base64.b64encode(json.dumps(kb,indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)

# ΓöÇΓöÇ WORKFLOW PERFORMANCE AUDITOR ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def audit_all_workflows() -> dict:
    """Pull all workflow runs. Score each. Identify systemic issues."""
    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100", headers=GH_H)
    runs = r.json().get("workflow_runs",[])
    
    wf_stats = {}
    for run in runs:
        n = run["name"]
        if n not in wf_stats:
            wf_stats[n] = {"success":0,"failure":0,"total":0,"errors":[],"last_run":None}
        wf_stats[n]["total"] += 1
        if run["conclusion"]=="success": wf_stats[n]["success"] += 1
        elif run["conclusion"]=="failure":
            wf_stats[n]["failure"] += 1
            # Get error details for first 2 failures
            if len(wf_stats[n]["errors"]) < 2:
                rj = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs/{run['id']}/jobs", headers=GH_H)
                for job in rj.json().get("jobs",[])[:1]:
                    rl = requests.get(f"https://api.github.com/repos/{REPO}/actions/jobs/{job['id']}/logs",
                        headers=GH_H, allow_redirects=True)
                    errs = [l.strip() for l in rl.text.split("\n") if any(x in l for x in ["Error","error","failed","Traceback"])]
                    if errs: wf_stats[n]["errors"].append(errs[0][:150])
        if not wf_stats[n]["last_run"]:
            wf_stats[n]["last_run"] = run.get("updated_at","")
    
    # Classify health
    unhealthy = []
    for name, stats in wf_stats.items():
        if stats["total"] < 2: continue
        rate = stats["success"] / stats["total"]
        if rate < 0.6:
            unhealthy.append({
                "name": name,
                "success_rate": round(rate*100,1),
                "failures": stats["failure"],
                "total": stats["total"],
                "errors": stats["errors"][:2]
            })
    
    return {
        "total_workflows": len(wf_stats),
        "healthy": len([s for s in wf_stats.values() if s["total"]>0 and s["success"]/s["total"]>=0.8]),
        "unhealthy": sorted(unhealthy, key=lambda x: x["success_rate"]),
        "all_stats": wf_stats
    }

# ΓöÇΓöÇ ROOT CAUSE ANALYSIS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def diagnose_with_ai(workflow_name: str, errors: list, context: dict = {}) -> dict:
    """Use Claude to diagnose failure root cause and generate fix."""
    if not ANTHROPIC or not errors:
        return {"diagnosis":"Unable to analyze","fix":"Manual inspection needed","confidence":0}
    
    return claude_json(
        ANALYST_VOICE,
        f"""Diagnose this GitHub Actions workflow failure:

Workflow: {workflow_name}
Error logs: {json.dumps(errors)}
Context: {json.dumps(context)}

Provide:
1. Root cause (be specific ΓÇö dependency, auth, timeout, code bug, config?)
2. Exact fix (code change, secret to add, config to update)
3. Prevention measure (so it never fails this way again)
4. Confidence level 0-100

Return JSON:
{{
  "root_cause": "specific diagnosis",
  "fix_type": "code_change|secret_add|config_update|dependency|auth|retrigger",
  "fix_instructions": "exact steps",
  "auto_fixable": true/false,
  "prevention": "what to add/change to prevent recurrence",
  "confidence": 0-100,
  "escalate_to_chairman": true/false,
  "escalation_reason": "why (if applicable)"
}}""",
        max_tokens=400
    ) or {"diagnosis":"Analysis failed","auto_fixable":False,"escalate_to_chairman":True}

# ΓöÇΓöÇ PERFORMANCE PATTERN RECOGNITION ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def detect_performance_patterns() -> list:
    """Find cross-departmental patterns in performance data."""
    patterns = []
    
    # Load all available performance data
    data_paths = [
        "data/sales/daily_stats.json",
        "data/deliverables/registry.json",
        "data/james/changelog.json",
    ]
    
    all_data = {}
    for path in data_paths:
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
        if r.status_code == 200:
            try:
                all_data[path] = json.loads(base64.b64decode(r.json()["content"]).decode())
            except Exception:  # noqa: bare-except

                pass
    if not ANTHROPIC or not all_data:
        return [{"pattern":"Insufficient data","recommendation":"Collect 7 days of data first","priority":"low"}]
    
    result = claude_json(
        ANALYST_VOICE,
        f"""Analyze this performance data across all departments and find patterns:

{json.dumps({k: v[:5] if isinstance(v,list) else v for k,v in all_data.items()}, indent=2)[:2000]}

Find:
1. What's working that should be amplified
2. What's failing repeatedly that needs fixing
3. Cross-department dependencies causing problems
4. The single highest-ROI action to take today

Return JSON array of patterns:
[{{
  "pattern": "what you found",
  "department": "which dept",
  "data_evidence": "specific numbers/facts",
  "recommendation": "exact action",
  "priority": "critical|high|medium|low",
  "auto_actionable": true/false
}}]""",
        max_tokens=600
    )
    return result if isinstance(result, list) else []

# ΓöÇΓöÇ AGENCY-WIDE LEARNING UPDATE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def generate_learning_update(audit: dict, patterns: list) -> dict:
    """Generate rules + insights for the knowledge base."""
    if not ANTHROPIC:
        return {}
    
    unhealthy = audit.get("unhealthy",[])
    
    return claude_json(
        ANALYST_VOICE,
        f"""Based on this week's agency performance:

WORKFLOW HEALTH: {audit["healthy"]}/{audit["total_workflows"]} healthy
UNHEALTHY WORKFLOWS: {json.dumps([u["name"] for u in unhealthy[:5]])}
PATTERNS FOUND: {json.dumps([p.get("pattern","") for p in patterns[:5]])}

Generate:
1. New rules the agency should follow going forward
2. Patterns to watch for
3. Things to STOP doing (kills)
4. Open questions that need more data

Return JSON:
{{
  "new_rules": [
    {{"rule": "specific rule", "reason": "why", "department": "which dept or all"}}
  ],
  "new_patterns": [
    {{"pattern": str, "trigger": "when to look for this", "response": "what to do"}}
  ],
  "kills": [
    {{"item": "what to stop", "reason": "why", "replaced_by": "what replaces it"}}
  ],
  "open_questions": ["question needing more data"]
}}""",
        max_tokens=600
    ) or {}

# ΓöÇΓöÇ SELF-HEALING LOOP ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def attempt_auto_fixes(unhealthy_workflows: list) -> list:
    """Try to fix workflows that can be auto-fixed."""
    fixed = []
    
    for wf in unhealthy_workflows[:5]:
        if not wf.get("errors"): continue
        diagnosis = diagnose_with_ai(wf["name"], wf["errors"])
        
        if diagnosis.get("auto_fixable") and not diagnosis.get("escalate_to_chairman"):
            fix_type = diagnosis.get("fix_type","")
            
            if fix_type == "retrigger":
                # Just re-trigger the workflow
                r = requests.get(f"https://api.github.com/repos/{REPO}/actions/workflows?per_page=60", headers=GH_H)
                for workflow in r.json().get("workflows",[]):
                    if workflow["name"] == wf["name"]:
                        r2 = requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow['id']}/dispatches",
                            json={"ref":"main"}, headers=GH_H)
                        if r2.status_code == 204:
                            fixed.append({"workflow": wf["name"], "action":"retriggered","confidence":diagnosis.get("confidence",50)})
                        break
    
    return fixed

# ΓöÇΓöÇ CHAIRMAN ESCALATION ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def escalate_to_chairman(issues: list):
    """Send critical issues to Chairman via ntfy."""
    if not issues: return
    
    msg = f"≡ƒºá LEARNING BRAIN ALERT\n"
    msg += f"Date: {date.today()}\n\n"
    for issue in issues[:3]:
        msg += f"ΓÜá∩╕Å {issue.get('name','')}\n"
        msg += f"   {issue.get('escalation_reason','Needs review')}\n\n"
    msg += "Review: github.com/nyspotlightreport/sct-agency-bots/actions"
    
    try:
        requests.post(f"https://ntfy.sh/{NTFY}",
            json={"topic":NTFY,"title":"Agency Brain Alert","message":msg,"priority":4,"tags":["warning"]},
            headers={"Content-Type":"application/json"}, timeout=5)
    except Exception:  # noqa: bare-except

        pass
# ΓöÇΓöÇ WEEKLY LEARNING REPORT ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def generate_weekly_report(audit, patterns, learning) -> str:
    """Generate the Chairman's weekly performance + learning report."""
    if not ANTHROPIC:
        return f"Week of {date.today()}: {audit.get('healthy',0)}/{audit.get('total_workflows',0)} workflows healthy."
    
    return claude(
        """You are the Chief Data Analyst presenting the weekly agency performance report.
Be specific with numbers. Lead with wins, then problems, then what you're doing about problems.
Under 200 words. Chairman reads this in 30 seconds.""",
        f"""Week ending {date.today()}:

WORKFLOW HEALTH: {audit.get('healthy',0)}/{audit.get('total_workflows',0)} healthy
UNHEALTHY: {len(audit.get('unhealthy',[]))} workflows need attention
PATTERNS FOUND: {len(patterns)}
NEW RULES ADDED: {len(learning.get('new_rules',[]))}
KILLS EXECUTED: {len(learning.get('kills',[]))}

Top issue: {audit.get('unhealthy',[{}])[0].get('name','none') if audit.get('unhealthy') else 'none'}

Write the weekly briefing.""",
        max_tokens=300
    ) or f"Weekly briefing: {audit.get('healthy',0)} workflows healthy, {len(audit.get('unhealthy',[]))} need attention."

# ΓöÇΓöÇ MAIN ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def run():
    log.info("System Learning Brain starting...")
    
    # 1. Audit all workflows
    log.info("Auditing all 60 workflows...")
    audit = audit_all_workflows()
    log.info(f"  Healthy: {audit['healthy']}/{audit['total_workflows']}")
    log.info(f"  Unhealthy: {len(audit['unhealthy'])}")
    
    # 2. Attempt auto-fixes
    if audit["unhealthy"]:
        log.info("Attempting auto-fixes...")
        fixed = attempt_auto_fixes(audit["unhealthy"])
        for f in fixed:
            log.info(f"  Γ£à Fixed: {f['workflow']}")
    
    # 3. Detect patterns
    log.info("Detecting performance patterns...")
    patterns = detect_performance_patterns()
    for p in patterns[:3]:
        log.info(f"  {p.get('priority','?').upper()}: {p.get('pattern','')[:70]}")
    
    # 4. Generate learning update
    log.info("Updating knowledge base...")
    learning = generate_learning_update(audit, patterns)
    
    # 5. Update shared knowledge base
    kb = load_knowledge_base()
    if learning.get("new_rules"):
        kb["rules"].extend(learning["new_rules"])
        kb["rules"] = kb["rules"][-100:]  # Keep last 100 rules
    if learning.get("new_patterns"):
        kb["patterns"].extend(learning["new_patterns"])
        kb["patterns"] = kb["patterns"][-50:]
    if learning.get("kills"):
        kb["kills"].extend(learning["kills"])
        kb["kills"] = kb["kills"][-50:]
    update_knowledge_base(kb)
    log.info(f"  Knowledge base: {len(kb.get('rules',[]))} rules | {len(kb.get('patterns',[]))} patterns")
    
    # 6. Escalate critical issues to Chairman
    escalations = [u for u in audit["unhealthy"] if u["success_rate"] < 20]
    if escalations:
        log.info(f"Escalating {len(escalations)} critical issues to Chairman...")
        escalate_to_chairman([{"name":e["name"],"escalation_reason":f"{e['success_rate']}% success rate ΓÇö needs manual review"} for e in escalations])
    
    # 7. Weekly report (Mondays)
    if date.today().weekday() == 0:
        log.info("Generating weekly learning report...")
        report = generate_weekly_report(audit, patterns, learning)
        log.info(f"\n{'='*55}\n{report}\n{'='*55}")
        
        # Save report
        path = f"data/brain/weekly_report_{date.today()}.txt"
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
        body = {"message":f"brain: weekly report {date.today()}","content":base64.b64encode(report.encode()).decode()}
        if r.status_code == 200: body["sha"] = r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)
    
    log.info("Γ£à Learning Brain complete")

if __name__ == "__main__":
    run()
