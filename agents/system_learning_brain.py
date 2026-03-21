#!/usr/bin/env python3
"""System-Wide Learning Brain — NYSR Agency
Watches ALL departments. Every failure is data. Self-corrects automatically.
Runs weekly. Gets better every cycle.
"""
import os,sys,json,logging,requests,base64
from datetime import datetime,date,timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude,claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO,format="%(asctime)s [Brain] %(message)s")
log=logging.getLogger()
ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN=os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
REPO="nyspotlightreport/sct-agency-bots"
STRIPE=os.environ.get("STRIPE_SECRET_KEY","")
NTFY=os.environ.get("NTFY_CHANNEL","nysr-chairman-alerts-xk9")

BRAIN_SYSTEM="""You are the learning brain of the NYSR agency system.
Analyze performance data. Identify root causes. Generate precise fixes.
Every underperforming department gets a specific, actionable correction.
Data-driven. No vague suggestions. Results-focused."""

THRESHOLDS={
    "workflow_success_rate":80,"avg_quality_score":7.5,
    "sales_conversion_rate":1,"revenue_growth_pct":10
}

def get_all_workflow_stats()->dict:
    r=requests.get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100",headers=GH_H)
    runs=r.json().get("workflow_runs",[])
    stats={}
    for run in runs:
        n=run["name"]
        if n not in stats: stats[n]={"success":0,"fail":0,"skip":0}
        c=run.get("conclusion","")
        if c=="success": stats[n]["success"]+=1
        elif c=="failure": stats[n]["fail"]+=1
        else: stats[n]["skip"]+=1
    return stats

def get_revenue()->dict:
    rev={"total":0,"mrr":0,"last_7_days":0}
    if STRIPE:
        r=requests.get("https://api.stripe.com/v1/charges?limit=100",auth=(STRIPE,""),timeout=10)
        if r.status_code==200:
            charges=r.json().get("data",[])
            rev["total"]=sum(c["amount"] for c in charges if c.get("paid"))/100
        r2=requests.get("https://api.stripe.com/v1/subscriptions?status=active",auth=(STRIPE,""),timeout=10)
        if r2.status_code==200:
            rev["mrr"]=sum(s.get("plan",{}).get("amount",0) for s in r2.json().get("data",[]))/100
    return rev

def analyze_and_fix(stats:dict,rev:dict)->list:
    actions=[]
    # Failing workflows
    critical_fails=[n for n,s in stats.items() if s["fail"]>0 and s["success"]<=s["fail"]]
    for wf in critical_fails[:5]:
        if ANTHROPIC:
            fix=claude(BRAIN_SYSTEM,
                f"Workflow '{wf}' is failing more than succeeding. Diagnose and give one specific fix in 50 words.",
                max_tokens=80) or f"Re-trigger {wf} and check logs"
        else:
            fix=f"Review and re-trigger: {wf}"
        actions.append({"type":"workflow_fix","target":wf,"action":fix,"priority":"HIGH"})
    # Revenue = 0 with time passed
    if rev["total"]==0:
        if ANTHROPIC:
            fix=claude(BRAIN_SYSTEM,
                """Revenue is $0. Infrastructure is complete. What are the 3 most likely reasons we haven't closed
                a deal yet, and what are the 3 specific actions to take in the next 24 hours?
                Under 150 words. Be ruthlessly specific.""",max_tokens=200
            ) or "Activate cold email sequence, post on HN, run Reddit campaign"
        else:
            fix="Revenue $0: Activate cold email sequence immediately, post Show HN, post on r/entrepreneur"
        actions.append({"type":"revenue_action","action":fix,"priority":"CRITICAL"})
    return sorted(actions,key=lambda x:{"CRITICAL":0,"HIGH":1,"MEDIUM":2}.get(x["priority"],3))

def evolve_agents(actions:list):
    """If sales has 0 conversions, rewrite the sales approach entirely."""
    has_revenue_crisis=any(a["type"]=="revenue_action" for a in actions)
    if has_revenue_crisis and ANTHROPIC:
        new_approach=claude(BRAIN_SYSTEM,
            """Current sales approach: cold email with feature-led pitch.
Result: 0 conversions.

Rewrite the approach completely. What's the different strategy?
Think: where are the buyers? What do they actually respond to?
What format, channel, and message will get a YES in the next 7 days?
Be specific. Under 200 words.""",max_tokens=300)
        if new_approach:
            enc=base64.b64encode(new_approach.encode()).decode()
            r=requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/evolved_strategy.txt",headers=GH_H)
            body={"message":"brain: evolved sales strategy","content":enc}
            if r.status_code==200: body["sha"]=r.json()["sha"]
            requests.put(f"https://api.github.com/repos/{REPO}/contents/data/sales/evolved_strategy.txt",json=body,headers=GH_H)
            log.info("  ✅ Sales strategy evolved — saved to data/sales/evolved_strategy.txt")

def run():
    log.info("System Learning Brain — full scan...")
    stats=get_all_workflow_stats()
    rev=get_revenue()
    total_wfs=len(stats)
    passing=sum(1 for s in stats.values() if s["success"]>0 and s["fail"]<=s["success"])
    log.info(f"  Workflows: {passing}/{total_wfs} healthy")
    log.info(f"  Revenue: ${rev['total']:.2f} total | ${rev['mrr']:.2f} MRR")
    actions=analyze_and_fix(stats,rev)
    if actions:
        log.info(f"  Actions generated: {len(actions)}")
        for a in actions[:5]:
            log.info(f"  [{a['priority']}] {a['type']}: {str(a.get('action',''))[:60]}")
    evolve_agents(actions)
    # Save report
    report={"date":str(date.today()),"workflow_health":{"passing":passing,"total":total_wfs},
            "revenue":rev,"actions":actions[:10]}
    enc=base64.b64encode(json.dumps(report,indent=2).encode()).decode()
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/data/brain/weekly_report.json",headers=GH_H)
    body={"message":f"brain: report {date.today()}","content":enc}
    if r.status_code==200: body["sha"]=r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/data/brain/weekly_report.json",json=body,headers=GH_H)
    # Notify
    top_action=actions[0]["action"] if actions else "All systems healthy"
    requests.post(f"https://ntfy.sh/{NTFY}",
        json={"topic":NTFY,"title":f"NYSR Brain: {passing}/{total_wfs} WFs healthy | ${rev['total']:.0f} rev",
              "message":str(top_action)[:200],"priority":3,"tags":["brain"]},
        headers={"Content-Type":"application/json"},timeout=5)
    log.info("✅ System Learning Brain complete")

if __name__=="__main__": run()
