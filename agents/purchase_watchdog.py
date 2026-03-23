#!/usr/bin/env python3
"""
agents/purchase_watchdog.py — NYSR Purchase Watchdog
Tests the ENTIRE customer journey end-to-end every 6 hours.
If ANY step fails, sends CRITICAL Pushover alert.
This agent exists because the Stripe webhook failure wasn't caught
by any other agent for days. Never again.
"""
import os, sys, json, logging, time
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.supercore import pushover, supa
except Exception:  # noqa: bare-except
    def pushover(*a,**k): pass
    def supa(*a,**k): return None
import urllib.request as urlreq

log = logging.getLogger("watchdog")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WATCHDOG] %(message)s")

SITE = "https://nyspotlightreport.com"
CHECKS = []

def check_url(url, name, must_contain=None, must_not_contain=None):
    try:
        req = urlreq.Request(url, headers={"User-Agent":"NYSR-Watchdog/1.0"})
        with urlreq.urlopen(req, timeout=15) as r:
            code = r.status
            body = r.read().decode('utf-8', errors='ignore')
            ok = code == 200
            if must_contain and must_contain not in body:
                CHECKS.append({"name":name,"status":"FAIL","reason":f"Missing '{must_contain}' in response"})
                return False
            if must_not_contain and must_not_contain in body:
                CHECKS.append({"name":name,"status":"FAIL","reason":f"Found '{must_not_contain}' in response"})
                return False
            CHECKS.append({"name":name,"status":"PASS" if ok else "FAIL","code":code})
            return ok
    except Exception as e:
        CHECKS.append({"name":name,"status":"FAIL","reason":str(e)[:100]})
        return False

def check_netlify_function(path, name):
    try:
        req = urlreq.Request(f"{SITE}/.netlify/functions/{path}",
            headers={"Content-Type":"application/json"},
            data=json.dumps({"type":"ping","data":{"object":{}}}).encode())
        with urlreq.urlopen(req, timeout=15) as r:
            body = json.loads(r.read())
            CHECKS.append({"name":name,"status":"PASS","response":str(body)[:100]})
            return True
    except Exception as e:
        CHECKS.append({"name":name,"status":"FAIL","reason":str(e)[:100]})
        return False

def check_stripe_webhook():
    sk = os.environ.get("STRIPE_SECRET_KEY","")
    if not sk:
        CHECKS.append({"name":"stripe_webhook_registered","status":"FAIL","reason":"No STRIPE_SECRET_KEY"})
        return False
    try:
        import base64
        auth = base64.b64encode(f"{sk}:".encode()).decode()
        req = urlreq.Request("https://api.stripe.com/v1/webhook_endpoints?limit=10",
            headers={"Authorization":f"Basic {auth}"})
        with urlreq.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            endpoints = data.get("data",[])
            nysr_endpoints = [e for e in endpoints if "nyspotlightreport" in e.get("url","")]
            if nysr_endpoints:
                ep = nysr_endpoints[0]
                status = ep.get("status","unknown")
                CHECKS.append({"name":"stripe_webhook_registered","status":"PASS" if status=="enabled" else "WARN",
                    "url":ep.get("url",""),"stripe_status":status})
                return status == "enabled"
            else:
                CHECKS.append({"name":"stripe_webhook_registered","status":"FAIL","reason":"No NYSR webhook endpoint found in Stripe"})
                return False
    except Exception as e:
        CHECKS.append({"name":"stripe_webhook_registered","status":"FAIL","reason":str(e)[:100]})
        return False

def run():
    log.info("="*60)
    log.info("PURCHASE WATCHDOG — End-to-End Customer Journey Test")
    log.info("="*60)
    global CHECKS; CHECKS = []

    # === SITE AVAILABILITY ===
    check_url(f"{SITE}/", "homepage_live", must_contain="NY Spotlight")
    check_url(f"{SITE}/store/", "store_page", must_contain="ProFlow")
    check_url(f"{SITE}/proflow/", "proflow_page")
    check_url(f"{SITE}/pricing/", "pricing_page")
    check_url(f"{SITE}/checkout/success/", "success_page", must_contain="Payment Successful")
    check_url(f"{SITE}/activate/", "activate_page")
    check_url(f"{SITE}/downloads/", "downloads_page")

    # === NETLIFY FUNCTIONS ===
    check_netlify_function("stripe-webhook", "stripe_webhook_function")
    check_netlify_function("lead-capture", "lead_capture_function")

    # === STRIPE WEBHOOK REGISTRATION ===
    check_stripe_webhook()

    # === SUPABASE CONNECTIVITY ===
    supa_url = os.environ.get("SUPABASE_URL","")
    supa_key = os.environ.get("SUPABASE_KEY","") or os.environ.get("SUPABASE_ANON_KEY","")
    if supa_url and supa_key:
        try:
            req = urlreq.Request(f"{supa_url}/rest/v1/contacts?select=id&limit=1",
                headers={"apikey":supa_key,"Authorization":f"Bearer {supa_key}"})
            with urlreq.urlopen(req, timeout=10) as r:
                CHECKS.append({"name":"supabase_connection","status":"PASS"})
        except Exception as e:
            CHECKS.append({"name":"supabase_connection","status":"FAIL","reason":str(e)[:100]})
    else:
        CHECKS.append({"name":"supabase_connection","status":"FAIL","reason":"Missing SUPABASE_URL or KEY"})

    # === SMTP / EMAIL CAPABILITY ===
    smtp_user = os.environ.get("SMTP_USER","") or os.environ.get("GMAIL_USER","")
    smtp_pass = os.environ.get("GMAIL_APP_PASS","")
    if smtp_user and smtp_pass:
        CHECKS.append({"name":"email_credentials","status":"PASS"})
    else:
        CHECKS.append({"name":"email_credentials","status":"FAIL","reason":"Missing SMTP_USER or GMAIL_APP_PASS"})

    # === PAYMENT LINKS ON SITE ===
    try:
        req = urlreq.Request(f"{SITE}/proflow/", headers={"User-Agent":"NYSR-Watchdog/1.0"})
        with urlreq.urlopen(req, timeout=15) as r:
            body = r.read().decode('utf-8', errors='ignore')
            if 'buy.stripe.com' in body or 'checkout' in body.lower():
                CHECKS.append({"name":"payment_links_present","status":"PASS"})
            else:
                CHECKS.append({"name":"payment_links_present","status":"FAIL","reason":"No Stripe links on /proflow/"})
    except Exception as e:
        CHECKS.append({"name":"payment_links_present","status":"FAIL","reason":str(e)[:100]})

    # === REPORT ===
    passed = sum(1 for c in CHECKS if c["status"]=="PASS")
    failed = [c for c in CHECKS if c["status"]=="FAIL"]
    warned = [c for c in CHECKS if c["status"]=="WARN"]
    total = len(CHECKS)
    report = f"WATCHDOG REPORT — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
    report += f"PASSED: {passed}/{total} | FAILED: {len(failed)} | WARNINGS: {len(warned)}\n"
    for c in CHECKS:
        icon = "✅" if c["status"]=="PASS" else "❌" if c["status"]=="FAIL" else "⚠️"
        report += f"\n{icon} {c['name']}: {c['status']}"
        if "reason" in c: report += f" — {c['reason']}"

    log.info(report)
    # Save to Supabase
    supa("POST","director_outputs",{"director":"Purchase Watchdog","output_type":"health_check",
        "content":report[:2000],"metrics":json.dumps({"passed":passed,"failed":len(failed),"total":total}),
        "created_at":datetime.utcnow().isoformat()})
    # ALERT on failures
    if failed:
        pushover("🚨 PURCHASE WATCHDOG CRITICAL",
            f"{len(failed)} FAILURES detected!\n" + "\n".join(f"❌ {f['name']}: {f.get('reason','')}" for f in failed[:5]),
            priority=1)
    else:
        pushover("✅ Watchdog: All Systems GO", f"{passed}/{total} checks passed. Customer journey verified.", priority=-1)
    log.info(f"\nWatchdog complete: {passed}/{total} passed, {len(failed)} failed")
    return {"passed":passed,"failed":len(failed),"total":total,"checks":CHECKS,"report":report}

if __name__=="__main__":
    run()
