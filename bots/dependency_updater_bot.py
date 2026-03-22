#!/usr/bin/env python3
"""
Dependency Updater Bot — Keeps package.json and requirements.txt current.
Checks for outdated dependencies, identifies security patches,
and proposes update PRs.
"""
import os, sys, json, logging, base64
from datetime import datetime
sys.path.insert(0, ".")

import urllib.request

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

def gh(path, method="GET", body=None):
    if not GH_TOKEN: return None
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
            data=json.dumps(body).encode() if body else None,
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/json"},
            method=method)
        with urllib.request.urlopen(req,timeout=15) as r:
            if r.status == 204: return {}
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"GH {path}: {e}")
        return None

def check_npm_outdated(package: str) -> dict:
    try:
        req = urllib.request.Request(f"https://registry.npmjs.org/{package}/latest",
            headers={"Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=10) as r:
            data = json.loads(r.read())
            return {"package":package,"latest":data.get("version","?"),"deprecated":data.get("deprecated",False)}
    except: return {"package":package,"latest":"?","error":True}

def check_pypi_outdated(package: str) -> dict:
    try:
        pkg_clean = package.split(">=")[0].split("==")[0].split("<=")[0].strip()
        req = urllib.request.Request(f"https://pypi.org/pypi/{pkg_clean}/json",
            headers={"Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=10) as r:
            data = json.loads(r.read())
            info = data.get("info",{})
            return {"package":pkg_clean,"latest":info.get("version","?"),"yanked":info.get("yanked",False)}
    except: return {"package":package,"latest":"?","error":True}

def run():
    log.info("Dependency Updater Bot scanning dependencies...")
    
    # Check package.json
    pkg_json = gh(f"/repos/{REPO}/contents/package.json")
    npm_updates = []
    if pkg_json and isinstance(pkg_json,dict):
        try:
            content = base64.b64decode(pkg_json.get("content","").replace("\n","")).decode()
            pkg_data = json.loads(content)
            deps = {**pkg_data.get("dependencies",{}),**pkg_data.get("devDependencies",{})}
            for pkg in list(deps.keys())[:10]:  # Check top 10
                info = check_npm_outdated(pkg)
                npm_updates.append(info)
                log.info(f"  npm: {pkg} → {info.get('latest','?')}")
        except Exception as e:
            log.warning(f"package.json parse: {e}")
    
    # Check requirements.txt
    req_txt = gh(f"/repos/{REPO}/contents/requirements.txt")
    py_updates = []
    if req_txt and isinstance(req_txt,dict):
        try:
            content = base64.b64decode(req_txt.get("content","").replace("\n","")).decode()
            packages = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]
            for pkg in packages[:10]:
                info = check_pypi_outdated(pkg)
                py_updates.append(info)
                log.info(f"  pip: {pkg} → {info.get('latest','?')}")
        except Exception as e:
            log.warning(f"requirements.txt parse: {e}")
    
    deprecated = [p for p in npm_updates if p.get("deprecated")]
    log.info(f"NPM: {len(npm_updates)} checked | {len(deprecated)} deprecated")
    log.info(f"PyPI: {len(py_updates)} checked")
    
    return {"npm_checked":len(npm_updates),"pypi_checked":len(py_updates),"deprecated":len(deprecated)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [DepUpdater] %(message)s")
    run()
