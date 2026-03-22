#!/usr/bin/env python3
# Security Auditor Agent - OWASP Top 10, secret scanning, code audit, compliance.
import os, sys, re, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude_json
except:
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

SECRET_PATTERNS = [
    (r"sk-ant-[a-zA-Z0-9\-_]{40,}", "Anthropic API key"),
    (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe live key"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub PAT"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access key"),
]

def scan_secrets(code, filename=""):
    findings = []
    for i, line in enumerate(code.split("\n"), 1):
        for pattern, secret_type in SECRET_PATTERNS:
            if re.search(pattern, line) and not any(p in line for p in ["YOUR_","example","REPLACE","placeholder"]):
                findings.append({"line":i,"type":secret_type,"severity":"CRITICAL","file":filename,"fix":"Move to env var"})
    return findings

def audit_code(code):
    issues = []
    if "os.system(" in code: issues.append({"type":"command_injection","severity":"CRITICAL"})
    if "pickle.loads" in code: issues.append({"type":"unsafe_deserialization","severity":"HIGH"})
    if "debug=True" in code: issues.append({"type":"debug_in_prod","severity":"MEDIUM"})
    issues += scan_secrets(code)
    return {"issues":issues,"critical":len([i for i in issues if i["severity"]=="CRITICAL"]),"passed":len(issues)==0}

def security_checklist(project="saas"):
    base = ["All secrets in env vars","HTTPS only","Input validation everywhere","Parameterized queries","Rate limiting","CORS configured","Dep audit run"]
    if project == "saas": base += ["Row-level security","Stripe webhook verification","User data isolation"]
    return base

def run():
    test = 'api_key = "sk-ant-abc123"
query = "SELECT * FROM users WHERE id = " + user_id'
    result = audit_code(test)
    log.info(f"Audit: {result['critical']} critical issues found")
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
