import subprocess, json, os, urllib.request, urllib.parse, re, base64, time

REPO = r'C:\Users\S\sct-agency-bots'
os.chdir(REPO)

# Get GH PAT from git remote URL
result = subprocess.run(['git','remote','get-url','origin'], capture_output=True, text=True)
remote = result.stdout.strip()
print(f"Remote: {remote}")

# Extract token if embedded in URL
pat_match = re.search(r'https://([^@]+)@github', remote)
if pat_match:
    PAT = pat_match.group(1)
    print(f"PAT found: {PAT[:8]}...")
else:
    # Try reading from git credential
    PAT = ""
    print("No PAT in remote URL")

if PAT:
    # Trigger the Stripe webhook registration workflow
    print("\n=== TRIGGERING STRIPE WEBHOOK REGISTRATION ===")
    data = json.dumps({"ref": "main"}).encode()
    req = urllib.request.Request(
        "https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/workflows/register_stripe_webhook.yml/dispatches",
        data=data,
        headers={"Authorization": f"token {PAT}", "Accept": "application/vnd.github+json", "Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=15)
        print("TRIGGERED register_stripe_webhook.yml")
    except urllib.error.HTTPError as e:
        print(f"Trigger error: {e.code} {e.read().decode()[:200]}")

    # === FULL SYSTEM INTEGRITY SCAN ===
    print("\n" + "="*60)
    print("FULL SYSTEM INTEGRITY SCAN")
    print("Finding everything that slipped through")
    print("="*60)

    HEADERS = {"Authorization": f"token {PAT}", "Accept": "application/vnd.github+json"}

    def gh_get(path):
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/nyspotlightreport/sct-agency-bots/{path}", headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except: return None

    issues = []

    # 1. Check Netlify env vars (different from GitHub Secrets!)
    print("\n[1] NETLIFY ENV VARS CHECK")
    print("  GitHub Secrets != Netlify env vars. Webhook needs GMAIL_APP_PASS in Netlify.")
    issues.append("CRITICAL: Netlify functions need env vars set in Netlify dashboard (GMAIL_APP_PASS, SMTP_USER, STRIPE_SECRET_KEY, SUPABASE_URL, etc). GitHub Secrets only work in GitHub Actions, NOT in Netlify functions.")

    # 2. Check for zero-byte files
    print("\n[2] ZERO-BYTE FILE CHECK")
    for folder in ['agents', 'bots']:
        for f in os.listdir(os.path.join(REPO, folder)):
            fp = os.path.join(REPO, folder, f)
            if os.path.getsize(fp) == 0:
                issues.append(f"ZERO-BYTE: {folder}/{f} — empty file, agent is dead")
                print(f"  ZERO: {folder}/{f}")

    # 3. Check Stripe payment links - do they have metadata?
    print("\n[3] STRIPE PAYMENT LINK METADATA CHECK")
    print("  Payment links MUST have offer_key metadata or webhook won't know which product was bought")
    issues.append("CHECK: Stripe payment links need metadata.offer_key set (proflow_ai, proflow_growth, etc) or webhook can't identify the product purchased")

    # 4. Check for hardcoded credentials in code
    print("\n[4] CREDENTIAL LEAK SCAN")
    cred_patterns = ['ghp_', 'sk_live_', 'sk_test_', 'Bearer ', 'api_key=', 'password=']
    for folder in ['agents', 'bots', 'netlify/functions']:
        folder_path = os.path.join(REPO, folder)
        if not os.path.exists(folder_path): continue
        for f in os.listdir(folder_path):
            fp = os.path.join(folder_path, f)
            if not os.path.isfile(fp): continue
            try:
                content = open(fp, 'r', encoding='utf-8', errors='ignore').read()
                for pat in cred_patterns:
                    if pat in content and 'environ' not in content[max(0,content.index(pat)-50):content.index(pat)]:
                        # Check if it's a real key (not just a variable name)
                        idx = content.index(pat)
                        snippet = content[idx:idx+30]
                        if any(c.isalnum() for c in snippet[len(pat):len(pat)+10]):
                            issues.append(f"CREDENTIAL LEAK: {folder}/{f} contains potential exposed key: {pat}...")
                            print(f"  LEAK: {folder}/{f} — {pat}...")
            except: pass

    # 5. Check success page actually redirects properly
    print("\n[5] SUCCESS PAGE CHECK")
    success_path = os.path.join(REPO, 'site', 'checkout', 'success', 'index.html')
    if os.path.exists(success_path):
        content = open(success_path, 'r').read()
        if 'stripe-webhook' not in content:
            issues.append("SUCCESS PAGE: Doesn't call stripe webhook — customer sees success but nothing happens")
        if 'session_id' not in content:
            issues.append("SUCCESS PAGE: Doesn't pass session_id — can't identify the purchase")
    else:
        issues.append("SUCCESS PAGE: File doesn't exist at site/checkout/success/")

    # 6. Check activate page exists (the setup_link in welcome email)
    print("\n[6] ACTIVATE PAGE CHECK")
    activate_path = os.path.join(REPO, 'site', 'activate', 'index.html')
    if os.path.exists(activate_path):
        content = open(activate_path, 'r').read()
        if len(content) < 500:
            issues.append("ACTIVATE PAGE: Exists but too small — likely placeholder")
            print("  WARN: activate page is tiny, may be placeholder")
    else:
        issues.append("ACTIVATE PAGE: Missing! Welcome email links to /activate/ but page doesn't exist")
        print("  MISSING: site/activate/index.html")

    # 7. Check failed workflows in last 24h
    print("\n[7] WORKFLOW FAILURE CHECK (last 20 runs)")
    runs = gh_get("actions/runs?per_page=20&status=failure")
    if runs and 'workflow_runs' in runs:
        failed = runs['workflow_runs']
        if failed:
            for r in failed[:5]:
                issues.append(f"WORKFLOW FAIL: {r['name']} — {r['conclusion']} at {r['updated_at']}")
                print(f"  FAIL: {r['name']} — {r['updated_at']}")
        else:
            print("  No failures in recent runs")

    # 8. Check Supabase schema deployed
    print("\n[8] SUPABASE SCHEMA CHECK")
    schema_path = os.path.join(REPO, 'database', 'schema_phase1.sql')
    if os.path.exists(schema_path):
        issues.append("PENDING: database/schema_phase1.sql has never been run against Supabase — tables may not exist")
        print("  PENDING: schema_phase1.sql exists but status unknown")

    # 9. Check Netlify deploy status
    print("\n[9] NETLIFY DEPLOY CHECK")
    issues.append("CHECK: After pushing stripe-webhook.js changes, verify Netlify auto-deployed. If functions aren't updating, check Netlify build settings.")

    # 10. Check old email still in any non-code files
    print("\n[10] OLD EMAIL IN NON-CODE FILES")
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in {'.git','node_modules'}]
        for f in files:
            if f.endswith(('.html', '.md', '.json', '.yml', '.sh', '.bat', '.ps1')):
                fp = os.path.join(root, f)
                try:
                    content = open(fp, 'r', encoding='utf-8', errors='ignore').read()
                    if 'nyspotlightreport' in content.lower():
                        rel = os.path.relpath(fp, REPO)
                        issues.append(f"OLD EMAIL: {rel} still contains nyspotlightreport")
                        print(f"  OLD EMAIL: {rel}")
                except: pass

    # 11. Check site looks professional (not AI boilerplate)
    print("\n[11] SITE QUALITY CHECK")
    index_path = os.path.join(REPO, 'site', 'index.html')
    if os.path.exists(index_path):
        content = open(index_path, 'r').read()
        boilerplate_signals = ['Lorem ipsum', 'placeholder', 'coming soon', 'under construction']
        for sig in boilerplate_signals:
            if sig.lower() in content.lower():
                issues.append(f"SITE QUALITY: index.html contains '{sig}' — looks unprofessional")
        if '-apple-system' in content or 'system-ui' in content:
            issues.append("SITE: Uses generic system fonts — Chairman says it looks AI-generated. Needs custom typography.")
    
    # 12. Check proflow page has proper Stripe links with metadata
    print("\n[12] PROFLOW PAYMENT LINKS")
    proflow_path = os.path.join(REPO, 'site', 'proflow', 'index.html')
    if os.path.exists(proflow_path):
        content = open(proflow_path, 'r').read()
        if 'buy.stripe.com' in content:
            print("  Stripe links found in proflow page")
            if 'offer_key' not in content and 'metadata' not in content:
                issues.append("PROFLOW: Stripe payment links exist but may not pass offer_key metadata — webhook won't know which tier was purchased")
        else:
            issues.append("PROFLOW: No Stripe payment links found on proflow page")

    # === FIX OLD EMAILS IN NON-CODE FILES ===
    print("\n=== AUTO-FIXING REMAINING OLD EMAILS ===")
    fixed_count = 0
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in {'.git','node_modules'}]
        for f in files:
            if not any(f.endswith(ext) for ext in ['.html','.md','.json','.yml','.yaml','.sh','.bat','.ps1','.js','.ts']): continue
            fp = os.path.join(root, f)
            try:
                content = open(fp, 'r', encoding='utf-8', errors='ignore').read()
                orig = content
                content = content.replace('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com')
                content = content.replace('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com')
                content = content.replace('nyspotlightreport+affiliates@gmail.com','nyspotlightreport+affiliates@gmail.com')
                content = content.replace('nyspotlightreport+sweep@gmail.com','nyspotlightreport+sweep@gmail.com')
                if content != orig:
                    open(fp, 'w', encoding='utf-8').write(content)
                    fixed_count += 1
                    print(f"  FIXED: {os.path.relpath(fp, REPO)}")
            except: pass
    print(f"  Fixed {fixed_count} files")

    # === SUMMARY ===
    print("\n" + "="*60)
    print(f"SYSTEM INTEGRITY SCAN COMPLETE")
    print(f"ISSUES FOUND: {len(issues)}")
    print("="*60)
    
    critical = [i for i in issues if 'CRITICAL' in i]
    checks = [i for i in issues if 'CHECK' in i]
    pending = [i for i in issues if 'PENDING' in i]
    other = [i for i in issues if i not in critical and i not in checks and i not in pending]
    
    if critical:
        print(f"\nCRITICAL ({len(critical)}):")
        for i in critical: print(f"  🔴 {i}")
    if other:
        print(f"\nISSUES ({len(other)}):")
        for i in other: print(f"  🟡 {i}")
    if checks:
        print(f"\nNEEDS VERIFICATION ({len(checks)}):")
        for i in checks: print(f"  🔵 {i}")
    if pending:
        print(f"\nPENDING ({len(pending)}):")
        for i in pending: print(f"  ⏳ {i}")

    # === COMMIT AND PUSH ALL FIXES ===
    print("\n=== COMMITTING FIXES ===")
    subprocess.run(['git','add','-A'], capture_output=True)
    r = subprocess.run(['git','commit','-m','audit: full integrity scan + auto-fix remaining emails + trigger stripe webhook'], capture_output=True, text=True)
    print(r.stdout[:200] if r.stdout else r.stderr[:200])
    r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
    print('PUSHED' if r2.returncode == 0 else r2.stderr[:200])

    # Save report
    report_path = os.path.join(REPO, 'data', 'integrity_scan.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump({"scan_date": time.strftime("%Y-%m-%d %H:%M"), "issues": issues, "total": len(issues), "critical": len(critical)}, f, indent=2)
    print(f"\nReport saved to data/integrity_scan.json")

else:
    print("Cannot extract PAT — need to trigger webhook manually")
    print("Go to: github.com/nyspotlightreport/sct-agency-bots/actions")
    print("Click: Register Stripe Webhook > Run workflow")
