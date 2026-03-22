#!/usr/bin/env python3
"""
SECRETS ADDER — S.C. Thomas Internal Agency  
Adds all GitHub Actions secrets via API.
Run AFTER push_to_github.py
Run in PowerShell: python add_secrets.py
"""

import sys
import json
import base64
import getpass
import urllib.request
import urllib.error

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
            body = r.read()
            return json.loads(body) if body else {}, r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {}, e.code

def encrypt_secret(public_key_b64, secret_value):
    """Encrypt secret using libsodium (PyNaCl) or fallback"""
    try:
        from nacl import encoding, public
        pk = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
        box = public.SealedBox(pk)
        encrypted = box.encrypt(secret_value.encode())
        return base64.b64encode(encrypted).decode()
    except ImportError:
        # Fallback: use subprocess to call Python with nacl
        # If PyNaCl not available, return None to signal manual addition
        return None

def set_secret(token, username, repo, secret_name, secret_value):
    """Set a repository secret"""
    # Get public key
    key_data, status = api("GET", f"/repos/{username}/{repo}/actions/secrets/public-key", token=token)
    if status != 200:
        return False, f"Couldn't get public key: {status}"
    
    key_id  = key_data["key_id"]
    pub_key = key_data["key"]
    
    encrypted = encrypt_secret(pub_key, secret_value)
    if encrypted is None:
        return False, "PyNaCl not installed — use manual method"
    
    _, status = api("PUT", f"/repos/{username}/{repo}/actions/secrets/{secret_name}",
                    token=token, data={"encrypted_value": encrypted, "key_id": key_id})
    return status in [201, 204], f"Status: {status}"

def run():
    print()
    print("╔══════════════════════════════════════════╗")
    print("║  AGENCY SYSTEM — Secrets Adder          ║")
    print("╚══════════════════════════════════════════╝")
    print()

    token    = getpass.getpass("GitHub token (same one from push step): ").strip()
    user_data, _ = api("GET", "/user", token=token)
    username = user_data.get("login")
    if not username:
        print("Invalid token"); sys.exit(1)
    
    repo = "sct-agency-bots"
    print(f"Adding secrets to: github.com/{username}/{repo}")
    print()

    # Check if PyNaCl available
    try:
        import nacl
        has_nacl = True
    except ImportError:
        has_nacl = False

    if not has_nacl:
        print("Installing PyNaCl (required for secret encryption)...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "PyNaCl", "--quiet"], check=True)
        print("Installed. Continuing...")
        print()

    SECRETS = [
        ("ANTHROPIC_API_KEY",  "console.anthropic.com -> API Keys",                              "",                          True),
        ("GMAIL_USER",         "Your Gmail address",                                             "nyspotlightreport@gmail.com",     True),
        ("GMAIL_APP_PASS",     "myaccount.google.com/apppasswords -> Mail app password",         "",                          True),
        ("CHAIRMAN_EMAIL",     "Email for reports (Enter = nyspotlightreport@gmail.com)",              "nyspotlightreport@gmail.com",     True),
        ("AHREFS_API_KEY",     "ahrefs.com/api (Enter to skip)",                                 "",                          False),
        ("HUBSPOT_API_KEY",    "HubSpot -> Settings -> Private Apps (Enter to skip)",            "",                          False),
        ("APOLLO_API_KEY",     "Apollo.io -> Settings -> API (Enter to skip)",                   "",                          False),
        ("TARGET_DOMAIN",      "Your domain e.g. yourdomain.com (Enter to skip)",               "",                          False),
        ("MONITORED_SITES",    "e.g. https://yoursite.com (Enter to skip)",                      "",                          False),
        ("PAYPAL_ME_LINK",     "e.g. https://paypal.me/yourhandle (Enter to skip)",              "",                          False),
    ]

    set_count = 0
    skipped   = []

    for name, prompt, default, required in SECRETS:
        print(f"  {name}")
        print(f"  -> {prompt}")
        
        if default:
            value = input(f"     Value [{default}]: ").strip()
            if not value:
                value = default
        else:
            value = getpass.getpass(f"     Value: ").strip() if "KEY" in name or "PASS" in name else input(f"     Value: ").strip()
        
        if value:
            ok, msg = set_secret(token, username, repo, name, value)
            if ok:
                print(f"     ✅ Set")
                set_count += 1
            else:
                print(f"     ❌ Failed: {msg}")
        else:
            if required:
                print(f"     ⚠️  Required — skipped (add manually later)")
            else:
                print(f"     ⏭  Skipped")
            skipped.append(name)
        print()

    print(f"╔══════════════════════════════════════════╗")
    print(f"║  Secrets added: {set_count}/{len(SECRETS)}                      ║")
    print(f"╚══════════════════════════════════════════╝")
    
    if skipped:
        print(f"\nSkipped (add manually if needed): {', '.join(skipped)}")
        print(f"Manual: https://github.com/{username}/{repo}/settings/secrets/actions")

    print(f"\n✅ Done. Bots are LIVE.")
    print(f"Actions: https://github.com/{username}/{repo}/actions")

if __name__ == "__main__":
    run()
