#!/usr/bin/env python3
"""
agents/effectiveness_auditor.py - Effectiveness Auditor
Runs daily BEFORE Chairman briefing. Checks BUSINESS OUTCOMES not just existence.
8 checks: affiliate coverage, editorial purity, smoke tests, stub agents,
workflow success, revenue touchpoints, content freshness, data growth.
"""
import os, json, logging, glob, re, time
from datetime import datetime, timedelta, timezone
import urllib.request as urlreq
import urllib.parse

log = logging.getLogger("effectiveness")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [EFFECTIVENESS] %(message)s")

SITE = "https://nyspotlightreport.com"
GH_PAT = os.environ.get("GH_PAT", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
AFFILIATE_TAG = "nyspotlightrepo-20"
PROFLOW_KEYWORDS = ["ProFlow", "proflow", "myproflow", "Start Free Trial", "Get Started Free"]

ALERTS = []
RESULTS = {}


def pushover(title, message, priority=1):
    if not PUSH_API or not PUSH_USER:
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_API, "user": PUSH_USER,
            "title": title, "message": message[:500], "priority": priority
        }).encode()
        urlreq.urlopen(urlreq.Request(
            "https://api.pushover.net/1/messages.json", data=data), timeout=10)
    except Exception as e:
        log.error("Pushover failed: %s", e)


def fetch_url(url, timeout=15):
    try:
        req = urlreq.Request(url, headers={"User-Agent": "NYSR-Auditor/1.0"})
        with urlreq.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def gh_api(endpoint):
    if not GH_PAT:
        return {}
    try:
        req = urlreq.Request(
            "https://api.github.com/" + endpoint,
            headers={"Authorization": "Bearer " + GH_PAT,
                     "Accept": "application/vnd.github.v3+json"}
        )
        with urlreq.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning("GitHub API failed for %s: %s", endpoint, e)
        return {}


def supa_count(table):
    if not SUPA_URL:
        return -1
    try:
        url = SUPA_URL + "/rest/v1/" + table + "?select=id"
        req = urlreq.Request(url, headers={
            "apikey": SUPA_KEY, "Authorization": "Bearer " + SUPA_KEY,
            "Prefer": "count=exact", "Range": "0-0"
        })
        with urlreq.urlopen(req, timeout=10) as r:
            cr = r.headers.get("Content-Range", "")
            if "/" in cr:
                return int(cr.split("/")[1])
        return 0
    except:
        return -1


def check_affiliate_coverage():
    log.info("CHECK 1: Affiliate Coverage")
    status, html = fetch_url(SITE + "/blog/")
    if status != 200:
        RESULTS["affiliate_coverage"] = {"status": "ERROR", "detail": "Blog returned " + str(status)}
        return
    links = list(set(re.findall(r'href="(/blog/[^"]+/)"', html)))[:30]
    total = len(links)
    with_aff = 0
    missing = []
    for link in links[:20]:
        s, body = fetch_url(SITE + link)
        if s == 200 and AFFILIATE_TAG in body:
            with_aff += 1
        elif s == 200:
            missing.append(link)
        time.sleep(0.3)
    checked = min(20, total)
    pct = (with_aff / checked * 100) if checked > 0 else 0
    RESULTS["affiliate_coverage"] = {
        "status": "PASS" if pct >= 80 else "FAIL",
        "coverage_pct": round(pct, 1), "checked": checked,
        "with_affiliate": with_aff, "missing_sample": missing[:5]
    }
    if pct < 80:
        ALERTS.append("AFFILIATE COVERAGE LOW: %.0f%% (%d/%d)" % (pct, with_aff, checked))
    log.info("  Affiliate: %.1f%% (%d/%d)", pct, with_aff, checked)


def check_editorial_purity():
    log.info("CHECK 2: Editorial Purity")
    status, html = fetch_url(SITE + "/blog/")
    if status != 200:
        RESULTS["editorial_purity"] = {"status": "ERROR"}
        return
    links = list(set(re.findall(r'href="(/blog/[^"]+/)"', html)))[:10]
    violations = []
    for link in links:
        s, body = fetch_url(SITE + link)
        if s != 200:
            continue
        for kw in PROFLOW_KEYWORDS:
            if kw.lower() in body.lower():
                violations.append({"page": link, "keyword": kw})
                break
        time.sleep(0.3)
    RESULTS["editorial_purity"] = {
        "status": "PASS" if len(violations) == 0 else "FAIL",
        "checked": len(links), "violations": len(violations), "details": violations[:5]
    }
    if violations:
        ALERTS.append("EDITORIAL PURITY: %d pages have SaaS content!" % len(violations))
    log.info("  Purity: %d/%d clean", len(links) - len(violations), len(links))


def check_smoke_tests():
    log.info("CHECK 3: Smoke Test Pass Rate")
    data = gh_api("repos/nyspotlightreport/NY-Spotlight-Report-good/actions/runs?per_page=20")
    runs = data.get("workflow_runs", [])
    smoke = [r for r in runs if "smoke" in r.get("name", "").lower()][:10]
    passed = sum(1 for r in smoke if r.get("conclusion") == "success")
    total = len(smoke)
    RESULTS["smoke_tests"] = {
        "status": "PASS" if total > 0 and passed == total else "WARN",
        "passed": passed, "total": total
    }
    if total > 0 and passed < total:
        ALERTS.append("SMOKE TESTS: %d/%d passed" % (passed, total))
    log.info("  Smoke: %d/%d passed", passed, total)


def check_agent_stubs():
    log.info("CHECK 4: Agent Stub Detection")
    agents_dir = os.path.dirname(os.path.abspath(__file__))
    stubs = []
    total = 0
    for f in glob.glob(os.path.join(agents_dir, "*.py")):
        if "__init__" in f:
            continue
        total += 1
        with open(f) as fh:
            lines = len(fh.readlines())
        if lines < 50:
            stubs.append({"file": os.path.basename(f), "lines": lines})
    RESULTS["agent_stubs"] = {
        "status": "PASS" if len(stubs) == 0 else "WARN",
        "total_agents": total, "stubs": len(stubs), "stub_list": stubs
    }
    if stubs:
        names = ", ".join(s["file"] for s in stubs[:5])
        ALERTS.append("STUB AGENTS: %d under 50 lines: %s" % (len(stubs), names))
    log.info("  Stubs: %d/%d are stubs", len(stubs), total)


def check_workflow_success():
    log.info("CHECK 5: Workflow Success Rate (24h)")
    data = gh_api("repos/nyspotlightreport/sct-agency-bots/actions/runs?per_page=50")
    runs = data.get("workflow_runs", [])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    recent = [r for r in runs if r.get("created_at", "") > cutoff and r.get("status") == "completed"]
    passed = sum(1 for r in recent if r.get("conclusion") == "success")
    failed = [r.get("name", "?") for r in recent if r.get("conclusion") == "failure"]
    total = len(recent)
    pct = (passed / total * 100) if total > 0 else 0
    RESULTS["workflow_success"] = {
        "status": "PASS" if pct >= 90 else "WARN" if pct >= 70 else "FAIL",
        "success_rate": round(pct, 1), "passed": passed, "total": total,
        "failures": failed[:10]
    }
    if failed:
        ALERTS.append("WORKFLOW FAILURES: " + ", ".join(failed[:5]))
    log.info("  Workflows: %d/%d (%.1f%%)", passed, total, pct)


def check_revenue_touchpoints():
    log.info("CHECK 6: Revenue Touchpoints")
    checks = {
        "homepage": (SITE + "/", 200),
        "store": (SITE + "/store/", 200),
        "checkout_success": (SITE + "/checkout/success/", 200),
        "subscribe_api": (SITE + "/.netlify/functions/subscribe", 405),
    }
    results = {}
    down = []
    for name, (url, expected) in checks.items():
        status, _ = fetch_url(url)
        ok = status == expected
        results[name] = {"status": status, "ok": ok}
        if not ok:
            down.append("%s (%d)" % (name, status))
    RESULTS["revenue_touchpoints"] = {
        "status": "PASS" if len(down) == 0 else "FAIL",
        "checks": results, "down": down
    }
    if down:
        ALERTS.append("REVENUE DOWN: " + ", ".join(down))
    log.info("  Revenue: %d/%d up", len(checks) - len(down), len(checks))


def check_content_freshness():
    log.info("CHECK 7: Content Freshness")
    data = gh_api("repos/nyspotlightreport/sct-agency-bots/actions/workflows/auto_publish_daily.yml/runs?per_page=5")
    runs = data.get("workflow_runs", [])
    last_success = None
    for r in runs:
        if r.get("conclusion") == "success":
            last_success = r.get("created_at", "")
            break
    stale = True
    if last_success:
        try:
            last_dt = datetime.fromisoformat(last_success.replace("Z", "+00:00"))
            stale = (datetime.now(timezone.utc) - last_dt) > timedelta(hours=48)
        except Exception as _silent_e:
            import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)
    RESULTS["content_freshness"] = {
        "status": "PASS" if not stale else "WARN",
        "last_publish_success": last_success or "NEVER", "stale": stale
    }
    if stale:
        ALERTS.append("CONTENT STALE: No auto-publish success in 48h")
    log.info("  Freshness: %s", "FRESH" if not stale else "STALE")


def check_data_growth():
    log.info("CHECK 8: Supabase Data Growth")
    tables = ["contacts", "outreach_log", "brand_mentions", "subscribers"]
    counts = {}
    for table in tables:
        counts[table] = supa_count(table)
    history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "data", "audits", "data_growth_history.json")
    yesterday = {}
    try:
        with open(history_file) as f:
            yesterday = json.load(f)
    except Exception as _silent_e:
        import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)
    try:
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w") as f:
            json.dump(counts, f)
    except Exception as _silent_e:
        import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)
    growth = {}
    for t in tables:
        p, c = yesterday.get(t, 0), counts[t]
        growth[t] = c - p if c >= 0 and p >= 0 else "unknown"
    RESULTS["data_growth"] = {
        "status": "PASS" if counts.get("contacts", 0) > 0 else "WARN",
        "current_counts": counts, "growth_24h": growth
    }
    if counts.get("contacts", 0) == 0:
        ALERTS.append("DATA: contacts table empty - outreach may be broken")
    log.info("  Data: %s", json.dumps(counts))


def main():
    now = datetime.now(timezone.utc)
    log.info("=== Effectiveness Auditor - %s ===", now.strftime("%Y-%m-%d %H:%M UTC"))

    check_affiliate_coverage()
    check_editorial_purity()
    check_smoke_tests()
    check_agent_stubs()
    check_workflow_success()
    check_revenue_touchpoints()
    check_content_freshness()
    check_data_growth()

    checks = list(RESULTS.values())
    passed = sum(1 for c in checks if c.get("status") == "PASS")
    total = len(checks)
    score = round(passed / total * 100) if total > 0 else 0

    RESULTS["_summary"] = {
        "timestamp": now.isoformat(), "score": score,
        "passed": passed, "total": total, "alerts": len(ALERTS)
    }

    audit_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "data", "audits")
    os.makedirs(audit_dir, exist_ok=True)
    audit_file = os.path.join(audit_dir,
                              "effectiveness_" + now.strftime("%Y-%m-%d") + ".json")
    with open(audit_file, "w") as f:
        json.dump(RESULTS, f, indent=2)
    log.info("Results saved to %s", audit_file)

    if ALERTS:
        alert_msg = "Score: %d%%\n\n" % score + "\n".join("!! " + a for a in ALERTS)
        pushover("Effectiveness Audit", alert_msg, priority=1)
        log.warning("ALERTS:\n%s", "\n".join(ALERTS))
    else:
        log.info("ALL CLEAR - Score: %d%% (%d/%d)", score, passed, total)

    log.info("=== Effectiveness Auditor complete ===")


if __name__ == "__main__":
    main()
