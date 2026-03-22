import os, subprocess
REPO = r'C:\Users\S\sct-agency-bots'
WF = os.path.join(REPO, '.github', 'workflows')
os.makedirs(WF, exist_ok=True)
s = "${{ secrets."
e = " }}"
new_workflows = [
    ('security_scan_daily.yml', 'Security Scanner Daily', 'security_scanner.py', '0 5 * * *'),
    ('code_quality_daily.yml', 'Code Quality Gate Daily', 'code_quality_gate.py', '30 5 * * *'),
    ('opportunity_discovery_daily.yml', 'Opportunity Discovery Daily', 'opportunity_discovery.py', '0 8 * * *'),
]
for fname, name, agent, cron in new_workflows:
    yaml = f"""name: {name}
on:
  schedule:
    - cron: '{cron}'
  workflow_dispatch:
env:
  ANTHROPIC_API_KEY: {s}ANTHROPIC_API_KEY{e}
  SUPABASE_URL: {s}SUPABASE_URL{e}
  SUPABASE_KEY: {s}SUPABASE_KEY{e}
  PUSHOVER_API_KEY: {s}PUSHOVER_API_KEY{e}
  PUSHOVER_USER_KEY: {s}PUSHOVER_USER_KEY{e}
  GH_PAT: {s}GH_PAT{e}
  APOLLO_API_KEY: {s}APOLLO_API_KEY{e}
  STRIPE_SECRET_KEY: {s}STRIPE_SECRET_KEY{e}
  AHREFS_API_KEY: {s}AHREFS_API_KEY{e}
jobs:
  run:
    name: {name}
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests -q
      - run: python agents/{agent}
"""
    with open(os.path.join(WF, fname), 'w') as f:
        f.write(yaml)
    print(f"CREATED {fname}")
os.chdir(REPO)
subprocess.run(['git','add','-A'])
r = subprocess.run(['git','commit','-m','feat: security scanner + code quality gate + opportunity discovery agents with daily workflows'], capture_output=True, text=True)
print(r.stdout[:300] if r.stdout else r.stderr[:300])
r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
print('PUSHED' if r2.returncode == 0 else r2.stderr[:200])
