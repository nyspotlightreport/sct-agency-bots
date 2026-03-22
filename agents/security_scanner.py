#!/usr/bin/env python3
"""
agents/security_scanner.py — NYSR Security Scanner (Snyk Concept)
Scans the entire codebase for vulnerabilities, credential leaks,
dependency issues, and security anti-patterns.
Runs daily via GitHub Actions.
"""
import os, sys, json, logging, re, base64
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

log = logging.getLogger("security")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SECURITY] %(message)s")

GH_PAT = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
REPO = "nyspotlightreport/sct-agency-bots"
import urllib.request as urlreq

def gh(path):
    req = urlreq.Request(f"https://api.github.com/repos/{REPO}/{path}",
        headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json"})
    try:
        with urlreq.urlopen(req, timeout=20) as r: return json.loads(r.read())
    except: return None

# ── VULNERABILITY PATTERNS ──────────────────────────────
VULN_PATTERNS = [
    {"name":"hardcoded_api_key","pattern":r'(?:api[_-]?key|secret|token|password)\s*[=:]\s*["\'][A-Za-z0-9_\-]{20,}["\']',"severity":"CRITICAL","fix":"Move to environment variable or GitHub Secret"},
    {"name":"hardcoded_email","pattern":r'[a-zA-Z0-9._%+-]+@gmail\.com',"severity":"MEDIUM","fix":"Use environment variable for email addresses"},
    {"name":"eval_usage","pattern":r'\beval\s*\(',"severity":"HIGH","fix":"Replace eval() with safe alternatives"},
    {"name":"no_timeout","pattern":r'urlopen\([^)]*\)\s*(?!.*timeout)',"severity":"MEDIUM","fix":"Add timeout parameter to all HTTP requests"},
    {"name":"sql_injection","pattern":r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*\{.*\}',"severity":"CRITICAL","fix":"Use parameterized queries"},
    {"name":"debug_print","pattern":r'print\s*\(\s*f?["\'].*(?:key|secret|token|pass)',"severity":"HIGH","fix":"Remove debug prints that may leak secrets"},
    {"name":"http_no_verify","pattern":r'verify\s*=\s*False',"severity":"MEDIUM","fix":"Enable SSL verification"},
    {"name":"pickle_load","pattern":r'pickle\.load',"severity":"HIGH","fix":"Use json.loads instead of pickle for untrusted data"},
    {"name":"subprocess_shell","pattern":r'subprocess\.(?:call|run|Popen)\([^)]*shell\s*=\s*True',"severity":"HIGH","fix":"Use list arguments instead of shell=True"},
    {"name":"temp_file_predictable","pattern":r'/tmp/[a-z_]+\.(?:json|txt|py)',"severity":"LOW","fix":"Use tempfile module for secure temp files"},
]

def scan_file(filepath, content):
    findings = []
    for vuln in VULN_PATTERNS:
        matches = list(re.finditer(vuln["pattern"], content, re.IGNORECASE))
        for m in matches:
            line_num = content[:m.start()].count('\n') + 1
            findings.append({
                "file": filepath, "line": line_num,
                "vuln": vuln["name"], "severity": vuln["severity"],
                "fix": vuln["fix"], "match": m.group()[:80]
            })
    return findings

def scan_dependencies():
    issues = []
    pkg = gh("contents/package.json")
    if pkg and "content" in pkg:
        content = base64.b64decode(pkg["content"]).decode()
        if "([^" in content:
            issues.append({"severity":"CRITICAL","issue":"package.json has broken dependency","fix":"Remove regex artifact line"})
    req_file = gh("contents/requirements.txt")
    if req_file and "content" in req_file:
        content = base64.b64decode(req_file["content"]).decode()
        for line in content.strip().split("\n"):
            if "==" not in line and ">=" not in line and line.strip():
                issues.append({"severity":"LOW","issue":f"Unpinned dependency: {line.strip()}","fix":"Pin version"})
    # Check GitHub security alerts
    alerts = gh("dependabot/alerts?state=open")
    if isinstance(alerts, list):
        for a in alerts[:10]:
            issues.append({"severity": a.get("security_advisory",{}).get("severity","MEDIUM").upper(),
                "issue": a.get("security_advisory",{}).get("summary","Unknown vulnerability"),
                "fix": a.get("security_advisory",{}).get("description","Update dependency")[:100]})
    return issues

def scan_codebase():
    log.info("SECURITY SCAN — Starting full codebase scan...")
    all_findings = []
    for folder in ["agents", "bots", "netlify/functions"]:
        contents = gh(f"contents/{folder}")
        if not isinstance(contents, list): continue
        for item in contents:
            if not item["name"].endswith((".py",".js")): continue
            file_data = gh(f"contents/{folder}/{item['name']}")
            if not file_data or "content" not in file_data: continue
            try:
                code = base64.b64decode(file_data["content"]).decode()
                findings = scan_file(f"{folder}/{item['name']}", code)
                all_findings.extend(findings)
            except: pass
    dep_issues = scan_dependencies()
    return all_findings, dep_issues

def run():
    log.info("="*50)
    log.info("NYSR SECURITY SCANNER — Full Scan")
    log.info("="*50)
    findings, dep_issues = scan_codebase()
    critical = [f for f in findings if f["severity"] == "CRITICAL"]
    high = [f for f in findings if f["severity"] == "HIGH"]
    medium = [f for f in findings if f["severity"] == "MEDIUM"]
    low = [f for f in findings if f["severity"] == "LOW"]
    report = f"""SECURITY SCAN REPORT — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
CRITICAL: {len(critical)} | HIGH: {len(high)} | MEDIUM: {len(medium)} | LOW: {len(low)}
DEPENDENCY ISSUES: {len(dep_issues)}
"""
    for f in critical[:10]:
        report += f"\n[CRITICAL] {f['file']}:{f['line']} — {f['vuln']}: {f['fix']}"
    for f in high[:10]:
        report += f"\n[HIGH] {f['file']}:{f['line']} — {f['vuln']}: {f['fix']}"
    for d in dep_issues[:5]:
        report += f"\n[DEP-{d['severity']}] {d['issue']}: {d['fix']}"
    log.info(report)
    supa("POST","director_outputs",{"director":"Security Scanner","output_type":"security_scan",
        "content":report[:2000],"metrics":json.dumps({"critical":len(critical),"high":len(high),
        "medium":len(medium),"low":len(low),"dep_issues":len(dep_issues)}),
        "created_at":datetime.utcnow().isoformat()})
    if critical:
        pushover("SECURITY CRITICAL",f"{len(critical)} critical vulnerabilities found!\n{report[:300]}",priority=1)
    else:
        pushover("Security Scan OK",f"No critical issues. {len(high)} high, {len(medium)} medium.",priority=0)
    log.info(f"Scan complete: {len(findings)} findings, {len(dep_issues)} dep issues")
    return {"findings":len(findings),"critical":len(critical),"high":len(high),"report":report}

if __name__=="__main__":
    run()
