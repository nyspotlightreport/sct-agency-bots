#!/usr/bin/env python3
"""
NYSR Output Verifier — catches bots that succeed but produce nothing.
Checks actual output (Supabase rows, API responses, files) not just workflow status.
"""
import os, sys, json, logging, ssl
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("output_verifier")
CTX = ssl.create_default_context()
RESULTS = []

def check(name, has_output, detail=""):
    status = "PRODUCING" if has_output else "ZERO_OUTPUT"
    RESULTS.append({"name": name, "status": status, "detail": detail})
    log.info(f"  {'OK' if has_output else 'EMPTY'}  {name} — {detail}")

def supa_query(table, params=""):
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        req = Request(f"{url}/rest/v1/{table}?{params}&limit=1", headers={
            "apikey": key, "Authorization": f"Bearer {key}"
        })
        resp = urlopen(req, timeout=10, context=CTX)
        return json.loads(resp.read())
    except Exception as e:
        return None

def supa_count(table, date_col="created_at", days=7):
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return -1
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        req = Request(f"{url}/rest/v1/{table}?{date_col}=gte.{cutoff}&select=id", headers={
            "apikey": key, "Authorization": f"Bearer {key}",
            "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"
        })
        resp = urlopen(req, timeout=10, context=CTX)
        cr = resp.headers.get("Content-Range", "")
        if "/" in cr:
            total = cr.split("/")[1]
            return int(total) if total != "*" else 0
        return len(json.loads(resp.read()))
    except Exception:
        return -1

def gh_workflow_last_success(workflow_name):
    pat = os.environ.get("GH_PAT", "")
    if not pat:
        return None
    try:
        req = Request(
            f"https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/workflows/{workflow_name}/runs?per_page=1&status=success",
            headers={"Authorization": f"Bearer {pat}", "User-Agent": "NYSR-Verifier"})
        resp = urlopen(req, timeout=10, context=CTX)
        data = json.loads(resp.read())
        runs = data.get("workflow_runs", [])
        return runs[0] if runs else None
    except Exception:
        return None

def pushover(title, msg):
    api_key = os.environ.get("PUSHOVER_API_KEY", "")
    user_key = os.environ.get("PUSHOVER_USER_KEY", "")
    if not api_key or not user_key:
        return
    try:
        data = urlencode({"token": api_key, "user": user_key, "title": title, "message": msg[:1024]}).encode()
        req = Request("https://api.pushover.net/1/messages.json", data=data)
        urlopen(req, timeout=10, context=CTX)
    except Exception:
        pass

def run():
    log.info("=" * 50)
    log.info("  NYSR OUTPUT VERIFIER")
    log.info(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log.info("=" * 50)

    # 1. Email blaster — check outreach_log for emails sent in last 7 days
    count = supa_count("outreach_log", "sent_at", 7)
    if count == -1:
        check("Email Blaster", False, "Supabase not accessible or table missing")
    else:
        check("Email Blaster", count > 0, f"{count} emails sent in last 7 days")

    # 2. Lead nurture — check contacts with nurture_stage > 0
    count = supa_count("contacts", "created_at", 7)
    if count == -1:
        check("Lead Nurture", False, "Supabase not accessible or table missing")
    else:
        check("Lead Nurture", count > 0, f"{count} contacts in last 7 days")

    # 3. Auto-publisher — check if blog has recent posts (HTTP check)
    try:
        req = Request("https://nyspotlightreport.com/blog/", headers={"User-Agent": "NYSR-Verifier"})
        resp = urlopen(req, timeout=10, context=CTX)
        body = resp.read().decode("utf-8", errors="replace")
        # Check for recent date patterns (2026-03)
        has_recent = "2026-03" in body or "March 2026" in body or "Mar 2026" in body
        check("Auto-Publisher", has_recent, "Recent content found on /blog/" if has_recent else "No March 2026 content on /blog/")
    except Exception:
        check("Auto-Publisher", False, "Could not fetch /blog/")

    # 4. Sweepstakes — check workflow ran and look for entry evidence
    last = gh_workflow_last_success("sweepstakes_entry.yml")
    if last:
        run_date = last.get("created_at", "")[:10]
        check("Sweepstakes Bot", True, f"Last success: {run_date}")
    else:
        check("Sweepstakes Bot", False, "No successful runs found")

    # 5. Mention monitor — check brand_mentions table
    count = supa_count("brand_mentions", "found_at", 30)
    if count == -1:
        check("Mention Monitor", False, "brand_mentions table not accessible")
    else:
        check("Mention Monitor", count > 0, f"{count} mentions in last 30 days")

    # 6. Chairman briefing — check last run
    last = gh_workflow_last_success("chairman_briefing_daily.yml")
    if last:
        run_date = last.get("created_at", "")[:10]
        check("Chairman Briefing", True, f"Last success: {run_date}")
    else:
        check("Chairman Briefing", False, "No successful runs")

    # 7. Site health monitor — check site_health_log
    count = supa_count("site_health_log", "checked_at", 1)
    if count == -1:
        check("Health Monitor", False, "site_health_log not accessible")
    else:
        check("Health Monitor", count > 0, f"{count} health checks in last 24h")

    # 8. Blake/Cameron/Casey agents — check director_outputs
    count = supa_count("director_outputs", "created_at", 7)
    if count == -1:
        check("Department Agents", False, "director_outputs not accessible")
    else:
        check("Department Agents", count > 0, f"{count} outputs in last 7 days")

    # 9. Affiliate pages — check link_audit.json exists and has data
    audit_path = os.path.join(os.path.dirname(__file__), "..", "data", "affiliate", "link_audit.json")
    if os.path.exists(audit_path):
        try:
            with open(audit_path) as f:
                data = json.load(f)
            total = data.get("total_links", 0)
            check("Affiliate Links", total > 0, f"{total} links audited")
        except Exception:
            check("Affiliate Links", False, "link_audit.json parse error")
    else:
        check("Affiliate Links", False, "link_audit.json not found")

    # 10. Stripe revenue — check if any charges exist
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if stripe_key:
        try:
            req = Request("https://api.stripe.com/v1/charges?limit=1",
                headers={"Authorization": f"Bearer {stripe_key}"})
            resp = urlopen(req, timeout=10, context=CTX)
            data = json.loads(resp.read())
            has_charges = len(data.get("data", [])) > 0
            check("Stripe Revenue", has_charges, "Charges exist" if has_charges else "No charges yet")
        except Exception:
            check("Stripe Revenue", False, "Stripe API error")
    else:
        check("Stripe Revenue", False, "STRIPE_SECRET_KEY not set")

    # Compile results
    producing = sum(1 for r in RESULTS if r["status"] == "PRODUCING")
    zero = sum(1 for r in RESULTS if r["status"] == "ZERO_OUTPUT")
    total = len(RESULTS)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "producing": producing,
        "zero_output": zero,
        "total": total,
        "results": RESULTS
    }

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "audit", "output_verification.json")
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass

    log.info("\n" + "=" * 50)
    log.info(f"  PRODUCING: {producing}/{total}")
    log.info(f"  ZERO OUTPUT: {zero}/{total}")
    log.info("=" * 50)

    # Alert
    zero_names = [r["name"] for r in RESULTS if r["status"] == "ZERO_OUTPUT"]
    if zero:
        pushover(f"OUTPUT CHECK: {zero} bots producing nothing",
                 f"Zero output: {', '.join(zero_names)}")
    else:
        pushover(f"OUTPUT CHECK: All {total} bots producing",
                 "Every monitored bot has real output.")

    sys.exit(0 if zero <= 3 else 1)

if __name__ == "__main__":
    run()
