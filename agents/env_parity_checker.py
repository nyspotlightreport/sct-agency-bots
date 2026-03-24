#!/usr/bin/env python3
"""
agents/env_parity_checker.py — Weekly Env Var Parity Checker
Scans workflows and agents for secret references, compares against actual GitHub secrets.
"""
import os, re, json, subprocess, logging
import urllib.request as urlreq
import urllib.parse

log = logging.getLogger("env_parity")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PARITY] %(message)s")

PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY", "")

def get_github_secrets():
    """Get list of actual GitHub secrets via gh CLI"""
    try:
        result = subprocess.run(["gh", "secret", "list", "--json", "name"],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return {s["name"] for s in json.loads(result.stdout)}
    except:
        pass
    return set()

def scan_workflows():
    """Scan .github/workflows/*.yml for secrets references"""
    refs = set()
    wf_dir = os.path.join(os.path.dirname(__file__), "..", ".github", "workflows")
    if not os.path.isdir(wf_dir):
        return refs
    for fname in os.listdir(wf_dir):
        if not fname.endswith((".yml", ".yaml")):
            continue
        path = os.path.join(wf_dir, fname)
        try:
            with open(path) as f:
                content = f.read()
            matches = re.findall(r'\$\{\{\s*secrets\.(\w+)\s*\}\}', content)
            refs.update(matches)
        except:
            pass
    return refs

def scan_agents():
    """Scan agents/*.py for os.environ references"""
    refs = set()
    agents_dir = os.path.join(os.path.dirname(__file__))
    for fname in os.listdir(agents_dir):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(agents_dir, fname)
        try:
            with open(path) as f:
                content = f.read()
            matches = re.findall(r'os\.environ(?:\.get)?\s*\[\s*["\'](\w+)["\']\s*\]', content)
            matches += re.findall(r'os\.environ\.get\s*\(\s*["\'](\w+)["\']', content)
            refs.update(matches)
        except:
            pass
    return refs

def pushover(msg):
    if not PUSH_API or not PUSH_USER:
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_API, "user": PUSH_USER,
            "title": "Env Parity Check", "message": msg
        }).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json", data=data), timeout=10)
    except:
        pass

def log_to_supabase(missing, extra_info=""):
    if not SUPA_URL:
        return
    try:
        data = json.dumps({
            "all_passed": len(missing) == 0,
            "failures": list(missing),
            "details": {"type": "env_parity", "info": extra_info}
        }).encode()
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/site_health_log",
            data=data,
            headers={
                "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json", "Prefer": "return=minimal"
            }
        )
        urlreq.urlopen(req, timeout=10)
    except:
        pass

def run():
    log.info("=== Env Parity Check ===")
    actual_secrets = get_github_secrets()
    workflow_refs = scan_workflows()
    agent_refs = scan_agents()

    all_refs = workflow_refs | agent_refs
    missing = all_refs - actual_secrets

    # Filter out known non-secret env vars
    known_non_secrets = {"HOME", "PATH", "GITHUB_SHA", "GITHUB_WORKSPACE", "PYTHONPATH"}
    missing -= known_non_secrets

    if missing:
        msg = f"⚠️ MISSING SECRETS ({len(missing)}):\n" + "\n".join(sorted(missing))
        log.warning(msg)
        pushover(msg[:500])
    else:
        log.info("All %d referenced secrets exist", len(all_refs))
        pushover(f"✅ Env parity OK — {len(all_refs)} secrets verified")

    log_to_supabase(missing)
    log.info("=== Parity Check Complete ===")

if __name__ == "__main__":
    run()
