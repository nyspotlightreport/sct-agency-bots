import os
REPO = r'C:\Users\S\sct-agency-bots'
WF = os.path.join(REPO, '.github', 'workflows')
s = "${{ secrets."
e = " }}"
new_wf = [
    ('outreach_daily.yml', 'Outreach Engine Daily', 'outreach_engine.py', '0 9 * * *'),
    ('onboarding_check.yml', 'Customer Onboarding Check', 'customer_onboarding.py', '0 */4 * * *'),
    ('synergy_router_daily.yml', 'Synergy Router', 'synergy_router.py', '30 11 * * *'),
]
for fname, name, agent, cron in new_wf:
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
  STRIPE_SECRET_KEY: {s}STRIPE_SECRET_KEY{e}
  GMAIL_APP_PASS: {s}GMAIL_APP_PASS{e}
  SMTP_USER: {s}SMTP_USER{e}
  APOLLO_API_KEY: {s}APOLLO_API_KEY{e}
  GH_PAT: {s}GH_PAT{e}
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
      - run: python agents/{agent}
"""
    with open(os.path.join(WF, fname), 'w') as f:
        f.write(yaml)
    print(f"CREATED {fname}")
print(f"Done: {len(new_wf)} workflows")
