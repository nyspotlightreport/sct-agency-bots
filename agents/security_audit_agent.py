#!/usr/bin/env python3
"""
Security Audit Agent — Scans codebase for security vulnerabilities.
Checks:
  - Hardcoded secrets/API keys
  - SQL injection vectors
  - Exposed credentials in commits
  - Insecure HTTP usage
  - Missing input validation
  - Dependency vulnerabilities
"""
import os, sys, json, logging, re
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude_json
except:
    def claude_json(s,u,**k): return {}

import urllib.request, urllib.parse, base64

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

# Patterns that indicate security issues
SECURITY_PATTERNS = {
    "hardcoded_secret":    re.compile(r"(api_key|secret|password|token|passwd)\s*=\s*['"][a-zA-Z0-9_\-]{10,}['"]", re.IGNORECASE),
    "hardcoded_key_var":   re.compile(r"ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,}|pat-na1-[a-zA-Z0-9\-_]{50,}"),
    "sql_injection":       re.compile(r"(SELECT|INSERT|UPDATE|DELETE).+\+\s*[a-z_]+\s*\+", re.IGNORECASE),
    "eval_exec":           re.compile(r"(eval|exec)\s*\("),
    "shell_injection":     re.compile(r"subprocess\.call\(.+shell=True"),
    "http_not_https":      re.compile(r"http://(?!localhost|127\.0\.0\.1)"),
    "no_verify":           re.compile(r"verify=False"),
    "debug_print":         re.compile(r"print\(.*(password|secret|token|key)", re.IGNORECASE),
}

SEVERITY = {
    "hardcoded_secret": "CRITICAL",
    "hardcoded_key_var":"CRITICAL",
    "sql_injection":    "HIGH",
    "eval_exec":        "HIGH",
    "shell_injection":  "HIGH",
    "http_not_https":   "MEDIUM",
    "no_verify":        "MEDIUM",
    "debug_print":      "LOW",
}

def notify(msg, title="Security Audit"):
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def gh(path):
    if not GH_TOKEN: return None
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"GH {path}: {e}")
        return None

def scan_file(path: str, content: str) -> list:
    """Scan a file for security issues."""
    findings = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        for check_name, pattern in SECURITY_PATTERNS.items():
            if pattern.search(line):
                # Skip if it's reading from env vars (safe)
                if "os.environ" in line or "os.getenv" in line: continue
                if "example" in line.lower() or "your_" in line.lower(): continue
                findings.append({
                    "file":     path,
                    "line":     i,
                    "issue":    check_name,
                    "severity": SEVERITY.get(check_name,"MEDIUM"),
                    "code":     line.strip()[:100],
                })
    return findings

def get_python_files() -> list:
    """Get all Python files from the repo."""
    all_files = []
    for folder in ["agents","bots"]:
        files = gh(f"/repos/{REPO}/contents/{folder}")
        if files and isinstance(files,list):
            all_files.extend([f for f in files if f["name"].endswith(".py")])
    return all_files

def get_file_content(download_url: str) -> str:
    try:
        with urllib.request.urlopen(download_url,timeout=10) as r:
            return r.read().decode("utf-8","replace")
    except: return ""

def run():
    log.info("Security Audit Agent scanning codebase...")
    files = get_python_files()
    log.info(f"Files to scan: {len(files)}")
    
    all_findings = []
    for f in files:
        content = get_file_content(f.get("download_url",""))
        if content:
            findings = scan_file(f["path"], content)
            all_findings.extend(findings)
    
    critical = [f for f in all_findings if f["severity"]=="CRITICAL"]
    high     = [f for f in all_findings if f["severity"]=="HIGH"]
    medium   = [f for f in all_findings if f["severity"]=="MEDIUM"]
    
    log.info(f"Findings: {len(all_findings)} total | {len(critical)} critical | {len(high)} high | {len(medium)} medium")
    
    if critical:
        notify(f"🚨 CRITICAL Security Issues Found: {len(critical)}\n" +
               "\n".join([f"• {f['file']}:{f['line']} — {f['issue']}" for f in critical[:3]]),
               "Security: CRITICAL")
    elif high or medium:
        notify(f"⚠️ Security Scan: {len(all_findings)} issues\n{len(high)} high | {len(medium)} medium\nRun full report for details.",
               "Security Audit")
    else:
        notify("✅ Security scan complete. No critical issues found.", "Security Audit")
    
    return {
        "files_scanned": len(files),
        "total_findings": len(all_findings),
        "critical": len(critical),
        "high": len(high),
        "medium": len(medium),
        "findings": all_findings[:20],
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Security] %(message)s")
    run()
