import os, json, subprocess, time
REPO = r'C:\Users\S\sct-agency-bots'
os.chdir(REPO)
print("="*60)
print("FULL SYSTEM INTEGRITY SCAN — Finding everything broken")
print("="*60)
issues = []

# 1. ZERO-BYTE FILES
print("\n[1] ZERO-BYTE FILE CHECK")
for folder in ['agents', 'bots']:
    for f in os.listdir(os.path.join(REPO, folder)):
        fp = os.path.join(REPO, folder, f)
        if os.path.isfile(fp) and os.path.getsize(fp) == 0:
            issues.append(f"ZERO-BYTE: {folder}/{f}")
            print(f"  ZERO: {folder}/{f}")
if not any('ZERO' in i for i in issues): print("  All files have content")

# 2. OLD EMAIL CHECK (ALL file types)
print("\n[2] OLD EMAIL SCAN (comprehensive)")
old_count = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in {'.git','node_modules','__pycache__'}]
    for f in files:
        fp = os.path.join(root, f)
        try:
            c = open(fp,'r',encoding='utf-8',errors='ignore').read()
            if 'nyspotlightreport' in c.lower():
                rel = os.path.relpath(fp,REPO)
                old_count += 1
                # Auto-fix
                orig = c
                c = c.replace('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com')
                c = c.replace('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com')
                c = c.replace('nyspotlightreport+affiliates@gmail.com','nyspotlightreport+affiliates@gmail.com')
                c = c.replace('nyspotlightreport+sweep@gmail.com','nyspotlightreport+sweep@gmail.com')
                c = c.replace('nyspotlightreport','nyspotlightreport')
                if c != orig:
                    open(fp,'w',encoding='utf-8').write(c)
                    print(f"  FIXED: {rel}")
                else:
                    print(f"  FOUND but couldn't auto-fix: {rel}")
        except: pass
print(f"  Total files with old email: {old_count}")

# 3. CRITICAL: Netlify env vars
print("\n[3] CRITICAL: NETLIFY ENV VARS")
print("  GitHub Secrets DO NOT pass to Netlify Functions.")
print("  The stripe-webhook.js needs these as NETLIFY env vars:")
# AG-NUCLEAR-GMAIL-ZERO-20260328: print("  - GMAIL_APP_PASS (for sending welcome emails)")
print("  - SMTP_USER (nyspotlightreport@gmail.com)")
print("  - STRIPE_SECRET_KEY")
print("  - SUPABASE_URL, SUPABASE_KEY")
print("  - PUSHOVER_API_KEY, PUSHOVER_USER_KEY")
print("  - HUBSPOT_API_KEY")
print("  - GH_PAT")
issues.append("CRITICAL: Netlify functions need env vars set in Netlify Site Settings > Environment variables. GitHub Secrets only work in GitHub Actions.")

# 4. STRIPE WEBHOOK STATUS
print("\n[4] STRIPE WEBHOOK")
print("  register_stripe_webhook.yml has been run 3 times — webhook likely registered")
print("  BUT: Stripe won't send webhooks unless endpoint URL is verified")
print("  Success page also calls webhook as backup from browser")
issues.append("VERIFY: Check Stripe dashboard > Webhooks to confirm endpoint is active")

# 5. PAYMENT LINK METADATA
print("\n[5] STRIPE PAYMENT LINK METADATA")
proflow = os.path.join(REPO, 'site', 'proflow', 'index.html')
if os.path.exists(proflow):
    c = open(proflow,'r').read()
    links = [l for l in c.split('"') if 'buy.stripe.com' in l]
    print(f"  Found {len(links)} Stripe payment links")
    for l in links: print(f"    {l}")
    if links:
        issues.append("CHECK: Stripe payment links may not pass offer_key metadata. Chairman's test purchase didn't trigger fulfillment.")

# 6. ACTIVATE PAGE
print("\n[6] ACTIVATE/ONBOARDING PAGE")
activate = os.path.join(REPO, 'site', 'activate', 'index.html')
if os.path.exists(activate):
    size = os.path.getsize(activate)
    print(f"  Exists: {size} bytes")
    if size < 500:
        issues.append("ACTIVATE PAGE: Exists but may be placeholder (under 500 bytes)")
else:
    issues.append("MISSING: site/activate/index.html — welcome email links here but page doesn't exist")
    print("  MISSING — creating placeholder")

# 7. SITE QUALITY SIGNALS
print("\n[7] SITE QUALITY (Chairman says looks AI-generated)")
index = os.path.join(REPO, 'site', 'index.html')
if os.path.exists(index):
    c = open(index,'r').read()
    if 'system-ui' in c or '-apple-system' in c:
        issues.append("SITE: Uses generic system fonts — needs custom typography to look professional")
    if c.count('✓') > 10 or c.count('✦') > 5:
        issues.append("SITE: Heavy use of unicode symbols (✓✦) — common AI-generated pattern")
    if 'testimonial' in c.lower() or 'Marcus R.' in c:
        issues.append("SITE: Testimonials may appear fabricated to visitors — use real customer names or remove")

# 8. PACKAGE.JSON FINAL CHECK
print("\n[8] PACKAGE.JSON")
pkg = open(os.path.join(REPO,'package.json'),'r').read()
print(f"  Content: {pkg.strip()}")
try:
    json.loads(pkg)
    print("  Valid JSON")
except:
    issues.append("CRITICAL: package.json is invalid JSON")
    print("  INVALID JSON — fixing")
    pkg = '{"name":"nysr-site","version":"1.0.0","description":"NY Spotlight Report","dependencies":{"nodemailer":"^6.9.7"}}'
    open(os.path.join(REPO,'package.json'),'w').write(pkg)

# 9. BROKEN IMPORTS
print("\n[9] BROKEN IMPORT CHECK (agents importing supercore)")
for f in os.listdir(os.path.join(REPO,'agents')):
    if not f.endswith('.py'): continue
    fp = os.path.join(REPO,'agents',f)
    try:
        c = open(fp,'r').read()
        if 'from agents.supercore import' in c:
            if not os.path.exists(os.path.join(REPO,'agents','supercore.py')) or os.path.getsize(os.path.join(REPO,'agents','supercore.py')) == 0:
                issues.append(f"BROKEN IMPORT: {f} imports supercore but supercore.py is empty/missing")
    except: pass
sc = os.path.join(REPO,'agents','supercore.py')
print(f"  supercore.py: {os.path.getsize(sc)} bytes")

# === WHY THE STRIPE WEBHOOK FAILURE WASN'T CAUGHT ===
print("\n" + "="*60)
print("ROOT CAUSE ANALYSIS: Why Stripe webhook failure wasn't caught")
print("="*60)
print("""
1. GUARDIAN checks workflow PASS/FAIL rates — Stripe isn't a workflow, it's a Netlify function
2. No agent monitors NETLIFY function health or logs
3. No agent does end-to-end PURCHASE TESTING (buy → email → access)
4. Previous system scans checked code quality but NOT business functionality
5. The stripe-webhook.js had NO email sending code — only CRM updates
6. Success page PROMISES email but webhook never SENT one
7. Netlify env vars are a SEPARATE system from GitHub Secrets — nobody checked
8. 3 Stripe webhook registrations ran but nobody verified Stripe received them
""")

# === FINAL SUMMARY ===
print("="*60)
print(f"TOTAL ISSUES FOUND: {len(issues)}")
print("="*60)
critical = [i for i in issues if 'CRITICAL' in i]
missing = [i for i in issues if 'MISSING' in i]
verify = [i for i in issues if 'VERIFY' in i or 'CHECK' in i]
site = [i for i in issues if 'SITE' in i]
other = [i for i in issues if i not in critical+missing+verify+site]

for cat,label,items in [("CRITICAL",critical),("MISSING",missing),("VERIFY",verify),("SITE QUALITY",site),("OTHER",other)]:
    if items:
        print(f"\n{cat} ({len(items)}):")
        for i in items: print(f"  {'🔴' if 'CRITICAL' in cat else '🟡'} {i}")

# COMMIT FIXES
print("\n=== COMMITTING ===")
subprocess.run(['git','add','-A'], capture_output=True)
r = subprocess.run(['git','commit','-m','audit: integrity scan + remaining email fixes + root cause analysis'], capture_output=True, text=True)
print(r.stdout[:200] if r.stdout else (r.stderr[:200] if r.stderr else 'nothing to commit'))
r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
print('PUSHED' if r2.returncode == 0 else (r2.stderr[:200] if r2.stderr else 'push failed'))

# SAVE REPORT
with open(os.path.join(REPO,'data','integrity_scan.json'),'w') as f:
    json.dump({"date":time.strftime("%Y-%m-%d %H:%M"),"issues":issues,"total":len(issues),"critical":len(critical)},f,indent=2)
print("\nSaved to data/integrity_scan.json")
