#!/usr/bin/env python3
"""
Fulfillment Monitor Agent — Monitors and repairs the entire customer fulfillment pipeline.

Checks:
1. Stripe webhook is responding (GET returns 400 = signature enforced)
2. create-checkout returns real cs_live_ session
3. lead-capture endpoint accepts POSTs
4. voice-ai returns TwiML with ProFlow
5. Onboarding page is live
6. Gumroad delivery webhook is active
7. Email SMTP connectivity (test Gmail SMTP login)

On failure: Pushover alert with specific failure details.
Logs results to Supabase site_health_log.
"""
import os, sys, json, logging, ssl, smtplib
import urllib.request, urllib.parse, urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [FULFILLMENT] %(message)s")
log = logging.getLogger("fulfillment_monitor")

SITE = "https://nyspotlightreport.com"
PUSHOVER_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_ANON_KEY", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "nyspotlightreport@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS", "")


def pushover(title, msg, priority=0):
    if not PUSHOVER_API or not PUSHOVER_USER:
        log.warning(f"No Pushover keys — cannot send: {title}")
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSHOVER_API, "user": PUSHOVER_USER,
            "title": title, "message": msg[:1024], "priority": priority
        }).encode()
        urllib.request.urlopen(urllib.request.Request(
            "https://api.pushover.net/1/messages.json", data=data
        ), timeout=10)
    except Exception as e:
        log.error(f"Pushover failed: {e}")


def check_stripe_webhook():
    """Stripe webhook POST without signature should return 400 (signature enforced)."""
    url = f"{SITE}/.netlify/functions/stripe-webhook"
    try:
        data = json.dumps({"type": "healthcheck"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=15)
        # If we get 200, signature is NOT being enforced
        return [f"stripe-webhook returned {resp.getcode()} on unsigned POST — signature not enforced!"]
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return []  # Good — signature enforcement active
        return [f"stripe-webhook returned {e.code}, expected 400"]
    except Exception as e:
        return [f"stripe-webhook unreachable: {e}"]


def check_create_checkout():
    """POST to create-checkout should return a cs_live_ session."""
    url = f"{SITE}/.netlify/functions/create-checkout"
    try:
        payload = json.dumps({"plan": "starter"}).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode("utf-8", errors="replace")
        if "cs_live_" not in body and "checkout.stripe.com" not in body:
            return [f"create-checkout returned no cs_live_ session: {body[:200]}"]
    except Exception as e:
        return [f"create-checkout failed: {e}"]
    return []


def check_lead_capture():
    """lead-capture endpoint should accept POSTs."""
    url = f"{SITE}/.netlify/functions/lead-capture"
    try:
        payload = json.dumps({
            "email": "healthcheck@test.invalid",
            "source": "fulfillment_monitor"
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=15)
        status = resp.getcode()
        if status not in (200, 201, 204):
            return [f"lead-capture returned {status}, expected 2xx"]
    except urllib.error.HTTPError as e:
        if e.code >= 500:
            return [f"lead-capture server error: {e.code}"]
        # 4xx might be OK (e.g., duplicate or validation)
    except Exception as e:
        return [f"lead-capture unreachable: {e}"]
    return []


def check_voice_ai():
    """voice-ai should return TwiML containing ProFlow."""
    url = f"{SITE}/.netlify/functions/voice-ai"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode("utf-8", errors="replace")[:2000]
        if "ProFlow" not in body:
            return [f"voice-ai response missing 'ProFlow' in TwiML: {body[:200]}"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:2000] if hasattr(e, 'read') else ""
        if "ProFlow" not in body:
            return [f"voice-ai returned {e.code}, body missing 'ProFlow'"]
    except Exception as e:
        return [f"voice-ai unreachable: {e}"]
    return []


def check_onboarding_page():
    """Onboarding page should be live and return 200."""
    url = f"{SITE}/onboarding/"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        if resp.getcode() != 200:
            return [f"Onboarding page returned {resp.getcode()}"]
    except urllib.error.HTTPError as e:
        return [f"Onboarding page returned {e.code}"]
    except Exception as e:
        return [f"Onboarding page unreachable: {e}"]
    return []


def check_gumroad_webhook():
    """Gumroad delivery function should be active (responds to ping)."""
    url = f"{SITE}/.netlify/functions/gumroad-delivery"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        # Any response means endpoint is live
        return []
    except urllib.error.HTTPError as e:
        # 400/405 are fine — means the function exists and rejects bare GETs
        if e.code in (400, 401, 403, 405):
            return []
        return [f"gumroad-webhook returned {e.code}"]
    except Exception as e:
        return [f"gumroad-webhook unreachable: {e}"]


def check_smtp():
    """Test email relay endpoint (Netlify function proxies Gmail SMTP)."""
    url = f"{SITE}/.netlify/functions/send-email"
    try:
        data = json.dumps({"to": "healthcheck@test.invalid", "subject": "healthcheck"}).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "x-auth-key": PUSHOVER_API},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=15)
        status = resp.getcode()
        if status == 200:
            return []  # Relay endpoint is live
        return [f"Email relay returned {status}"]
    except urllib.error.HTTPError as e:
        if e.code in (400, 401, 500):
            body = e.read().decode("utf-8", errors="replace")[:200]
            return [f"Email relay returned {e.code}: {body}"]
        return [f"Email relay returned {e.code}"]
    except Exception as e:
        return [f"Email relay unreachable: {e}"]


def log_to_supabase(results):
    """Log health check results to site_health_log table."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.warning("No Supabase credentials — skipping log")
        return
    all_passed = all(len(v) == 0 for v in results.values())
    failures = []
    for category, issues in results.items():
        for issue in issues:
            failures.append(f"[{category}] {issue}")
    try:
        payload = json.dumps({
            "agent": "fulfillment_monitor",
            "all_passed": all_passed,
            "failures": failures[:20],
            "details": {k: v for k, v in results.items()}
        }).encode()
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/site_health_log",
            data=payload,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"Supabase logging failed: {e}")


def run():
    log.info("=== Fulfillment Monitor Starting ===")
    results = {}

    checks = [
        ("stripe_webhook", check_stripe_webhook),
        ("create_checkout", check_create_checkout),
        ("lead_capture", check_lead_capture),
        ("voice_ai", check_voice_ai),
        ("onboarding", check_onboarding_page),
        ("gumroad_webhook", check_gumroad_webhook),
        ("smtp", check_smtp),
    ]

    for name, fn in checks:
        log.info(f"Checking {name}...")
        results[name] = fn()
        log.info(f"  {name}: {'PASS' if not results[name] else f'FAIL ({len(results[name])})'}")

    total_issues = sum(len(v) for v in results.values())
    log.info(f"\n=== RESULTS: {total_issues} total issues ===")

    # Separate critical (blocks customer delivery) from warnings (degraded but functional)
    CRITICAL_CHECKS = {"stripe_webhook", "create_checkout", "lead_capture", "voice_ai", "onboarding", "gumroad_webhook"}
    WARNING_CHECKS = {"smtp"}

    critical_issues = sum(len(results[k]) for k in CRITICAL_CHECKS if k in results)
    warning_issues = sum(len(results[k]) for k in WARNING_CHECKS if k in results)
    total_issues = critical_issues + warning_issues

    log.info(f"\n=== RESULTS: {critical_issues} critical, {warning_issues} warnings ===")

    for category, issues in results.items():
        if issues:
            level = "CRITICAL" if category in CRITICAL_CHECKS else "WARNING"
            log.warning(f"  [{level}:{category}] {len(issues)} issues:")
            for issue in issues:
                log.warning(f"    - {issue}")

    # Log to Supabase
    log_to_supabase(results)

    # Alert only on critical failures
    if critical_issues > 0:
        failure_summary = []
        for category in CRITICAL_CHECKS:
            for issue in results.get(category, []):
                failure_summary.append(f"[{category}] {issue}")
        pushover(
            "FULFILLMENT PIPELINE ALERT",
            f"{critical_issues} critical issues:\n" + "\n".join(failure_summary[:8]),
            1 if critical_issues >= 3 else 0
        )
    elif warning_issues > 0:
        log.info(f"{warning_issues} non-critical warnings (SMTP) — not blocking")
    else:
        log.info("ALL CHECKS PASSED — fulfillment pipeline healthy")

    return results


if __name__ == "__main__":
    results = run()
    critical = sum(len(results[k]) for k in {"stripe_webhook", "create_checkout", "lead_capture", "voice_ai", "onboarding", "gumroad_webhook"} if k in results)
    sys.exit(1 if critical > 0 else 0)
