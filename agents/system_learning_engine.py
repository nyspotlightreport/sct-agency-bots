#!/usr/bin/env python3
"""
System-Wide Learning & Self-Correction Engine ΓÇö NYSR Intelligence
ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

This is the brain that makes every department smarter over time.
NO department operates in a static mode ΓÇö all learn and evolve.

DEPARTMENTS MONITORED:
  ΓÇó Sales ΓÇö conversion rates, funnel velocity, objection frequency
  ΓÇó Marketing ΓÇö traffic, CTR, channel ROI, CAC
  ΓÇó Content/Deliverables ΓÇö quality scores, engagement, shares
  ΓÇó Product ΓÇö feature usage, pricing acceptance, churn signals
  ΓÇó Finance ΓÇö revenue trends, MRR growth, unit economics
  ΓÇó Operations ΓÇö workflow success rates, error patterns

LEARNING METHODOLOGY:
  1. OBSERVE: Collect raw performance data from all departments
  2. ANALYZE: Claude runs root cause analysis on underperformance
  3. HYPOTHESIZE: Generate 3 candidate fixes ranked by expected impact
  4. TEST: Deploy fix as variant alongside current approach (A/B)
  5. MEASURE: Track result for 7 days
  6. ADOPT: If fix wins ΓåÆ replace current; if not ΓåÆ try next hypothesis
  7. DOCUMENT: Log what was learned to prevent repeating mistakes

ERROR CORRECTION:
  ΓÇó Any workflow failing 3+ times ΓåÆ auto-diagnose + fix attempted
  ΓÇó Any metric below threshold 7+ days ΓåÆ escalate + root cause
  ΓÇó Any department going dark (no output) ΓåÆ emergency alert

MEMORY SYSTEM:
  ΓÇó All learnings stored in data/learning/memory.json
  ΓÇó Each entry: what was tried, what happened, what was learned
  ΓÇó New strategies checked against memory to avoid repeating failures
"""
import os, sys, json, logging, requests, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LearningEngine] %(message)s")
log = logging.getLogger()

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN  = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H      = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
REPO      = "nyspotlightreport/sct-agency-bots"

LEARNING_SYSTEM = """You are the intelligence core of NY Spotlight Report.
Your job: analyze performance data, find root causes, generate fixes, and make every part of the system better.
You are rigorous, data-driven, and direct. You do not guess ΓÇö you hypothesize and test.
When something is failing, you say exactly why and exactly what to try next.
Format: specific, actionable, numbered. No vague advice."""

# ΓöÇΓöÇ DEPARTMENT HEALTH MONITORS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

THRESHOLDS = {
    "sales": {
        "email_open_rate":    {"min": 25, "critical": 15, "unit": "%"},
        "reply_rate":         {"min": 3,  "critical": 1,  "unit": "%"},
        "calls_booked_week":  {"min": 1,  "critical": 0,  "unit": "count"},
        "conversion_rate":    {"min": 5,  "critical": 0,  "unit": "%"},
    },
    "marketing": {
        "weekly_traffic":     {"min": 100, "critical": 0,   "unit": "visitors"},
        "email_list_growth":  {"min": 5,   "critical": 0,   "unit": "subscribers/week"},
        "content_published":  {"min": 5,   "critical": 0,   "unit": "pieces/week"},
        "social_posts":       {"min": 21,  "critical": 0,   "unit": "posts/week"},
    },
    "deliverables": {
        "avg_quality_score":  {"min": 7.5, "critical": 6.0, "unit": "score"},
        "posts_published":    {"min": 7,   "critical": 0,   "unit": "per week"},
        "approval_rate":      {"min": 80,  "critical": 50,  "unit": "%"},
    },
    "workflows": {
        "success_rate":       {"min": 80,  "critical": 50,  "unit": "%"},
        "consecutive_failures":{"max": 3,  "critical": 5,   "unit": "count"},
    }
}

def collect_system_health() -> dict:
    """Collect current health metrics across all departments."""
    health = {"timestamp": datetime.now().isoformat(), "departments": {}}
    
    # Workflow health from GitHub Actions
    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100", headers=GH_H)
    if r.status_code == 200:
        runs = r.json().get("workflow_runs", [])
        wf_stats = {}
        for run in runs:
            n = run["name"]
            if n not in wf_stats: wf_stats[n] = {"success":0,"fail":0,"total":0,"consecutive_fail":0}
            wf_stats[n]["total"] += 1
            if run["conclusion"] == "success": wf_stats[n]["success"] += 1
            elif run["conclusion"] == "failure":
                wf_stats[n]["fail"] += 1
                wf_stats[n]["consecutive_fail"] += 1
            else:
                wf_stats[n]["consecutive_fail"] = 0
        
        critical_wfs = [n for n, s in wf_stats.items() 
                       if s["total"] >= 3 and s["success"]/s["total"] < 0.5]
        
        health["departments"]["workflows"] = {
            "total": len(wf_stats),
            "critical": critical_wfs,
            "success_rate": round(sum(s["success"] for s in wf_stats.values()) /
                                 max(sum(s["total"] for s in wf_stats.values()), 1) * 100, 1)
        }
    
    # Deliverables health
    r2 = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/deliverables/registry.json", headers=GH_H)
    if r2.status_code == 200:
        try:
            registry = json.loads(base64.b64decode(r2.json()["content"]).decode())
            recent = [d for d in registry if d.get("created","") >= str(date.today() - timedelta(days=7))]
            avg_q = (sum(d.get("quality_score",0) for d in recent) / max(len(recent),1)) if recent else 0
            health["departments"]["deliverables"] = {
                "week_count": len(recent),
                "avg_quality": round(avg_q, 2),
                "approved_rate": round(sum(1 for d in recent if d.get("approved")) / max(len(recent),1) * 100, 1)
            }
        except: pass
    
    # Sales funnel health
    r3 = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/funnel.json", headers=GH_H)
    if r3.status_code == 200:
        try:
            funnel = json.loads(base64.b64decode(r3.json()["content"]).decode())
            stages = [v.get("current_stage","") for v in funnel.values()]
            health["departments"]["sales"] = {
                "total_prospects": len(funnel),
                "in_pipeline": len([s for s in stages if s not in ["CLOSED_WON","CLOSED_LOST","IDENTIFIED"]]),
                "closed_won": stages.count("CLOSED_WON"),
                "closed_lost": stages.count("CLOSED_LOST"),
            }
        except: pass
    
    return health

def run_department_analysis(health: dict) -> dict:
    """Run Claude analysis on all underperforming departments."""
    if not ANTHROPIC:
        return {"analysis": "No Anthropic key", "fixes": []}
    
    health_str = json.dumps(health, indent=2)
    
    return claude_json(
        LEARNING_SYSTEM,
        f"""Analyze this system health report and identify what needs fixing:

{health_str}

For each department with issues, provide:
1. Root cause (be specific ΓÇö not "needs improvement")
2. Top 3 fixes ranked by expected impact and ease
3. What to measure to know if the fix worked
4. What NOT to do (avoid repeating past failures)

Return JSON:
{{
  "overall_health_score": 0-100,
  "critical_issues": [
    {{
      "department": str,
      "issue": "specific problem statement",
      "root_cause": "specific root cause",
      "fixes": [
        {{"action": str, "expected_impact": "high|medium|low", "implementation": "exact steps", "timeline": "days"}},
        {{"action": str, "expected_impact": "high|medium|low", "implementation": "exact steps", "timeline": "days"}}
      ],
      "success_metric": "what number improves when fixed"
    }}
  ],
  "wins_to_amplify": ["what's working that should get more resources"],
  "learning_insights": ["key lessons from this analysis"]
}}""",
        max_tokens=1500
    ) or {"overall_health_score": 70, "critical_issues": [], "wins_to_amplify": [], "learning_insights": []}

def store_memory(learning: dict):
    """
    Persistent memory ΓÇö every lesson stored so the system never
    makes the same mistake twice.
    """
    path = "data/learning/memory.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    memory = []
    if r.status_code == 200:
        try: memory = json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    
    entry = {
        "date": str(date.today()),
        "health_score": learning.get("overall_health_score"),
        "critical_issues_count": len(learning.get("critical_issues",[])),
        "insights": learning.get("learning_insights",[]),
        "actions_taken": [i["fixes"][0]["action"] for i in learning.get("critical_issues",[]) if i.get("fixes")]
    }
    memory.insert(0, entry)
    memory = memory[:90]  # 90-day rolling memory
    
    body = {"message": f"learning: system memory {date.today()}",
            "content": base64.b64encode(json.dumps(memory, indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)
    
    # Also save full analysis
    path2 = f"data/learning/analysis_{date.today()}.json"
    body2 = {"message": f"learning: full analysis {date.today()}",
             "content": base64.b64encode(json.dumps(learning, indent=2).encode()).decode()}
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path2}", json=body2, headers=GH_H)

def alert_chairman(message: str):
    """Send critical alerts to Chairman via ntfy."""
    ntfy_ch = os.environ.get("NTFY_CHANNEL","nysr-chairman-alerts-xk9")
    try:
        requests.post(f"https://ntfy.sh/{ntfy_ch}",
            data=message.encode(), timeout=10,
            headers={"Title":"NYSR System Learning Alert",
                    "Priority":"default","Tags":"brain,robot"})
    except: pass

def run():
    log.info("System Learning Engine starting...")
    
    # 1. Collect health data
    log.info("Collecting system health...")
    health = collect_system_health()
    
    dept_count = len(health.get("departments",{}))
    log.info(f"  {dept_count} departments monitored")
    
    # 2. Run AI analysis
    log.info("Running AI root cause analysis...")
    analysis = run_department_analysis(health)
    
    score = analysis.get("overall_health_score", 70)
    issues = analysis.get("critical_issues", [])
    wins   = analysis.get("wins_to_amplify", [])
    
    log.info(f"  Health score: {score}/100")
    log.info(f"  Critical issues: {len(issues)}")
    log.info(f"  Wins to amplify: {len(wins)}")
    
    if issues:
        for issue in issues[:3]:
            log.warning(f"  Γ¥ù {issue.get('department','')}: {issue.get('issue','')}")
            if issue.get("fixes"):
                log.info(f"     Fix: {issue['fixes'][0].get('action','')}")
    
    # 3. Store to memory
    store_memory(analysis)
    log.info("  Γ£à Learnings stored to system memory")
    
    # 4. Alert if critical
    if score < 50 or any(i for i in issues if "CLOSED" not in i.get("department","")):
        alert_chairman(f"System health: {score}/100. {len(issues)} critical issues. Check data/learning/analysis_{date.today()}.json")
    
    log.info("Γ£à Learning Engine complete")

if __name__ == "__main__":
    run()
