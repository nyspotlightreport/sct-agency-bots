#!/usr/bin/env python3
"""
Performance Monitor Bot — Tracks system performance metrics.
Monitors: Netlify function response times, workflow durations,
API call latency, and system health scores.
Alerts on degradation and builds performance history.
"""
import os, sys, json, logging, time
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def supabase_request(m,t,**k): return None

import urllib.request, urllib.parse

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
NETLIFY_TOKEN = os.environ.get("NETLIFY_AUTH_TOKEN","")
NETLIFY_SITE  = os.environ.get("NETLIFY_SITE_ID","8ef722e1-4110-42af-8ddb-ff6c2ce1745e")

ENDPOINTS_TO_TEST = [
    {"name":"Homepage",        "url":"https://nyspotlightreport.com/",           "expected_status":200, "max_ms":3000},
    {"name":"Command Center",  "url":"https://nyspotlightreport.com/command/",   "expected_status":200, "max_ms":3000},
    {"name":"CRM Dashboard",   "url":"https://nyspotlightreport.com/crm/",       "expected_status":200, "max_ms":3000},
    {"name":"Token Collector", "url":"https://nyspotlightreport.com/tokens/",    "expected_status":200, "max_ms":3000},
    {"name":"Sales Dept",      "url":"https://nyspotlightreport.com/sales/",     "expected_status":200, "max_ms":3000},
    {"name":"Dev Dept",        "url":"https://nyspotlightreport.com/dev/",       "expected_status":200, "max_ms":3000},
]

def check_endpoint(endpoint: dict) -> dict:
    start = time.time()
    try:
        req = urllib.request.Request(endpoint["url"], headers={"User-Agent":"NYSR-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            elapsed_ms = int((time.time()-start)*1000)
            return {
                "name":       endpoint["name"],
                "url":        endpoint["url"],
                "status":     r.status,
                "elapsed_ms": elapsed_ms,
                "ok":         r.status == endpoint["expected_status"] and elapsed_ms <= endpoint["max_ms"],
                "issue":      None,
            }
    except urllib.error.HTTPError as e:
        return {"name":endpoint["name"],"url":endpoint["url"],"status":e.code,"elapsed_ms":int((time.time()-start)*1000),"ok":False,"issue":f"HTTP {e.code}"}
    except Exception as e:
        return {"name":endpoint["name"],"url":endpoint["url"],"status":0,"elapsed_ms":int((time.time()-start)*1000),"ok":False,"issue":str(e)[:100]}

def get_workflow_stats() -> dict:
    if not GH_TOKEN: return {}
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/runs?per_page=50",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        )
        with urllib.request.urlopen(req,timeout=15) as r:
            runs = json.loads(r.read())
        wf_runs = runs.get("workflow_runs",[])
        if not wf_runs: return {}
        total  = len(wf_runs)
        passed = len([r for r in wf_runs if r.get("conclusion")=="success"])
        failed = len([r for r in wf_runs if r.get("conclusion")=="failure"])
        return {"total":total,"passed":passed,"failed":failed,"pass_rate":round(passed/max(total,1)*100)}
    except Exception as e:
        log.warning(f"Workflow stats: {e}")
        return {}

def save_metrics(results: list, wf_stats: dict):
    supabase_request("POST","performance_metrics",{
        "endpoints_checked": len(results),
        "endpoints_ok":      sum(1 for r in results if r.get("ok")),
        "avg_response_ms":   round(sum(r.get("elapsed_ms",0) for r in results)/max(len(results),1)),
        "workflow_pass_rate": wf_stats.get("pass_rate",0),
        "recorded_at":       datetime.utcnow().isoformat(),
    })

def notify(msg, title="Perf Monitor"):
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except Exception:  # noqa: bare-except

        pass
def run():
    log.info("Performance Monitor Bot checking all endpoints...")
    results   = [check_endpoint(ep) for ep in ENDPOINTS_TO_TEST]
    wf_stats  = get_workflow_stats()
    
    ok_count  = sum(1 for r in results if r.get("ok"))
    fail_count = len(results) - ok_count
    avg_ms    = round(sum(r.get("elapsed_ms",0) for r in results)/max(len(results),1))
    
    log.info(f"Endpoints: {ok_count}/{len(results)} OK | Avg: {avg_ms}ms | Workflows: {wf_stats.get('pass_rate',0)}%")
    for r in results:
        status = "✅" if r["ok"] else "❌"
        log.info(f"  {status} {r['name']}: {r.get('elapsed_ms',0)}ms (HTTP {r['status']})")
    
    save_metrics(results, wf_stats)
    
    if fail_count > 0:
        failures = "\n".join([f"• {r['name']}: {r.get('issue','failed')}" for r in results if not r.get("ok")])
        notify(f"⚠️ {fail_count} endpoints DOWN\n{failures}\n\nAvg response: {avg_ms}ms", "Perf: Degraded")
    elif avg_ms > 2000:
        notify(f"🐌 Slow responses: avg {avg_ms}ms\nAll endpoints up but sluggish.", "Perf: Slow")
    else:
        notify(f"✅ All {ok_count} endpoints healthy\nAvg: {avg_ms}ms | Workflows: {wf_stats.get('pass_rate',0)}% passing", "Perf Monitor")
    
    return {"endpoints_ok":ok_count,"total":len(results),"avg_ms":avg_ms,"wf_pass_rate":wf_stats.get("pass_rate",0)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [PerfMon] %(message)s")
    run()
