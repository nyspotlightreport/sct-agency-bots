#!/usr/bin/env python3
# Monitoring Bot - Sentry, uptime, alerting, logging setup across all services.
import os, sys, json, logging
sys.path.insert(0,".")
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg, title="Monitor Alert"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def check_url(url, timeout=10):
    import time
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"NYSR-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"url":url,"status":r.status,"ok":r.status==200,"response_ms":round((time.time()-start)*1000)}
    except Exception as e:
        return {"url":url,"status":0,"ok":False,"error":str(e),"response_ms":round((time.time()-start)*1000)}

MONITOR_URLS = [
    "https://nyspotlightreport.com",
    "https://nyspotlightreport.com/command/",
    "https://nyspotlightreport.com/crm/",
    "https://nyspotlightreport.com/proflow/",
]

def run_uptime_check():
    results = [check_url(url) for url in MONITOR_URLS]
    down = [r for r in results if not r["ok"]]
    if down:
        msg = f"DOWN: {len(down)} pages
" + "
".join([f"  {r['url']}: {r.get('error','status '+str(r['status']))}" for r in down])
        notify(msg, "NYSR Uptime Alert")
        logging.error(msg)
    else:
        avg_ms = sum(r["response_ms"] for r in results) / len(results)
        log.info(f"All {len(results)} URLs up. Avg response: {avg_ms:.0f}ms")
    return {"total":len(results),"down":len(down),"results":results}

def sentry_snippet(platform="python"):
    if platform == "python":
        return "import sentry_sdk
sentry_sdk.init(dsn=os.environ['SENTRY_DSN'],traces_sample_rate=0.1,environment='production')"
    return "import*as Sentry from '@sentry/nextjs';
Sentry.init({dsn:process.env.NEXT_PUBLIC_SENTRY_DSN,tracesSampleRate:0.1});"

def run():
    return run_uptime_check()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
