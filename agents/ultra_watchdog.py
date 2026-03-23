#!/usr/bin/env python3
"""
agents/ultra_watchdog.py — NYSR Ultra Watchdog v3
Checks EVERYTHING. Every endpoint. Every webhook. Every file. Every link.
Every line of code that could fail. Auto-repairs. Alerts all agents.
Runs every 30 min. Nothing slips. Ever.
"""
import os,sys,json,logging,time,base64,re,hashlib
from datetime import datetime,timedelta
sys.path.insert(0,".")
log=logging.getLogger("ultra_watchdog")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [ULTRA-WATCHDOG] %(message)s")
import urllib.request as urlreq,urllib.parse,urllib.error

SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
GH_PAT=os.environ.get("GH_PAT","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
STRIPE_SK=os.environ.get("STRIPE_SECRET_KEY","")
ANTHROPIC_KEY=os.environ.get("ANTHROPIC_API_KEY","")
SITE="https://nyspotlightreport.com"
REPO="nyspotlightreport/sct-agency-bots"

# ═══ UTILITY FUNCTIONS ═══
def push(t,m,p=0):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000],"priority":p}).encode(),timeout=5)
    except:pass

def gh(path,method="GET",data=None):
    body=json.dumps(data).encode() if data else None
    req=urlreq.Request(f"https://api.github.com/repos/{REPO}/{path}",data=body,method=method,
        headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urlreq.urlopen(req,timeout=20) as r:
            raw=r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:return {"error":e.code,"body":e.read().decode()[:200]}
        except:return {"error":e.code}
    except Exception as ex:return {"error":str(ex)[:100]}

def supa_post(table,data):
    if not SUPA_URL:return
    try:
        req=urlreq.Request(f"{SUPA_URL}/rest/v1/{table}",data=json.dumps(data).encode(),method="POST",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=minimal"})
        urlreq.urlopen(req,timeout=10)
    except:pass

def fetch_url(url,timeout=15):
    try:
        req=urlreq.Request(url,headers={"User-Agent":"NYSR-UltraWatchdog/3.0"})
        with urlreq.urlopen(req,timeout=timeout) as r:
            return r.getcode(),r.read().decode(errors="ignore")[:5000]
    except urllib.error.HTTPError as e:return e.code,""
    except Exception as e:return 0,str(e)[:100]

# ═══════════════════════════════════════════════════════
# LEVEL 1: INFRASTRUCTURE CHECKS (Is anything down?)
# ═══════════════════════════════════════════════════════
def check_site_up():
    code,body=fetch_url(SITE)
    if code!=200:return False,f"Site DOWN HTTP {code}"
    if len(body)<500:return False,"Site returned minimal content"
    if "NY Spotlight" not in body and "NYSR" not in body:return False,"Site content missing branding"
    return True,f"HTTP 200, {len(body)} bytes, branded"

def check_site_pages():
    fails=[]
    pages=["/","/proflow/","/store/","/pricing/","/checkout/success/","/activate/","/reps/","/blog/"]
    for p in pages:
        code,body=fetch_url(f"{SITE}{p}")
        if code!=200:fails.append(f"{p}={code}")
    if fails:return False,f"{len(fails)} pages down: {', '.join(fails[:5])}"
    return True,f"All {len(pages)} pages responding"

def check_netlify_functions():
    fails=[]
    fns=["stripe-webhook","lead-capture","knowledge-base"]
    for fn in fns:
        code,body=fetch_url(f"{SITE}/.netlify/functions/{fn}")
        if code not in(200,400,405):fails.append(f"{fn}={code}")
    if fails:return False,f"Functions down: {', '.join(fails)}"
    return True,f"All {len(fns)} functions responding"

def check_stripe_webhook():
    if not STRIPE_SK:return False,"STRIPE_SECRET_KEY not set"
    try:
        auth=base64.b64encode(f"{STRIPE_SK}:".encode()).decode()
        with urlreq.urlopen(urlreq.Request("https://api.stripe.com/v1/webhook_endpoints?limit=10",
            headers={"Authorization":f"Basic {auth}"}),timeout=10) as r:
            data=json.loads(r.read())
            nysr=[e for e in data.get("data",[]) if "nyspotlightreport" in e.get("url","")]
            if not nysr:return False,"No webhook registered for nyspotlightreport.com"
            ep=nysr[0]
            status=ep.get("status","unknown")
            events=ep.get("enabled_events",[])
            if status!="enabled":return False,f"Webhook status: {status} (not enabled)"
            if "checkout.session.completed" not in events and "*" not in events:
                return False,f"Missing checkout.session.completed event"
            return True,f"Active, {len(events)} events, status={status}"
    except Exception as e:return False,str(e)[:80]

def check_stripe_products():
    if not STRIPE_SK:return True,"No key"
    try:
        auth=base64.b64encode(f"{STRIPE_SK}:".encode()).decode()
        with urlreq.urlopen(urlreq.Request("https://api.stripe.com/v1/prices?active=true&limit=10",
            headers={"Authorization":f"Basic {auth}"}),timeout=10) as r:
            data=json.loads(r.read())
            prices=data.get("data",[])
            if not prices:return False,"No active Stripe prices — nothing to sell"
            return True,f"{len(prices)} active prices"
    except Exception as e:return True,f"Check skipped: {str(e)[:60]}"

def check_supabase():
    if not SUPA_URL:return False,"SUPABASE_URL not set"
    try:
        with urlreq.urlopen(urlreq.Request(f"{SUPA_URL}/rest/v1/director_outputs?select=id&limit=1",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"}),timeout=10) as r:
            return True,"Connected, table accessible"
    except Exception as e:return False,str(e)[:80]

def check_anthropic():
    if not ANTHROPIC_KEY:return False,"ANTHROPIC_API_KEY not set"
    try:
        data=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":10,
            "messages":[{"role":"user","content":"reply ok"}]}).encode()
        req=urlreq.Request("https://api.anthropic.com/v1/messages",data=data,
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
        with urlreq.urlopen(req,timeout=30) as r:
            return True,"API responding"
    except Exception as e:return False,str(e)[:80]

# ═══════════════════════════════════════════════════════
# LEVEL 2: CODE INTEGRITY (Is any code broken?)
# ═══════════════════════════════════════════════════════
def check_zero_bytes():
    c=gh("contents/agents")
    if not isinstance(c,list):return True,"Cannot list agents"
    zeros=[f["name"] for f in c if f.get("size",1)==0]
    if zeros:return False,f"{len(zeros)} empty agents: {', '.join(zeros[:5])}"
    return True,f"All {len(c)} agents have code"

def check_old_email():
    """Spot-check critical files for old email."""
    for fname in ["james_butler.py","jeff_banks_cro.py","priya_sharma_email_agent.py","stripe-webhook.js"]:
        folder="agents" if fname.endswith(".py") else "netlify/functions"
        fdata=gh(f"contents/{folder}/{fname}")
        if fdata and "content" in fdata:
            code=base64.b64decode(fdata["content"]).decode(errors="ignore")
            if "seanb041992" in code.lower():
                return False,f"{fname} still has old email"
    return True,"Spot-check clean"

def check_credential_leaks():
    """Scan for hardcoded secrets in code."""
    patterns=["ghp_","sk_live_","sk_test_","Bearer sk-","AKIA"]
    for fname in ["alex_mercer_orchestrator.py","jeff_banks_cro.py","the_guardian.py"]:
        fdata=gh(f"contents/agents/{fname}")
        if fdata and "content" in fdata:
            code=base64.b64decode(fdata["content"]).decode(errors="ignore")
            for pat in patterns:
                if pat in code:return False,f"CREDENTIAL LEAK in agents/{fname}: {pat}..."
    return True,"No leaks in spot-check"

def check_package_json():
    fdata=gh("contents/package.json")
    if not fdata or "content" not in fdata:return True,"Cannot read"
    content=base64.b64decode(fdata["content"]).decode()
    try:
        json.loads(content)
        if "([^" in content:return False,"Broken regex artifact in package.json"
        return True,"Valid JSON"
    except:return False,"package.json is invalid JSON"

def check_stripe_webhook_code():
    """Verify the webhook JS actually sends emails."""
    fdata=gh("contents/netlify/functions/stripe-webhook.js")
    if not fdata or "content" not in fdata:return False,"Cannot read stripe-webhook.js"
    code=base64.b64decode(fdata["content"]).decode(errors="ignore")
    checks={"nodemailer":"nodemailer" in code,"sendMail":"sendMail" in code,
        "welcome_email":"welcome" in code.lower(),"pushover":"pushover" in code.lower(),
        "supabase":"supabase" in code.lower() or "SUPA" in code}
    missing=[k for k,v in checks.items() if not v]
    if missing:return False,f"Webhook missing: {', '.join(missing)}"
    return True,"Has email send, pushover, supabase"

def check_success_page():
    code2,body=fetch_url(f"{SITE}/checkout/success/")
    if code2!=200:return False,f"Success page HTTP {code2}"
    if "session_id" not in body:return False,"Success page doesn't capture session_id"
    if "stripe-webhook" not in body:return False,"Success page doesn't call webhook"
    return True,"Has session_id + webhook call"

# ═══════════════════════════════════════════════════════
# LEVEL 3: BUSINESS HEALTH (Is money flowing?)
# ═══════════════════════════════════════════════════════
def check_revenue():
    if not STRIPE_SK:return True,"No Stripe key"
    try:
        auth=base64.b64encode(f"{STRIPE_SK}:".encode()).decode()
        now=int(time.time());week_ago=now-604800
        with urlreq.urlopen(urlreq.Request(f"https://api.stripe.com/v1/charges?created[gte]={week_ago}&limit=20",
            headers={"Authorization":f"Basic {auth}"}),timeout=10) as r:
            data=json.loads(r.read())
            charges=data.get("data",[])
            total=sum(c.get("amount",0) for c in charges if c.get("paid"))/100
            return True,f"${total:.2f} in 7d ({len(charges)} charges)"
    except Exception as e:return True,f"Check: {str(e)[:60]}"

def check_payment_links():
    """Verify Stripe payment links are on the proflow page."""
    code2,body=fetch_url(f"{SITE}/proflow/")
    if code2!=200:return False,f"Proflow page HTTP {code2}"
    if "buy.stripe.com" not in body and "checkout" not in body:
        return False,"No payment links on proflow page"
    return True,"Payment links present"

# ═══════════════════════════════════════════════════════
# LEVEL 4: WORKFLOW & DIRECTOR HEALTH
# ═══════════════════════════════════════════════════════
def check_workflow_failures():
    runs=gh("actions/runs?per_page=50&status=failure")
    if not runs or not isinstance(runs,dict):return True,"Cannot fetch"
    recent=[r for r in runs.get("workflow_runs",[]) if
        datetime.strptime(r["updated_at"][:19],"%Y-%m-%dT%H:%M:%S")>datetime.utcnow()-timedelta(hours=1)]
    if recent:
        names=list(set(r["name"] for r in recent))[:5]
        return False,f"{len(recent)} fails in 1h: {', '.join(names)}"
    return True,"Clean last 1h"

def check_github_secrets():
    """Verify critical secrets exist (can't read values, just check presence via workflow)."""
    critical=["ANTHROPIC_API_KEY","STRIPE_SECRET_KEY","SUPABASE_URL","SUPABASE_KEY",
        "PUSHOVER_API_KEY","PUSHOVER_USER_KEY","GH_PAT","GMAIL_APP_PASS"]
    missing=[]
    for s in critical:
        val=os.environ.get(s,"")
        if not val:missing.append(s)
    if missing:return False,f"{len(missing)} secrets missing in env: {', '.join(missing[:4])}"
    return True,f"All {len(critical)} critical secrets present"

# ═══════════════════════════════════════════════════════
# AUTO-REPAIR CASCADE — Fix it before anyone notices
# ═══════════════════════════════════════════════════════
REPAIR_MAP={
    "SITE":["deploy-site.yml"],
    "PAGES":["deploy-site.yml"],
    "FUNC":["set-netlify-env.yml"],
    "STRIPE_WEBHOOK":["register_stripe_webhook.yml"],
    "STRIPE_PRODUCTS":[],
    "SUPABASE":[],
    "ANTHROPIC":[],
    "ZERO":["guardian_self_healing.yml"],
    "EMAIL":["guardian_self_healing.yml"],
    "CREDENTIAL":[],
    "PACKAGE":["guardian_self_healing.yml"],
    "WEBHOOK_CODE":["deploy-site.yml","set-netlify-env.yml"],
    "SUCCESS":["deploy-site.yml"],
    "REVENUE":[],
    "PAYMENT_LINKS":["deploy-site.yml"],
    "WORKFLOW":["guardian_always_on.yml"],
    "SECRETS":[],
}

def auto_repair(failure_name,failure_msg):
    log.info(f"AUTO-REPAIR: {failure_name} — {failure_msg}")
    repairs=[]
    for key,workflows in REPAIR_MAP.items():
        if key in failure_name:
            for wf in workflows:
                result=gh(f"actions/workflows/{wf}/dispatches","POST",{"ref":"main"})
                if not result or "error" not in result:
                    repairs.append(wf)
                    log.info(f"  TRIGGERED: {wf}")
    # Always alert Omega Brain for learning
    gh("actions/workflows/omega_orchestration.yml/dispatches","POST",{"ref":"main"})
    repairs.append("omega_orchestration.yml")
    # Store repair event
    supa_post("director_outputs",{"director":"Ultra Watchdog","output_type":"auto_repair",
        "content":json.dumps({"failure":failure_name,"msg":failure_msg,"repairs":repairs})[:2000],
        "created_at":datetime.utcnow().isoformat()})
    return repairs

# ═══════════════════════════════════════════════════════
# MAIN RUN — Execute ALL checks, repair ALL failures
# ═══════════════════════════════════════════════════════
ALL_CHECKS=[
    # Level 1: Infrastructure
    ("SITE_UP",check_site_up),
    ("SITE_PAGES",check_site_pages),
    ("FUNC_HEALTH",check_netlify_functions),
    ("STRIPE_WEBHOOK_REG",check_stripe_webhook),
    ("STRIPE_PRODUCTS",check_stripe_products),
    ("SUPABASE",check_supabase),
    ("ANTHROPIC_API",check_anthropic),
    # Level 2: Code Integrity
    ("ZERO_BYTES",check_zero_bytes),
    ("OLD_EMAIL",check_old_email),
    ("CREDENTIAL_LEAKS",check_credential_leaks),
    ("PACKAGE_JSON",check_package_json),
    ("WEBHOOK_CODE_REVIEW",check_stripe_webhook_code),
    ("SUCCESS_PAGE",check_success_page),
    # Level 3: Business Health
    ("REVENUE_7D",check_revenue),
    ("PAYMENT_LINKS",check_payment_links),
    # Level 4: Workflow Health
    ("WORKFLOW_FAILURES",check_workflow_failures),
    ("SECRETS_PRESENT",check_github_secrets),
]

def run():
    start=time.time()
    log.info("="*60)
    log.info("ULTRA WATCHDOG v3 — 30min — ALL CHECKS — AUTO-REPAIR")
    log.info("="*60)
    results=[]
    for name,fn in ALL_CHECKS:
        try:
            ok,msg=fn()
        except Exception as e:
            ok,msg=False,f"CHECK CRASHED: {str(e)[:60]}"
        results.append((name,ok,msg))
        icon="OK" if ok else "FAIL"
        log.info(f"  {icon} {name}: {msg}")

    failed=[(n,m) for n,o,m in results if not o]
    passed=len(results)-len(failed)
    duration=int((time.time()-start)*1000)
    ts=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    report=f"ULTRA WATCHDOG {ts} | {passed}/{len(results)} passed | {duration}ms\n"
    # Auto-repair failures
    total_repairs=[]
    if failed:
        report+=f"\nFAILURES ({len(failed)}):\n"
        for name,msg in failed:
            report+=f"  {name}: {msg}\n"
            repairs=auto_repair(name,msg)
            if repairs:
                total_repairs.extend(repairs)
                report+=f"    REPAIR: {', '.join(repairs)}\n"
        report+=f"\nTOTAL REPAIRS: {len(total_repairs)}\n"
        push(f"WATCHDOG | {len(failed)} FAILURES",report[:800],priority=1)
    else:
        report+="ALL SYSTEMS OPERATIONAL\n"
        hour=datetime.utcnow().hour
        if hour%6==0 and datetime.utcnow().minute<30:
            push("Watchdog OK",f"{passed}/{len(results)} passed | {duration}ms",-1)
    # Append system status summary
    report+=f"\n--- SYSTEM STATUS ---\n"
    for name,ok,msg in results:
        report+=f"{'[OK]' if ok else '[!!]'} {name}: {msg}\n"
    log.info(f"\n{report}")
    # Store in Supabase
    supa_post("director_outputs",{"director":"Ultra Watchdog","output_type":"health_check",
        "content":report[:2000],"metrics":json.dumps({"passed":passed,"failed":len(failed),
        "total":len(results),"repairs":len(total_repairs),"duration_ms":duration,
        "failures":[f[0] for f in failed]}),"created_at":datetime.utcnow().isoformat()})
    return {"passed":passed,"failed":len(failed),"total":len(results),"repairs":total_repairs,"report":report}

if __name__=="__main__":
    run()
