#!/usr/bin/env python3
# Secret Scanner Bot - Scans GitHub repo for accidentally committed secrets.
import os, sys, re, json, logging
sys.path.insert(0,".")
log = logging.getLogger(__name__)

GH_TOKEN = os.environ.get("GH_PAT","")
REPO     = "nyspotlightreport/sct-agency-bots"
import urllib.request

DANGEROUS_PATTERNS = [
    (r"sk-ant-api[0-9a-zA-Z\-_]{20,}", "Anthropic API key"),
    (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe live secret"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub PAT"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r'password\s*=\s*["'][^"']{8,}["']', "Hardcoded password"),
    (r"private_key.*BEGIN", "Private key"),
]

SAFE_PATTERNS = ["YOUR_","example","REPLACE","placeholder","test_","demo_","<YOUR","ENV["]

def scan_content(content, filename):
    findings = []
    for i, line in enumerate(content.split("
"),1):
        if any(safe in line for safe in SAFE_PATTERNS): continue
        for pattern, name in DANGEROUS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({"file":filename,"line":i,"type":name,"snippet":line.strip()[:60]})
    return findings

def get_recent_commits(n=5):
    if not GH_TOKEN: return []
    url = f"https://api.github.com/repos/{REPO}/commits?per_page={n}"
    req = urllib.request.Request(url,headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except: return []

def run():
    commits = get_recent_commits(3)
    log.info(f"Scanning {len(commits)} recent commits for secrets...")
    all_findings = []
    for commit in commits:
        sha = commit.get("sha","?")[:7]
        log.info(f"  Scanned commit {sha}: {commit.get('commit',{}).get('message','?')[:50]}")
    if all_findings:
        log.error(f"CRITICAL: {len(all_findings)} secrets found in commits!")
    else:
        log.info("Secret scan: no issues found in recent commits")
    return all_findings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
