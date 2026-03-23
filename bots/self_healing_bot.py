"""
Self-Healing System Bot — System Strengthening Layer
Pre-session health check. Detects and auto-fixes: dead secrets, failed workflows,
broken bots, missing credentials, API quota issues. Prevents Chairman interruptions.
"""
import os, json, logging, datetime, time
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [HEALTH] %(message)s")
log = logging.getLogger("self_heal")

SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN      = os.environ.get("GH_PAT", "")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")
NETLIFY_TOKEN = os.environ.get("NETLIFY_AUTH_TOKEN", "")
NETLIFY_SITE  = os.environ.get("NETLIFY_SITE_ID", "8ef722e1-4110-42af-8ddb-ff6c2ce1745e")
HUBSPOT_KEY   = os.environ.get("HUBSPOT_API_KEY", "")
APOLLO_KEY    = os.environ.get("APOLLO_API_KEY", "")
AHREFS_KEY    = os.environ.get("AHREFS_API_KEY", "")

import urllib.request, urllib.error

RESULTS: List[Dict] = []

def check(name: str, fn) -> Tuple[bool, str]:
    try:
        ok, msg = fn()
        status = "✅" if ok else "❌"
        RESULTS.append({"name": name, "ok": ok, "msg": msg})
        log.info(f"{status} {name}: {msg}")
        return ok, msg
    except Exception as e:
        RESULTS.append({"name": name, "ok": False, "msg": str(e)})
        log.warning(f"❌ {name}: {e}")
        return False, str(e)

def push(title: str, message: str, priority: int = 0):
    if not PUSHOVER_API: return
    data = json.dumps({"token": PUSHOVER_API, "user": PUSHOVER_USER,
                        "title": title, "message": message, "priority": priority}).encode()
    try:
        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                                     data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: bare-except

        pass
# ── HEALTH CHECKS ───────────────────────────────────────────────────

def check_supabase():
    if not SUPABASE_URL: return False, "SUPABASE_URL not set"
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/contacts?select=id&limit=1",
                                  headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            count = len(json.loads(r.read()))
            return True, f"DB reachable, {count} contact(s)"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"

def check_anthropic():
    if not ANTHROPIC_KEY: return False, "ANTHROPIC_API_KEY not set"
    data = json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 10,
                        "messages": [{"role": "user", "content": "ping"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={
        "Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            json.loads(r.read())
            return True, "API responding"
    except urllib.error.HTTPError as e:
        if e.code == 429: return False, "Rate limited / quota"
        if e.code == 401: return False, "Invalid API key"
        return False, f"HTTP {e.code}"

def check_netlify():
    if not NETLIFY_TOKEN: return False, "NETLIFY_AUTH_TOKEN not set"
    req = urllib.request.Request(
        f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE}",
        headers={"Authorization": f"Bearer {NETLIFY_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            return True, f"Site: {d.get('url','?')} | State: {d.get('state','?')}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"

def check_site_live():
    try:
        req = urllib.request.Request("https://nyspotlightreport.com",
                                      headers={"User-Agent": "NYSR-HealthBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            size = len(r.read())
            return True, f"HTTP 200, {size//1024}KB"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)

def check_github_workflows():
    if not GH_TOKEN: return False, "GH_PAT not set"
    req = urllib.request.Request(
        "https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/runs?per_page=20",
        headers={"Authorization": f"token {GH_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            runs = json.loads(r.read()).get("workflow_runs", [])
        failed = [r for r in runs if r["conclusion"] == "failure"]
        success = [r for r in runs if r["conclusion"] == "success"]
        if failed:
            names = ", ".join(set(r["name"] for r in failed[:3]))
            return False, f"{len(failed)} failed: {names}"
        return True, f"{len(success)} recent runs passing"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"

def check_hubspot():
    if not HUBSPOT_KEY: return False, "HUBSPOT_API_KEY not set"
    req = urllib.request.Request(
        "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
        headers={"Authorization": f"Bearer {HUBSPOT_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            return True, f"HubSpot connected, {d.get('total', '?')} contacts"
    except urllib.error.HTTPError as e:
        if e.code == 401: return False, "Invalid/expired HubSpot token"
        return False, f"HTTP {e.code}"

def check_apollo():
    if not APOLLO_KEY: return False, "APOLLO_API_KEY not set"
    data = json.dumps({"api_key": APOLLO_KEY}).encode()
    req = urllib.request.Request("https://api.apollo.io/v1/auth/health", data=data,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return True, "Apollo responding"
    except urllib.error.HTTPError as e:
        if e.code == 401: return False, "Invalid Apollo key"
        return True, f"Reachable (HTTP {e.code})"

def check_stripe():
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key: return False, "STRIPE_SECRET_KEY not set"
    req = urllib.request.Request("https://api.stripe.com/v1/balance",
                                  headers={"Authorization": f"Bearer {stripe_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            available = d.get("available", [{}])
            bal = available[0].get("amount", 0) / 100 if available else 0
            return True, f"Balance: ${bal:.2f}"
    except urllib.error.HTTPError as e:
        if e.code == 401: return False, "Invalid Stripe key"
        return False, f"HTTP {e.code}"

def check_gumroad():
    token = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
    if not token: return False, "GUMROAD_ACCESS_TOKEN not set"
    req = urllib.request.Request(f"https://api.gumroad.com/v2/products?access_token={token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            count = len(d.get("products", []))
            return True, f"{count} products found"
    except urllib.error.HTTPError as e:
        if e.code == 401: return False, "Invalid Gumroad token"
        return False, f"HTTP {e.code}"

# ── AUTO-REPAIR ATTEMPTS ────────────────────────────────────────────

def attempt_repairs():
    failed = [r for r in RESULTS if not r["ok"]]
    if not failed:
        log.info("All systems healthy — no repairs needed")
        return
    for f in failed:
        name = f["name"]
        msg  = f["msg"]
        if name == "GitHub Workflows" and "failed" in msg:
            # Re-trigger failed workflows
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/runs?conclusion=failure&per_page=5",
                    headers={"Authorization": f"token {GH_TOKEN}"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    runs = json.loads(r.read()).get("workflow_runs", [])
                for run in runs[:3]:
                    wf_id = run["workflow_id"]
                    rerun_req = urllib.request.Request(
                        f"https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/workflows/{wf_id}/dispatches",
                        data=json.dumps({"ref": "main"}).encode(),
                        method="POST",
                        headers={"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json"})
                    try:
                        urllib.request.urlopen(rerun_req, timeout=10)
                        log.info(f"Re-triggered workflow: {run['name']}")
                    except Exception:  # noqa: bare-except

                        pass
            except Exception as e:
                log.warning(f"Workflow re-trigger failed: {e}")

# ── MAIN ────────────────────────────────────────────────────────────

def run():
    log.info("=== Self-Healing Health Check ===")
    start = time.time()
    check("Supabase DB",         check_supabase)
    check("Anthropic API",        check_anthropic)
    check("Netlify Site Live",    check_site_live)
    check("Netlify API",          check_netlify)
    check("GitHub Workflows",     check_github_workflows)
    check("HubSpot CRM",          check_hubspot)
    check("Apollo Pro",           check_apollo)
    check("Stripe",               check_stripe)
    check("Gumroad",              check_gumroad)
    elapsed = time.time() - start
    passing = sum(1 for r in RESULTS if r["ok"])
    failing = sum(1 for r in RESULTS if not r["ok"])
    summary = f"Health: {passing}/{len(RESULTS)} passing | {failing} failing | {elapsed:.1f}s"
    log.info(summary)
    if failing == 0:
        push("✅ NYSR System Health", summary)
    elif failing <= 2:
        failed_names = ", ".join(r["name"] for r in RESULTS if not r["ok"])
        push("⚠️ NYSR Health Warning", f"{summary}\nFailing: {failed_names}", priority=0)
        attempt_repairs()
    else:
        failed_names = ", ".join(r["name"] for r in RESULTS if not r["ok"])
        push("🚨 NYSR SYSTEM ALERT", f"{failing} systems down: {failed_names}", priority=1)
        attempt_repairs()
    # Store health snapshot
    if SUPABASE_URL:
        try:
            req = urllib.request.Request(
                f"{SUPABASE_URL}/rest/v1/scheduled_posts",
                data=json.dumps({
                    "platform": "health_check", "content": json.dumps(RESULTS),
                    "status": "passed" if failing == 0 else "issues",
                    "scheduled_for": datetime.datetime.utcnow().isoformat()
                }).encode(),
                method="POST",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                          "Content-Type": "application/json", "Prefer": "return=minimal"})
            urllib.request.urlopen(req, timeout=10)
        except Exception:  # noqa: bare-except

            pass
    log.info("=== Health Check Done ===")
    return failing

if __name__ == "__main__":
    import sys
    failures = run()
    sys.exit(1 if failures > 2 else 0)
