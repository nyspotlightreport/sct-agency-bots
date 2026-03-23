#!/usr/bin/env python3
"""
Hayden Cross ΓÇö Quality Control Director\nAgentic Super-intelligence for output excellence.\nAutonomous: Grade all director outputs ΓåÆ Block low-quality content ΓåÆ Enforce standards ΓåÆ Track quality trends
"""
from agents.supercore import SuperDirector,pushover as super_push
import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

log = logging.getLogger("hayden")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [HAYDEN] %(message)s")

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
    except Exception:  # noqa: bare-except

        pass
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

SYSTEM = """You are Hayden Cross, QC Director. Agentic Super-intelligence. Mental models: Deming total quality, Six Sigma DMAIC, Crosby zero defects, Jobs quality bar. Nothing ships below B+. Revenue-facing items require A. You report directly to Chairman. Your standards are absolute.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


def audit_recent_outputs():
    """Pull and grade all recent director outputs."""
    outputs = supa("GET", "director_outputs",
        query=f"?created_at=gte.{(date.today()-timedelta(days=1))}T00:00:00&select=director,output_type,content,created_at&order=created_at.desc&limit=20") or []
    return outputs if isinstance(outputs, list) else []

def grade_output(director, content):
    """Use Claude to grade a director's output."""
    return claude_json(SYSTEM,
        f"Grade this director output from {director}.\n\nContent:\n{content[:1500]}\n\n"
        f"Return JSON: {{\"grade\": \"A+/A/A-/B+/B/B-/C+/C/D/F\", "
        f"\"score\": 0-100, \"strengths\": [\"...\"], "
        f"\"weaknesses\": [\"...\"], \"actionable\": true/false, "
        f"\"has_specific_numbers\": true/false, \"has_revenue_link\": true/false, "
        f"\"recommendation\": \"one sentence improvement\"}}",
        max_tokens=400) or {"grade": "N/A", "score": 0}

def run():
    log.info("HAYDEN CROSS ΓÇö Quality Control Director ΓÇö Activating")
    outputs = audit_recent_outputs()
    log.info(f"Outputs to review: {len(outputs)}")
    
    grades = []
    for output in outputs[:10]:
        if not isinstance(output, dict): continue
        grade = grade_output(output.get("director",""), output.get("content",""))
        grades.append({"director": output.get("director",""), "type": output.get("output_type",""),
            "grade": grade.get("grade","N/A"), "score": grade.get("score",0),
            "actionable": grade.get("actionable", False), "recommendation": grade.get("recommendation","")})
        log.info(f"  {output.get('director','')}: {grade.get('grade','?')} ({grade.get('score',0)}/100)")
    
    avg_score = round(sum(g["score"] for g in grades)/max(len(grades),1))
    failing = [g for g in grades if g["score"] < 70]
    
    summary = f"QC REPORT ΓÇö {date.today()}\nOutputs reviewed: {len(grades)}\nAvg score: {avg_score}/100\nFailing: {len(failing)}"
    if failing:
        summary += "\n\nFAILING OUTPUTS:\n" + "\n".join(f"  {g['director']}: {g['grade']} ΓÇö {g['recommendation']}" for g in failing)
    
    save_output("Hayden Cross", "daily_qc", summary, {"avg_score": avg_score, "grades": grades})
    save_to_repo(f"data/qc/hayden_{date.today()}.json",
        json.dumps({"grades": grades, "avg_score": avg_score, "summary": summary}, indent=2),
        f"hayden: QC report {date.today()}")
    push("Hayden Cross | QC", f"Avg: {avg_score}/100 | Reviewed: {len(grades)} | Failing: {len(failing)}\n{summary[:200]}")
    log.info(f"\n{summary}")
    return {"avg_score": avg_score, "grades": grades}



# ΓòÉΓòÉΓòÉ SUPERCORE PARALLELISM WIRING ΓòÉΓòÉΓòÉ
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="hayden_cross"
        DIRECTOR_NAME="Hayden Cross"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES=['deming_quality', 'six_sigma', 'jobs_quality_bar', 'pixar_iteration']
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives=['deming_quality', 'six_sigma', 'jobs_quality_bar', 'pixar_iteration'],chain_steps=3,rank_criteria="quality_revenue_ready")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{r.get('grade','?')}
{r.get('final_output','')[:1000]}")
    else:
        run()
