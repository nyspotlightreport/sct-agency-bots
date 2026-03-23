#!/usr/bin/env python3
"""
Error Aggregator Bot — Collects and correlates errors from all sources.
Sources: GitHub Actions failures, Netlify function errors, Supabase logs.
Groups similar errors, tracks frequency, and identifies error trends.
Feeds data to Auto Debugger for resolution.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def supabase_request(m,t,**k): return None

import urllib.request, urllib.parse

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
NETLIFY_TOKEN = os.environ.get("NETLIFY_AUTH_TOKEN","")
NETLIFY_SITE  = os.environ.get("NETLIFY_SITE_ID","8ef722e1-4110-42af-8ddb-ff6c2ce1745e")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

def gh(path):
    if not GH_TOKEN: return None
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except: return None

def get_github_errors() -> list:
    runs = gh(f"/repos/{REPO}/actions/runs?status=failure&per_page=20")
    errors = []
    for r in (runs or {}).get("workflow_runs",[]):
        errors.append({
            "source":    "github_actions",
            "name":      r.get("name",""),
            "error_msg": f"Workflow failed: {r.get('name','')}",
            "url":       r.get("html_url",""),
            "timestamp": r.get("updated_at",""),
        })
    return errors

def get_netlify_errors() -> list:
    if not NETLIFY_TOKEN: return []
    try:
        req = urllib.request.Request(
            f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE}/deploys?per_page=5",
            headers={"Authorization":f"Bearer {NETLIFY_TOKEN}"}
        )
        with urllib.request.urlopen(req,timeout=10) as r:
            deploys = json.loads(r.read())
        errors = []
        for d in deploys:
            if d.get("state") in ["error","failed"]:
                errors.append({
                    "source":    "netlify",
                    "name":      f"Deploy {d.get('id','')[:8]}",
                    "error_msg": d.get("error_message","Deploy failed"),
                    "url":       d.get("admin_url",""),
                    "timestamp": d.get("created_at",""),
                })
        return errors
    except: return []

def group_errors(errors: list) -> dict:
    groups = {}
    for e in errors:
        key = e.get("error_msg","")[:50]
        if key not in groups:
            groups[key] = {"count":0,"examples":[],"sources":[]}
        groups[key]["count"] += 1
        groups[key]["examples"].append(e)
        if e.get("source") not in groups[key]["sources"]:
            groups[key]["sources"].append(e.get("source",""))
    return groups

def save_errors(errors: list):
    for e in errors:
        supabase_request("POST","error_log",{
            "source":    e.get("source",""),
            "error_msg": e.get("error_msg","")[:500],
            "url":       e.get("url",""),
            "recorded_at": datetime.utcnow().isoformat(),
        })

def run():
    log.info("Error Aggregator Bot collecting errors...")
    
    gh_errors      = get_github_errors()
    netlify_errors = get_netlify_errors()
    all_errors     = gh_errors + netlify_errors
    
    log.info(f"Errors: {len(gh_errors)} GitHub | {len(netlify_errors)} Netlify")
    
    groups = group_errors(all_errors)
    save_errors(all_errors)
    
    if all_errors:
        summary = f"🚨 {len(all_errors)} errors aggregated\n{len(gh_errors)} GitHub | {len(netlify_errors)} Netlify\n\nTop issues:\n"
        for key, data in list(groups.items())[:3]:
            summary += f"• [{data['count']}x] {key}\n"
        if PUSHOVER_API and PUSHOVER_USER:
            try:
                data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Error Aggregator","message":summary[:1000]}).encode()
                urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
            except Exception:  # noqa: bare-except

                pass
    return {"total_errors":len(all_errors),"groups":len(groups),"github":len(gh_errors),"netlify":len(netlify_errors)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [ErrAgg] %(message)s")
    run()
