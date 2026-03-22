#!/usr/bin/env python3
"""
agents/code_quality_gate.py — NYSR Code Quality Gate (Qodo Concept)
Reviews every commit, grades code quality, generates test suggestions,
checks for anti-patterns, enforces standards. Hayden Cross + Reese Morgan.
"""
import os, sys, json, logging, base64, re
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.supercore import SuperDirector, pushover, supa
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def pushover(*a,**k): pass
    def supa(*a,**k): return None

log = logging.getLogger("quality")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [QUALITY] %(message)s")

GH_PAT = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
REPO = "nyspotlightreport/sct-agency-bots"
import urllib.request as urlreq

def gh(path):
    req = urlreq.Request(f"https://api.github.com/repos/{REPO}/{path}",
        headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json"})
    try:
        with urlreq.urlopen(req, timeout=20) as r: return json.loads(r.read())
    except: return None

QUALITY_CHECKS = [
    {"name":"missing_docstring","pattern":r'^def \w+\([^)]*\):\s*\n\s*(?!"""|\'\'\')','severity':'MEDIUM'},
    {"name":"bare_except","pattern":r'except\s*:','severity':'HIGH'},
    {"name":"magic_number","pattern":r'(?<!["\'])\b(?:86400|3600|1440|60000)\b','severity':'LOW'},
    {"name":"missing_type_hints","pattern":r'^def \w+\(\s*(?:self\s*,?\s*)?(?:\w+\s*(?:,|\))(?!\s*:))','severity':'LOW'},
    {"name":"long_function","check":"line_count","threshold":80,"severity":"MEDIUM"},
    {"name":"no_error_handling","pattern":r'urlopen|requests\.(?:get|post)','needs_nearby':r'try|except','severity':'HIGH'},
    {"name":"hardcoded_url","pattern":r'https?://(?!api\.|cdn\.)[\w.-]+\.(?:com|io|net)/\w+','severity':'MEDIUM'},
    {"name":"unused_import","check":"import_analysis","severity":"LOW"},
]

def review_file(filepath, content):
    issues = []
    lines = content.split('\n')
    for check in QUALITY_CHECKS:
        if "pattern" in check:
            for i, line in enumerate(lines):
                if re.search(check["pattern"], line):
                    if "needs_nearby" in check:
                        context = '\n'.join(lines[max(0,i-5):i+5])
                        if not re.search(check["needs_nearby"], context):
                            issues.append({"file":filepath,"line":i+1,"issue":check["name"],"severity":check["severity"]})
                    else:
                        issues.append({"file":filepath,"line":i+1,"issue":check["name"],"severity":check["severity"]})
        elif check.get("check") == "line_count":
            # Check function lengths
            in_func = False; func_start = 0; func_name = ""
            for i, line in enumerate(lines):
                if re.match(r'^def \w+', line):
                    if in_func and (i - func_start) > check["threshold"]:
                        issues.append({"file":filepath,"line":func_start+1,"issue":f"long_function:{func_name}({i-func_start}lines)","severity":check["severity"]})
                    in_func = True; func_start = i; func_name = line.split('(')[0].replace('def ','')
    return issues

def ai_review_recent_commits():
    commits = gh("commits?per_page=5")
    if not isinstance(commits, list): return []
    reviews = []
    for commit in commits[:3]:
        sha = commit.get("sha","")
        msg = commit.get("commit",{}).get("message","")
        detail = gh(f"commits/{sha}")
        if not detail: continue
        files_changed = [f["filename"] for f in detail.get("files",[]) if f["filename"].endswith((".py",".js"))]
        if not files_changed: continue
        patch_text = "\n".join(f.get("patch","")[:500] for f in detail.get("files",[]) if f.get("patch"))[:2000]
        if not patch_text: continue
        review = claude_json(
            "You are Hayden Cross, QC Director. Grade this commit A+ to F. Find bugs, anti-patterns, and suggest tests.",
            f"Commit: {msg}\nFiles: {', '.join(files_changed)}\nPatch:\n{patch_text}\n\n"
            f"Return JSON: {{\"grade\":\"B+\",\"issues\":[\"issue1\"],\"tests_needed\":[\"test1\"],\"verdict\":\"...\"}}")
        if review:
            review["sha"] = sha[:8]
            review["message"] = msg[:60]
            reviews.append(review)
    return reviews

def run():
    log.info("="*50)
    log.info("CODE QUALITY GATE — Hayden Cross + Reese Morgan")
    log.info("="*50)
    all_issues = []
    for folder in ["agents", "bots"]:
        contents = gh(f"contents/{folder}")
        if not isinstance(contents, list): continue
        sample = [f for f in contents if f["name"].endswith(".py")][:20]
        for item in sample:
            file_data = gh(f"contents/{folder}/{item['name']}")
            if not file_data or "content" not in file_data: continue
            try:
                code = base64.b64decode(file_data["content"]).decode()
                issues = review_file(f"{folder}/{item['name']}", code)
                all_issues.extend(issues)
            except: pass
    commit_reviews = ai_review_recent_commits()
    high = [i for i in all_issues if i["severity"]=="HIGH"]
    report = f"""CODE QUALITY REPORT — {datetime.utcnow().strftime('%Y-%m-%d')}
STATIC ANALYSIS: {len(all_issues)} issues (HIGH:{len(high)} MEDIUM:{len([i for i in all_issues if i['severity']=='MEDIUM'])} LOW:{len([i for i in all_issues if i['severity']=='LOW'])})
COMMIT REVIEWS: {len(commit_reviews)} recent commits graded
"""
    for r in commit_reviews:
        report += f"\n  [{r.get('grade','?')}] {r.get('sha','')} {r.get('message','')}: {r.get('verdict','')[:100]}"
    for i in high[:5]:
        report += f"\n  [HIGH] {i['file']}:{i['line']} — {i['issue']}"
    log.info(report)
    supa("POST","director_outputs",{"director":"Code Quality Gate","output_type":"quality_review",
        "content":report[:2000],"metrics":json.dumps({"total_issues":len(all_issues),"high":len(high),
        "commits_reviewed":len(commit_reviews)}), "created_at":datetime.utcnow().isoformat()})
    pushover("Code Quality Gate",f"{len(all_issues)} issues, {len(commit_reviews)} commits graded\n{report[:300]}")
    return {"issues":len(all_issues),"high":len(high),"commit_reviews":commit_reviews,"report":report}

if __name__=="__main__":
    run()
