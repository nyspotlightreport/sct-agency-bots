#!/usr/bin/env python3
"""agents/system_watchdog.py — End-to-End Health Monitor. Runs every 6h."""
import os,sys,json,logging,time,base64
from datetime import datetime,timedelta
sys.path.insert(0,".")
log=logging.getLogger("watchdog")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [WATCHDOG] %(message)s")
import urllib.request as urlreq,urllib.parse,urllib.error
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
GH_PAT=os.environ.get("GH_PAT","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
STRIPE_SK=os.environ.get("STRIPE_SECRET_KEY","")
SITE="https://nyspotlightreport.com"
RN="nyspotlightreport/sct-agency-bots"
def push(t,m,p=0):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000],"priority":p}).encode(),timeout=5)
    except:pass
def gh(path):
    try:
        with urlreq.urlopen(urlreq.Request(f"https://api.github.com/repos/{RN}/{path}",headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json"}),timeout=20) as r:return json.loads(r.read())
    except:return None
def ck_site():
    try:
        with urlreq.urlopen(urlreq.Request(SITE,headers={"User-Agent":"NYSR-WD"}),timeout=15) as r:return r.getcode()==200,f"HTTP {r.getcode()}"
    except Exception as e:return False,str(e)[:80]
def ck_fn(n):
    try:
        with urlreq.urlopen(urlreq.Request(f"{SITE}/.netlify/functions/{n}",headers={"User-Agent":"NYSR-WD"}),timeout=15) as r:return True,f"HTTP {r.getcode()}"
    except urllib.error.HTTPError as e:return e.code in(400,405,500),f"HTTP {e.code}"
    except Exception as e:return False,str(e)[:80]
def ck_stripe():
    if not STRIPE_SK:return False,"No key"
    try:
        auth=base64.b64encode(f"{STRIPE_SK}:".encode()).decode()
        with urlreq.urlopen(urlreq.Request("https://api.stripe.com/v1/webhook_endpoints?limit=5",headers={"Authorization":f"Basic {auth}"}),timeout=10) as r:
            data=json.loads(r.read());nysr=[e for e in data.get("data",[]) if "nyspotlightreport" in e.get("url","")]
            return len(nysr)>0,f"{len(nysr)} endpoints"
    except Exception as e:return False,str(e)[:80]
def ck_supa():
    if not SUPA_URL:return False,"No URL"
    try:
        with urlreq.urlopen(urlreq.Request(f"{SUPA_URL}/rest/v1/?apikey={SUPA_KEY}",headers={"apikey":SUPA_KEY}),timeout=10) as r:return True,"OK"
    except Exception as e:return False,str(e)[:80]
def ck_wf():
    runs=gh("actions/runs?per_page=30&status=failure")
    if not runs:return True,"Cannot fetch"
    recent=[r for r in runs.get("workflow_runs",[]) if datetime.strptime(r["updated_at"][:19],"%Y-%m-%dT%H:%M:%S")>datetime.utcnow()-timedelta(hours=24)]
    return len(recent)==0,f"{len(recent)} failures" if recent else "Clean"
def ck_zeros():
    c=gh("contents/agents")
    if not isinstance(c,list):return True,"Cannot list"
    z=[f["name"] for f in c if f.get("size",1)==0]
    return len(z)==0,f"{len(z)} empty" if z else f"All {len(c)} OK"
def run():
    log.info("WATCHDOG — Full Health Check")
    checks=[]
    for name,fn in [("SITE",ck_site),("FUNC:stripe-webhook",lambda:ck_fn("stripe-webhook")),("FUNC:lead-capture",lambda:ck_fn("lead-capture")),("STRIPE_WH",ck_stripe),("SUPABASE",ck_supa),("WORKFLOWS",ck_wf),("ZERO_BYTES",ck_zeros)]:
        ok,msg=fn();checks.append((name,ok,msg));log.info(f"{'OK' if ok else 'FAIL'} {name}: {msg}")
    failed=[(n,m) for n,o,m in checks if not o]
    rpt=f"WATCHDOG {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}|{len(checks)-len(failed)}/{len(checks)} passed"
    if failed:rpt+="\nFAILURES:"+",".join(f"{n}({m})" for n,m in failed);push("WATCHDOG ALERT",rpt,1)
    else:push("Watchdog OK",rpt,-1)
    log.info(rpt);return {"passed":len(checks)-len(failed),"total":len(checks)}
if __name__=="__main__":run()
