#!/usr/bin/env python3
"""agents/system_watchdog.py — NYSR Ultra Watchdog v2
Runs every 30 min. Detects issues. Auto-repairs. Alerts ALL agents. Reviews system.
If ANY check fails: triggers Guardian, Omega Brain, and Reese Morgan for immediate fix.
"""
import os,sys,json,logging,time,base64,re
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
REPO="nyspotlightreport/sct-agency-bots"

def push(t,m,p=0):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000],"priority":p}).encode(),timeout=5)
    except:pass

def gh(path,method="GET",data=None):
    body=json.dumps(data).encode() if data else None
    req=urlreq.Request(f"https://api.github.com/repos/{REPO}/{path}",data=body,method=method,
        headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urlreq.urlopen(req,timeout=20) as r:return json.loads(r.read()) if r.read() else {}
    except urllib.error.HTTPError as e:
        try:return json.loads(e.read())
        except:return {"error":e.code}
    except:return None

def supa_post(table,data):
    if not SUPA_URL:return
    try:
        body=json.dumps(data).encode()
        req=urlreq.Request(f"{SUPA_URL}/rest/v1/{table}",data=body,method="POST",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=minimal"})
        urlreq.urlopen(req,timeout=10)
    except:pass

# ═══ CHECKS ═══
def check_site():
    try:
        with urlreq.urlopen(urlreq.Request(SITE,headers={"User-Agent":"NYSR-Watchdog/2.0"}),timeout=15) as r:
            return r.getcode()==200,f"HTTP {r.getcode()}"
    except Exception as e:return False,str(e)[:80]

def check_fn(name):
    try:
        with urlreq.urlopen(urlreq.Request(f"{SITE}/.netlify/functions/{name}",headers={"User-Agent":"NYSR-Watchdog"}),timeout=15) as r:
            return True,f"HTTP {r.getcode()}"
    except urllib.error.HTTPError as e:return e.code in(400,405),f"HTTP {e.code}"
    except Exception as e:return False,str(e)[:80]

def check_stripe():
    if not STRIPE_SK:return False,"No STRIPE_SECRET_KEY"
    try:
        auth=base64.b64encode(f"{STRIPE_SK}:".encode()).decode()
        with urlreq.urlopen(urlreq.Request("https://api.stripe.com/v1/webhook_endpoints?limit=5",headers={"Authorization":f"Basic {auth}"}),timeout=10) as r:
            data=json.loads(r.read());nysr=[e for e in data.get("data",[]) if "nyspotlightreport" in e.get("url","")]
            return len(nysr)>0,f"{len(nysr)} endpoint(s) registered"
    except Exception as e:return False,str(e)[:80]

def check_supa():
    if not SUPA_URL:return False,"No SUPABASE_URL"
    try:
        with urlreq.urlopen(urlreq.Request(f"{SUPA_URL}/rest/v1/director_outputs?select=id&limit=1",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"}),timeout=10) as r:
            return True,"Connected"
    except Exception as e:return False,str(e)[:80]

def check_wf_fails():
    runs=gh("actions/runs?per_page=50&status=failure")
    if not runs or not isinstance(runs,dict):return True,"Cannot fetch"
    recent=[r for r in runs.get("workflow_runs",[]) if
        datetime.strptime(r["updated_at"][:19],"%Y-%m-%dT%H:%M:%S")>datetime.utcnow()-timedelta(hours=1)]
    if recent:
        names=list(set(r["name"] for r in recent))[:5]
        return False,f"{len(recent)} fails in 1h: {', '.join(names)}"
    return True,"Clean (last 1h)"

def check_zeros():
    c=gh("contents/agents")
    if not isinstance(c,list):return True,"Cannot list"
    z=[f["name"] for f in c if f.get("size",1)==0]
    return len(z)==0,f"{len(z)} empty: {', '.join(z[:3])}" if z else f"All {len(c)} OK"

def check_revenue():
    if not STRIPE_SK:return True,"No Stripe key to check"
    try:
        auth=base64.b64encode(f"{STRIPE_SK}:".encode()).decode()
        now=int(time.time());day_ago=now-86400
        with urlreq.urlopen(urlreq.Request(f"https://api.stripe.com/v1/charges?created[gte]={day_ago}&limit=10",
            headers={"Authorization":f"Basic {auth}"}),timeout=10) as r:
            data=json.loads(r.read())
            charges=data.get("data",[])
            total=sum(c.get("amount",0) for c in charges if c.get("paid"))/100
            return True,f"${total:.2f} in 24h ({len(charges)} charges)"
    except Exception as e:return True,f"Check failed: {str(e)[:60]}"

def check_email_redirect():
    c=gh("contents/agents")
    if not isinstance(c,list):return True,"Cannot check"
    # Spot-check a few key files
    for fname in ["james_butler.py","jeff_banks_cro.py","priya_sharma_email_agent.py"]:
        fdata=gh(f"contents/agents/{fname}")
        if fdata and "content" in fdata:
            code=base64.b64decode(fdata["content"]).decode()
            if "seanb041992" in code.lower():
                return False,f"{fname} still has old email"
    return True,"Spot-check clean"

# ═══ AUTO-REPAIR CASCADE ═══
def trigger_repair(failure_name, failure_msg):
    """When a check fails, trigger the appropriate repair workflow and alert all agents."""
    log.info(f"AUTO-REPAIR: {failure_name} — {failure_msg}")
    repairs_triggered = []

    # Map failures to repair actions
    if "SITE" in failure_name:
        # Trigger site redeploy
        gh("actions/workflows/deploy-site.yml/dispatches",method="POST",data={"ref":"main"})
        repairs_triggered.append("deploy-site.yml")

    if "STRIPE" in failure_name:
        gh("actions/workflows/register_stripe_webhook.yml/dispatches",method="POST",data={"ref":"main"})
        repairs_triggered.append("register_stripe_webhook.yml")

    if "FUNC" in failure_name:
        # Netlify function down — redeploy + sync env
        gh("actions/workflows/set-netlify-env.yml/dispatches",method="POST",data={"ref":"main"})
        repairs_triggered.append("set-netlify-env.yml")

    if "ZERO" in failure_name:
        # Trigger Guardian self-healing
        gh("actions/workflows/guardian_self_healing.yml/dispatches",method="POST",data={"ref":"main"})
        repairs_triggered.append("guardian_self_healing.yml")

    if "WORKFLOW" in failure_name:
        gh("actions/workflows/guardian_always_on.yml/dispatches",method="POST",data={"ref":"main"})
        repairs_triggered.append("guardian_always_on.yml")

    if "EMAIL" in failure_name:
        # Trigger nuclear email fix
        gh("actions/workflows/guardian_self_healing.yml/dispatches",method="POST",data={"ref":"main"})
        repairs_triggered.append("guardian_self_healing.yml (email)")

    # Always alert Omega Brain for system-wide learning
    gh("actions/workflows/omega_orchestration.yml/dispatches",method="POST",data={"ref":"main"})
    repairs_triggered.append("omega_orchestration.yml")

    # Store failure + repair in Supabase for learning
    supa_post("director_outputs",{
        "director":"System Watchdog","output_type":"auto_repair",
        "content":json.dumps({"failure":failure_name,"message":failure_msg,"repairs":repairs_triggered})[:2000],
        "metrics":json.dumps({"repairs_triggered":len(repairs_triggered),"failure_type":failure_name}),
        "created_at":datetime.utcnow().isoformat()
    })
    return repairs_triggered

# ═══ MAIN RUN ═══
def run():
    log.info("="*60)
    log.info("ULTRA WATCHDOG v2 — 30min Cycle — Auto-Repair Active")
    log.info("="*60)
    checks=[]
    for name,fn in [
        ("SITE_UP",check_site),
        ("FUNC_stripe-webhook",lambda:check_fn("stripe-webhook")),
        ("FUNC_lead-capture",lambda:check_fn("lead-capture")),
        ("STRIPE_WEBHOOK",check_stripe),
        ("SUPABASE",check_supa),
        ("WORKFLOW_HEALTH",check_wf_fails),
        ("ZERO_BYTES",check_zeros),
        ("REVENUE_24H",check_revenue),
        ("EMAIL_REDIRECT",check_email_redirect),
    ]:
        try:
            ok,msg=fn()
        except Exception as e:
            ok,msg=False,f"CHECK CRASHED: {str(e)[:60]}"
        checks.append((name,ok,msg))
        log.info(f"{'OK' if ok else 'FAIL'} {name}: {msg}")

    failed=[(n,m) for n,o,m in checks if not o]
    passed=len(checks)-len(failed)
    ts=datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    report=f"WATCHDOG {ts} | {passed}/{len(checks)} passed"

    # ═══ AUTO-REPAIR ON FAILURE ═══
    all_repairs=[]
    if failed:
        report+=f"\n\nFAILURES ({len(failed)}):"
        for name,msg in failed:
            report+=f"\n  {name}: {msg}"
            repairs=trigger_repair(name,msg)
            all_repairs.extend(repairs)
            report+=f"\n    AUTO-REPAIR: {', '.join(repairs)}"
        report+=f"\n\nTOTAL REPAIRS TRIGGERED: {len(all_repairs)}"
        push(f"WATCHDOG ALERT | {len(failed)} failures",report[:800],priority=1)
    else:
        report+="\nALL SYSTEMS OPERATIONAL"
        # Only send quiet notification every 6h (not every 30min)
        hour=datetime.utcnow().hour
        if hour % 6 == 0 and datetime.utcnow().minute < 30:
            push("Watchdog OK",f"{passed}/{len(checks)} passed",priority=-1)

    log.info(f"\n{report}")
    # Save to Supabase
    supa_post("director_outputs",{
        "director":"System Watchdog","output_type":"health_check",
        "content":report[:2000],
        "metrics":json.dumps({"passed":passed,"failed":len(failed),"total":len(checks),
            "repairs":len(all_repairs),"failures":[f[0] for f in failed]}),
        "created_at":datetime.utcnow().isoformat()
    })
    return {"passed":passed,"failed":len(failed),"repairs":len(all_repairs)}

if __name__=="__main__":
    run()
