#!/usr/bin/env python3
"""
NYSR Self-Repair Engine — auto-fixes common audit failures.
Triggered after audit failures. Commits fixes to repo.
"""
import os, sys, json, logging, re, ssl, subprocess
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("self_repair")
CTX = ssl.create_default_context()
FIXES = []

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

def fix_free_trial():
    """Remove any 'free trial' text from site HTML files."""
    site_dir = os.path.join(os.path.dirname(__file__), "..", "site")
    if not os.path.isdir(site_dir):
        return
    fixed = []
    for root, dirs, files in os.walk(site_dir):
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    if "free trial" in content.lower():
                        # Replace common patterns
                        new = re.sub(r'(?i)start\s+free\s+trial', 'Get Started', content)
                        new = re.sub(r'(?i)14-day\s+free\s+trial', 'instant setup', new)
                        new = re.sub(r'(?i)free\s+trial', 'getting started', new)
                        if new != content:
                            with open(path, "w", encoding="utf-8") as fh:
                                fh.write(new)
                            fixed.append(os.path.relpath(path, site_dir))
                except Exception:
                    pass
    if fixed:
        FIXES.append(f"Removed 'free trial' from {len(fixed)} files: {', '.join(fixed[:5])}")
        log.info(f"FIXED: Removed free trial from {len(fixed)} files")

def fix_zoho_email():
    """Ensure Zoho email is on key pages."""
    zoho = "editor-in-chief@nyspotlightreport.com"
    site_dir = os.path.join(os.path.dirname(__file__), "..", "site")
    pages = {
        "press/index.html": "media contact",
        "contact/index.html": "news desk",
        "about/masthead/index.html": "editorial contact",
    }
    for page, context in pages.items():
        path = os.path.join(site_dir, page)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if zoho not in content:
                # Add before </body>
                injection = f'\n<p style="text-align:center;padding:20px;"><strong>{context.title()}:</strong> <a href="mailto:{zoho}">{zoho}</a></p>\n'
                content = content.replace("</body>", injection + "</body>")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                FIXES.append(f"Added Zoho email to {page}")
                log.info(f"FIXED: Added Zoho email to {page}")

def fix_python_syntax():
    """Check all .py files for syntax errors and report."""
    dirs_to_check = ["agents", "bots", "scripts"]
    broken = []
    for d in dirs_to_check:
        dir_path = os.path.join(os.path.dirname(__file__), "..", d)
        if not os.path.isdir(dir_path):
            continue
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    try:
                        result = subprocess.run(
                            [sys.executable, "-m", "py_compile", path],
                            capture_output=True, text=True, timeout=10)
                        if result.returncode != 0:
                            broken.append(f"{d}/{f}")
                    except Exception:
                        pass
    if broken:
        FIXES.append(f"WARNING: {len(broken)} Python files have syntax errors: {', '.join(broken[:10])}")
        log.info(f"ALERT: {len(broken)} broken Python files found")
    else:
        log.info("All Python files compile clean")

def run():
    log.info("=" * 50)
    log.info("  NYSR SELF-REPAIR ENGINE")
    log.info(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log.info("=" * 50)

    # Read latest audit report to know what failed
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "audit", "latest_99d_audit.json")
    failures = []
    if os.path.exists(report_path):
        try:
            with open(report_path) as f:
                report = json.load(f)
            failures = [r["name"] for r in report.get("failures", [])]
            log.info(f"Audit failures to address: {', '.join(failures)}")
        except Exception:
            log.info("Could not read audit report")

    # Run repairs
    if any("free trial" in f.lower() for f in failures) or True:
        fix_free_trial()

    if any("zoho" in f.lower() for f in failures) or True:
        fix_zoho_email()

    fix_python_syntax()

    # Report
    log.info("\n" + "=" * 50)
    if FIXES:
        log.info(f"  {len(FIXES)} FIXES APPLIED")
        for fix in FIXES:
            log.info(f"  - {fix}")
        pushover(f"SELF-REPAIR: {len(FIXES)} fixes applied", "\n".join(FIXES[:5]))
    else:
        log.info("  NO REPAIRS NEEDED")
        pushover("SELF-REPAIR: System clean", "No repairs needed.")
    log.info("=" * 50)

if __name__ == "__main__":
    run()
