#!/usr/bin/env python3
"""
GITHUB AUTO-PUSHER — S.C. Thomas Internal Agency
Pushes ALL bot files to GitHub via API. No git. No bash. No installation.
Run in PowerShell: python push_to_github.py
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import getpass
from pathlib import Path

REPO_NAME   = "sct-agency-bots"
DESCRIPTION = "S.C. Thomas Internal Agency Bot System v2.0"
SCRIPT_DIR  = Path(__file__).parent

def api(method, endpoint, data=None, token=""):
    url = f"https://api.github.com{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "AgencyBot/2.0")
    if data:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {}, e.code

def b64(content):
    if isinstance(content, str):
        content = content.encode("utf-8")
    return base64.b64encode(content).decode()

def collect_files():
    """Collect all files to push"""
    files = {}
    
    # All bot Python files
    for f in sorted((SCRIPT_DIR / "bots").glob("*.py")):
        files[f"bots/{f.name}"] = f.read_text(encoding="utf-8", errors="replace")
    
    # All bot shell/ps1 scripts
    for f in sorted(SCRIPT_DIR.glob("*.ps1")):
        files[f.name] = f.read_text(encoding="utf-8", errors="replace")
    for f in sorted(SCRIPT_DIR.glob("*.sh")):
        files[f.name] = f.read_text(encoding="utf-8", errors="replace")
    
    # GitHub Actions workflows
    for f in sorted((SCRIPT_DIR / ".github" / "workflows").glob("*.yml")):
        files[f".github/workflows/{f.name}"] = f.read_text(encoding="utf-8", errors="replace")
    
    # Other files
    for fname in ["README.md", "requirements.txt", ".gitignore"]:
        fpath = SCRIPT_DIR / fname
        if fpath.exists():
            files[fname] = fpath.read_text(encoding="utf-8", errors="replace")
    
    return files

def run():
    print()
    print("╔══════════════════════════════════════════╗")
    print("║  AGENCY SYSTEM — GitHub Auto-Pusher     ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # ── GET TOKEN ─────────────────────────────────────────────────────────────
    print("You need a GitHub Personal Access Token.")
    print()
    print("Get one now (30 seconds):")
    print("  1. Go to: https://github.com/settings/tokens/new")
    print("  2. Note: 'Agency Bot Setup'")
    print("  3. Expiration: 7 days")
    print("  4. Scopes: check 'repo' (top checkbox)")
    print("  5. Click 'Generate token'")
    print("  6. Copy the token (starts with ghp_)")
    print()
    
    token = getpass.getpass("Paste token here (hidden): ").strip()
    if not token:
        print("No token entered. Exiting.")
        sys.exit(1)

    # ── VERIFY TOKEN ──────────────────────────────────────────────────────────
    print()
    print("Verifying token...")
    user_data, status = api("GET", "/user", token=token)
    if status != 200:
        print(f"Token invalid (status {status}). Check and try again.")
        sys.exit(1)
    username = user_data["login"]
    print(f"  Logged in as: {username}")

    # ── CREATE REPO ───────────────────────────────────────────────────────────
    print(f"Creating repo: {REPO_NAME}...")
    repo_data, status = api("POST", "/user/repos", token=token, data={
        "name":        REPO_NAME,
        "description": DESCRIPTION,
        "private":     True,
        "auto_init":   False,
    })
    if status == 201:
        print(f"  Repo created: github.com/{username}/{REPO_NAME}")
    elif status == 422:
        print(f"  Repo already exists — pushing to it")
    else:
        print(f"  Repo creation error: {repo_data.get('message', status)}")

    # ── COLLECT AND PUSH FILES ────────────────────────────────────────────────
    files = collect_files()
    print(f"Pushing {len(files)} files...")
    
    pushed = 0
    failed = 0
    
    for filepath, content in sorted(files.items()):
        # Check if file exists to get SHA for update
        existing, _ = api("GET", f"/repos/{username}/{REPO_NAME}/contents/{filepath}", token=token)
        sha = existing.get("sha") if isinstance(existing, dict) else None
        
        payload = {
            "message": f"Add {filepath}",
            "content": b64(content),
        }
        if sha:
            payload["sha"] = sha
            payload["message"] = f"Update {filepath}"
        
        _, status = api("PUT", f"/repos/{username}/{REPO_NAME}/contents/{filepath}",
                        token=token, data=payload)
        
        if status in [200, 201]:
            pushed += 1
            print(f"  [OK] {filepath}")
        else:
            failed += 1
            print(f"  [!!] {filepath} (status {status})")

    # ── DONE ──────────────────────────────────────────────────────────────────
    print()
    print(f"╔══════════════════════════════════════════╗")
    print(f"║  PUSHED: {pushed}/{len(files)} files                   ║")
    print(f"╚══════════════════════════════════════════╝")
    print()
    print(f"  Repo:    https://github.com/{username}/{REPO_NAME}")
    print(f"  Actions: https://github.com/{username}/{REPO_NAME}/actions")
    print()
    print("NOW ADD SECRETS:")
    print(f"  https://github.com/{username}/{REPO_NAME}/settings/secrets/actions")
    print()
    print("  ANTHROPIC_API_KEY  -> console.anthropic.com")
    print("  GMAIL_APP_PASS     -> myaccount.google.com/apppasswords")
    print("  AHREFS_API_KEY     -> ahrefs.com/api")
    print("  HUBSPOT_API_KEY    -> HubSpot -> Settings -> Private Apps")
    print("  APOLLO_API_KEY     -> Apollo.io -> Settings -> API")
    print("  TARGET_DOMAIN      -> yourdomain.com")
    print("  MONITORED_SITES    -> https://yoursite.com")
    print()
    print("  (GMAIL_USER and CHAIRMAN_EMAIL already default to nyspotlightreport@gmail.com)")
    print()

    # Save the repo URL for reference
    (SCRIPT_DIR / "REPO_URL.txt").write_text(f"https://github.com/{username}/{REPO_NAME}\n")
    print(f"Repo URL saved to REPO_URL.txt")
    
    if failed == 0:
        print()
        print("All files pushed successfully. Bots will run automatically.")

if __name__ == "__main__":
    run()
