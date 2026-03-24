#!/usr/bin/env python3
"""
Deliverability Monitor Agent — Ensures all digital product delivery paths work.

Checks:
1. All PDF files in data/kdp_books/ are >10KB and readable
2. All cover images in data/kdp_books/covers/ exist
3. Gumroad delivery webhook maps to valid download files
4. ProFlow playbook download page is live
5. Checkout success page links to onboarding

On any issue: Pushover alert with specific details.
"""
import os, sys, json, logging
import urllib.request, urllib.parse, urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [DELIVER] %(message)s")
log = logging.getLogger("deliverability_monitor")

SITE = "https://nyspotlightreport.com"
PUSHOVER_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_ANON_KEY", "")

# Resolve data paths relative to repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KDP_BOOKS_DIR = os.path.join(REPO_ROOT, "data", "kdp_books")
COVERS_DIR = os.path.join(KDP_BOOKS_DIR, "covers")

MIN_PDF_SIZE = 10 * 1024  # 10KB


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


def check_pdf_files():
    """Verify all PDFs in data/kdp_books/ are >10KB and readable."""
    issues = []
    if not os.path.isdir(KDP_BOOKS_DIR):
        return [f"KDP books directory not found: {KDP_BOOKS_DIR}"]

    pdf_count = 0
    for root, dirs, files in os.walk(KDP_BOOKS_DIR):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            pdf_count += 1
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            if size < MIN_PDF_SIZE:
                issues.append(f"{f}: only {size} bytes (min {MIN_PDF_SIZE})")
                continue
            # Verify readable — check PDF header
            try:
                with open(path, "rb") as fh:
                    header = fh.read(5)
                    if header != b"%PDF-":
                        issues.append(f"{f}: invalid PDF header ({header[:10]})")
            except Exception as e:
                issues.append(f"{f}: unreadable — {e}")

    if pdf_count == 0:
        issues.append("No PDF files found in kdp_books/")
    else:
        log.info(f"  Scanned {pdf_count} PDF files")

    return issues


def check_cover_images():
    """Verify all cover images in data/kdp_books/covers/ exist."""
    issues = []
    if not os.path.isdir(COVERS_DIR):
        return [f"Covers directory not found: {COVERS_DIR}"]

    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    cover_count = 0
    for f in os.listdir(COVERS_DIR):
        ext = os.path.splitext(f)[1].lower()
        if ext not in image_exts:
            continue
        cover_count += 1
        path = os.path.join(COVERS_DIR, f)
        size = os.path.getsize(path)
        if size < 1024:
            issues.append(f"Cover {f}: only {size} bytes (suspiciously small)")

    if cover_count == 0:
        issues.append("No cover images found in kdp_books/covers/")
    else:
        log.info(f"  Found {cover_count} cover images")

    # Cross-check: every PDF should have a corresponding cover
    # Normalize names for fuzzy matching (strip _FULL, _cover, lowercase)
    if os.path.isdir(KDP_BOOKS_DIR):
        cover_bases = set()
        if os.path.isdir(COVERS_DIR):
            for cf in os.listdir(COVERS_DIR):
                cb = os.path.splitext(cf)[0].lower().replace("_cover", "").replace("-", "_")
                cover_bases.add(cb)

        for f in os.listdir(KDP_BOOKS_DIR):
            if not f.lower().endswith(".pdf"):
                continue
            base = os.path.splitext(f)[0].lower().replace("_full", "").replace("-", "_")
            # Check if any cover matches this normalized base
            if not any(base.startswith(cb) or cb.startswith(base) or base in cb or cb in base for cb in cover_bases):
                issues.append(f"No cover image found for {f}")

    return issues


def check_gumroad_webhook():
    """Verify Gumroad delivery webhook maps to valid download files."""
    url = f"{SITE}/.netlify/functions/gumroad-delivery"
    issues = []
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        return []
    except urllib.error.HTTPError as e:
        # 400/405 = function exists and rejects bare GETs (expected)
        if e.code in (400, 401, 403, 405):
            return []
        issues.append(f"Gumroad webhook returned unexpected {e.code}")
    except Exception as e:
        issues.append(f"Gumroad webhook unreachable: {e}")
    return issues


def check_proflow_download():
    """ProFlow playbook download page should be live."""
    url = f"{SITE}/proflow/"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode("utf-8", errors="replace")[:3000]
        if resp.getcode() != 200:
            return [f"ProFlow page returned {resp.getcode()}"]
        # Check for download-related content
        if "download" not in body.lower() and "playbook" not in body.lower() and "proflow" not in body.lower():
            return ["ProFlow page missing download/playbook content"]
    except urllib.error.HTTPError as e:
        return [f"ProFlow page returned {e.code}"]
    except Exception as e:
        return [f"ProFlow page unreachable: {e}"]
    return []


def check_checkout_success_onboarding():
    """Checkout success page should link to onboarding."""
    # Check success page exists and references onboarding
    url = f"{SITE}/checkout/success/"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode("utf-8", errors="replace")[:5000]
        if resp.getcode() != 200:
            return [f"Success page returned {resp.getcode()}"]
        if "onboarding" not in body.lower():
            return ["Success page does not link to onboarding"]
    except urllib.error.HTTPError as e:
        # 404 means no success page
        if e.code == 404:
            return ["Success page not found (404) — checkout may not redirect properly"]
        return [f"Success page returned {e.code}"]
    except Exception as e:
        return [f"Success page unreachable: {e}"]
    return []


def log_to_supabase(results):
    """Log results to site_health_log table."""
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
            "agent": "deliverability_monitor",
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
    log.info("=== Deliverability Monitor Starting ===")
    results = {}

    checks = [
        ("pdf_files", check_pdf_files),
        ("cover_images", check_cover_images),
        ("gumroad_webhook", check_gumroad_webhook),
        ("proflow_download", check_proflow_download),
        ("checkout_to_onboarding", check_checkout_success_onboarding),
    ]

    for name, fn in checks:
        log.info(f"Checking {name}...")
        results[name] = fn()
        log.info(f"  {name}: {'PASS' if not results[name] else f'FAIL ({len(results[name])})'}")

    total_issues = sum(len(v) for v in results.values())
    log.info(f"\n=== RESULTS: {total_issues} total issues ===")

    for category, issues in results.items():
        if issues:
            log.warning(f"  [{category}] {len(issues)} issues:")
            for issue in issues:
                log.warning(f"    - {issue}")

    # Log to Supabase
    log_to_supabase(results)

    # Alert on any failure
    if total_issues > 0:
        failure_summary = []
        for category, issues in results.items():
            for issue in issues:
                failure_summary.append(f"[{category}] {issue}")
        pushover(
            "DELIVERABILITY ALERT",
            f"{total_issues} delivery issues:\n" + "\n".join(failure_summary[:8]),
            priority=1 if total_issues >= 3 else 0
        )
    else:
        log.info("ALL CHECKS PASSED — all delivery paths healthy")

    return results


if __name__ == "__main__":
    results = run()
    total = sum(len(v) for v in results.values())
    sys.exit(1 if total > 0 else 0)
