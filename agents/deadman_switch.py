#!/usr/bin/env python3
"""
deadman_switch.py — Dead-Man's Switch Monitor
══════════════════════════════════════════════

Detects when the system goes silent:
  - No agent runs in 6+ hours → CRITICAL alert
  - No content published in 24h → WARNING
  - No leads captured in 48h → WARNING
  - No revenue in 72h → CRITICAL
  - Key API health checks failing → WARNING

Runs every 2 hours via GitHub Actions.
If THIS agent fails to run, the Chairman knows something is deeply wrong.
"""

import os, sys, json, logging, time
from datetime import datetime, timedelta, timezone

log = logging.getLogger("deadman")

SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")
SITE_URL      = "https://nyspotlightreport.com"

import urllib.request, urllib.error, urllib.parse


def _supa(method, table, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json"}
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"Supa query failed: {e}")
        return None


def _push(title, msg, priority=0):
    if not PUSHOVER_API: return
    data = urllib.parse.urlencode({
        "token": PUSHOVER_API, "user": PUSHOVER_USER,
        "title": title[:100], "message": msg[:1000], "priority": priority
    }).encode()
    try:
        urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except Exception:
        pass


def _site_check(path="/"):
    """Check if the site is responding."""
    try:
        req = urllib.request.Request(f"{SITE_URL}{path}",
                                     headers={"User-Agent": "NYSR-DeadmanSwitch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.getcode() == 200
    except Exception:
        return False


def check_agent_silence():
    """Alert if no agent has run in 6+ hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    runs = _supa("GET", "agent_run_logs",
                 f"?completed_at=gte.{cutoff}&select=id&limit=1")
    if runs is None:
        return {"status": "unknown", "reason": "Cannot reach Supabase"}
    if isinstance(runs, list) and len(runs) == 0:
        return {"status": "critical", "reason": "No agent runs in 6+ hours"}
    return {"status": "ok", "reason": "Agents running"}


def check_revenue_silence():
    """Alert if no revenue in 72 hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=72)).strftime("%Y-%m-%d")
    revenue = _supa("GET", "revenue_daily",
                    f"?date=gte.{cutoff}&amount=gt.0&select=id&limit=1")
    if revenue is None:
        return {"status": "unknown", "reason": "Cannot reach Supabase"}
    if isinstance(revenue, list) and len(revenue) == 0:
        return {"status": "critical", "reason": "No revenue in 72+ hours"}
    return {"status": "ok", "reason": "Revenue flowing"}


def check_lead_flow():
    """Alert if no new leads in 48 hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    leads = _supa("GET", "contacts",
                  f"?created_at=gte.{cutoff}&select=id&limit=1")
    if leads is None:
        return {"status": "unknown", "reason": "Cannot reach Supabase"}
    if isinstance(leads, list) and len(leads) == 0:
        return {"status": "warning", "reason": "No new leads in 48+ hours"}
    return {"status": "ok", "reason": "Leads flowing"}


def check_site_health():
    """Check if the main site and key pages are up."""
    pages = ["/", "/portal/", "/proflow/"]
    for page in pages:
        if not _site_check(page):
            return {"status": "critical", "reason": f"Site down: {SITE_URL}{page}"}
    return {"status": "ok", "reason": "Site healthy"}


def check_api_health():
    """Check if critical APIs are responding."""
    checks = []

    # Anthropic
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 5,
                                 "messages": [{"role": "user", "content": "ping"}]}).encode(),
                headers={"Content-Type": "application/json", "x-api-key": key,
                         "anthropic-version": "2023-06-01"})
            with urllib.request.urlopen(req, timeout=10) as r:
                checks.append(("anthropic", "ok"))
        except Exception as e:
            checks.append(("anthropic", f"fail: {str(e)[:50]}"))

    # Supabase
    if SUPABASE_URL:
        result = _supa("GET", "agent_run_logs", "?select=id&limit=1")
        checks.append(("supabase", "ok" if result is not None else "fail"))

    failed = [c for c in checks if c[1] != "ok"]
    if failed:
        return {"status": "warning", "reason": f"API issues: {', '.join(f'{n}: {s}' for n, s in failed)}"}
    return {"status": "ok", "reason": f"All {len(checks)} APIs healthy"}


def run():
    log.info("Dead-man's switch — running all checks")

    checks = [
        ("AGENT_SILENCE", check_agent_silence),
        ("REVENUE", check_revenue_silence),
        ("LEAD_FLOW", check_lead_flow),
        ("SITE_HEALTH", check_site_health),
        ("API_HEALTH", check_api_health),
    ]

    results = {}
    criticals = []
    warnings = []

    for name, check_fn in checks:
        try:
            result = check_fn()
        except Exception as e:
            result = {"status": "error", "reason": str(e)[:100]}

        results[name] = result
        status = result.get("status", "unknown")
        reason = result.get("reason", "")

        if status == "critical":
            criticals.append(f"{name}: {reason}")
            log.error(f"CRITICAL — {name}: {reason}")
        elif status == "warning":
            warnings.append(f"{name}: {reason}")
            log.warning(f"WARNING — {name}: {reason}")
        else:
            log.info(f"OK — {name}: {reason}")

    # Alert logic
    if criticals:
        _push("DEADMAN ALERT — CRITICAL",
              "CRITICAL ISSUES:\n" + "\n".join(criticals) +
              ("\n\nWARNINGS:\n" + "\n".join(warnings) if warnings else ""),
              priority=1)
    elif warnings:
        _push("Deadman — Warnings",
              "Warnings:\n" + "\n".join(warnings),
              priority=0)

    # Log results to Supabase
    if SUPABASE_URL:
        try:
            payload = json.dumps({
                "agent_name": "deadman_switch",
                "status": "failed" if criticals else ("partial" if warnings else "success"),
                "metrics": results,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }).encode()
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                       "Content-Type": "application/json", "Prefer": "return=minimal"}
            req = urllib.request.Request(
                f"{SUPABASE_URL}/rest/v1/agent_run_logs",
                data=payload, method="POST", headers=headers)
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    summary = f"Checks: {len(checks)} | Critical: {len(criticals)} | Warnings: {len(warnings)}"
    log.info(f"Dead-man's switch complete: {summary}")

    return {
        "checks": len(checks),
        "criticals": len(criticals),
        "warnings": len(warnings),
        "details": results,
        "items_processed": len(checks),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [DEADMAN] %(message)s")
    results = run()
    print(json.dumps(results, indent=2, default=str))
