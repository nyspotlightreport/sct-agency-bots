#!/usr/bin/env python3
# Dependency Updater Bot - Scans and updates outdated packages across all services.
import os, sys, json, logging
import subprocess
sys.path.insert(0,".")
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg, title="Dep Update"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def check_python_deps(requirements_file="requirements.txt"):
    if not os.path.exists(requirements_file):
        return {"error":f"{requirements_file} not found"}
    try:
        result = subprocess.run(["pip","list","--outdated","--format=json"],capture_output=True,text=True,timeout=60)
        outdated = json.loads(result.stdout) if result.returncode == 0 else []
        return {"outdated_count":len(outdated),"packages":outdated[:10],"file":requirements_file}
    except Exception as e:
        return {"error":str(e)}

def check_npm_deps():
    try:
        result = subprocess.run(["npm","outdated","--json"],capture_output=True,text=True,timeout=60,cwd="/home/claude")
        data = json.loads(result.stdout or "{}") if result.stdout else {}
        return {"outdated_count":len(data),"packages":list(data.keys())[:10]}
    except Exception as e:
        return {"error":str(e)}

def run_security_audit():
    try:
        result = subprocess.run(["pip","install","pip-audit","-q"],capture_output=True,text=True,timeout=60)
        audit = subprocess.run(["pip-audit","--format=json"],capture_output=True,text=True,timeout=120)
        vulns = json.loads(audit.stdout) if audit.returncode == 0 else []
        if isinstance(vulns, list) and vulns:
            notify(f"Security: {len(vulns)} vulnerabilities found in Python deps","Dep Security Alert")
        return {"vulnerabilities":len(vulns) if isinstance(vulns,list) else 0}
    except Exception as e:
        return {"error":str(e)}

def run():
    python_deps = check_python_deps()
    log.info(f"Python deps: {python_deps.get('outdated_count',0)} outdated")
    security = run_security_audit()
    log.info(f"Security audit: {security.get('vulnerabilities',0)} vulnerabilities")
    return {"python":python_deps,"security":security}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
