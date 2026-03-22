# ================================================================
# AGENCY SYSTEM — COMPLETE GITHUB ACTIONS DEPLOYMENT
# S.C. Thomas Internal Agency v2.0
# ================================================================
# SETUP:
# 1. Create private GitHub repo
# 2. Push entire /bots/ directory
# 3. Add all secrets in repo Settings → Secrets → Actions
# 4. All bots run automatically on schedule
# ================================================================

# ── FILE: .github/workflows/command-center.yml ──────────────────
COMMAND_CENTER = """
name: Agency Command Center
on:
  schedule:
    - cron: '* * * * *'    # Every minute (GitHub minimum is 5min in practice)
  workflow_dispatch:

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - name: Cache state
        uses: actions/cache@v3
        with:
          path: state/
          key: agency-state-${{ github.run_number }}
          restore-keys: agency-state-
      - run: pip install requests schedule
      - name: Health check
        run: python bots/agency_command_center.py --status
        env: &env
          ANTHROPIC_API_KEY:  ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:         ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS:     ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:     ${{ secrets.CHAIRMAN_EMAIL }}
          AHREFS_API_KEY:     ${{ secrets.AHREFS_API_KEY }}
          HUBSPOT_API_KEY:    ${{ secrets.HUBSPOT_API_KEY }}
          APOLLO_API_KEY:     ${{ secrets.APOLLO_API_KEY }}
          TARGET_DOMAIN:      ${{ secrets.TARGET_DOMAIN }}
          MONITORED_SITES:    ${{ secrets.MONITORED_SITES }}
          PAYPAL_ME_LINK:     ${{ secrets.PAYPAL_ME_LINK }}
          BUSINESS_NAME:      ${{ secrets.BUSINESS_NAME }}
"""

# ── FILE: .github/workflows/weekly-report.yml ───────────────────
WEEKLY_REPORT = """
name: Weekly KPI Report
on:
  schedule:
    - cron: '0 13 * * 1'   # Monday 8am ET
  workflow_dispatch:
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - run: python bots/weekly_report_bot_v2.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:        ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS:    ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}
          AHREFS_API_KEY:    ${{ secrets.AHREFS_API_KEY }}
          HUBSPOT_API_KEY:   ${{ secrets.HUBSPOT_API_KEY }}
          TARGET_DOMAIN:     ${{ secrets.TARGET_DOMAIN }}
"""

# ── FILE: .github/workflows/daily-ops.yml ───────────────────────
DAILY_OPS = """
name: Daily Operations
on:
  schedule:
    - cron: '0 12 * * *'   # Daily 7am ET
  workflow_dispatch:
jobs:
  inbox:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests google-auth google-auth-oauthlib google-api-python-client
      - name: Restore Gmail token
        uses: actions/cache@v3
        with:
          path: token.pickle
          key: gmail-token-stable
      - run: python bots/inbox_triage_bot.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:        ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS:    ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}

  invoices:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - name: Restore invoice state
        uses: actions/cache@v3
        with:
          path: invoice_state.json
          key: invoice-state-${{ github.run_number }}
          restore-keys: invoice-state-
      - run: python bots/invoice_bot.py --remind
        env:
          GMAIL_USER:    ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS: ${{ secrets.GMAIL_APP_PASS }}
          PAYPAL_ME_LINK: ${{ secrets.PAYPAL_ME_LINK }}
"""

# ── FILE: .github/workflows/uptime.yml ──────────────────────────
UPTIME = """
name: Uptime Monitor
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:
jobs:
  monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - name: Restore uptime state
        uses: actions/cache@v3
        with:
          path: uptime_state.json
          key: uptime-state-${{ github.run_number }}
          restore-keys: uptime-state-
      - run: python bots/uptime_monitor_bot.py
        env:
          GMAIL_USER:      ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS:  ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:  ${{ secrets.CHAIRMAN_EMAIL }}
          MONITORED_SITES: ${{ secrets.MONITORED_SITES }}
"""

# ── FILE: .github/workflows/seo-monitor.yml ─────────────────────
SEO_MONITOR = """
name: SEO Monitor
on:
  schedule:
    - cron: '0 14 * * 1,4'  # Mon + Thu 9am ET
  workflow_dispatch:
jobs:
  seo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - name: Restore SEO state
        uses: actions/cache@v3
        with:
          path: seo_state.json
          key: seo-state-${{ github.run_number }}
          restore-keys: seo-state-
      - run: python bots/seo_rank_tracker_bot.py
        env:
          AHREFS_API_KEY: ${{ secrets.AHREFS_API_KEY }}
          GMAIL_USER:     ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS: ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL: ${{ secrets.CHAIRMAN_EMAIL }}
          TARGET_DOMAIN:  ${{ secrets.TARGET_DOMAIN }}
"""

# ── FILE: .github/workflows/self-improvement.yml ────────────────
SELF_IMPROVE = """
name: Self-Improvement Engine
on:
  schedule:
    - cron: '0 11 * * 0'   # Sunday 6am ET
  workflow_dispatch:
jobs:
  improve:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - name: Restore all state
        uses: actions/cache@v3
        with:
          path: state/
          key: agency-state-${{ github.run_number }}
          restore-keys: agency-state-
      - run: python bots/self_improvement_bot.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:        ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS:    ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}
"""

# ── FILE: .github/workflows/lead-pipeline.yml ───────────────────
LEADS = """
name: Lead Pipeline
on:
  schedule:
    - cron: '0 17 * * 2'   # Tuesday noon ET
  workflow_dispatch:
    inputs:
      search_query:
        description: 'Apollo search'
        default: 'founder CEO media New York'
      limit:
        description: 'Lead count'
        default: '25'
jobs:
  leads:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - run: python bots/lead_pipeline_bot.py --search "${{ github.event.inputs.search_query || 'founder CEO media New York' }}" --limit ${{ github.event.inputs.limit || '25' }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          APOLLO_API_KEY:    ${{ secrets.APOLLO_API_KEY }}
          HUBSPOT_API_KEY:   ${{ secrets.HUBSPOT_API_KEY }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}
      - uses: actions/upload-artifact@v3
        with:
          name: leads-${{ github.run_number }}
          path: leads_*.json
          retention-days: 30
"""

# ── FILE: .github/workflows/competitor-monitor.yml ──────────────
COMPETITOR = """
name: Competitor Monitor
on:
  schedule:
    - cron: '0 4 * * 0'   # Sunday 11pm ET
  workflow_dispatch:
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests
      - name: Restore competitor state
        uses: actions/cache@v3
        with:
          path: competitor_state.json
          key: competitor-state-${{ github.run_number }}
          restore-keys: competitor-state-
      - run: python bots/competitor_monitor_bot.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_USER:        ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASS:    ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}
"""

# ── SECRETS REFERENCE ───────────────────────────────────────────
SECRETS = """
REQUIRED SECRETS (GitHub → Settings → Secrets → Actions):

  Core:
  ANTHROPIC_API_KEY     Your Anthropic API key
  GMAIL_USER            nyspotlightreport@gmail.com
  GMAIL_APP_PASS        Gmail App Password (myaccount.google.com/apppasswords)
  CHAIRMAN_EMAIL        nyspotlightreport@gmail.com

  APIs:
  AHREFS_API_KEY        Ahrefs API (ahrefs.com/api)
  HUBSPOT_API_KEY       HubSpot private app token
  APOLLO_API_KEY        Apollo.io API key

  Config:
  TARGET_DOMAIN         yourdomain.com (no https://)
  MONITORED_SITES       https://site1.com,https://site2.com
  PAYPAL_ME_LINK        https://paypal.me/yourhandle
  BUSINESS_NAME         S.C. Thomas
"""

if __name__ == "__main__":
    from pathlib import Path
    base = Path(".github/workflows")
    base.mkdir(parents=True, exist_ok=True)

    workflows = {
        "weekly-report.yml":        WEEKLY_REPORT,
        "daily-ops.yml":            DAILY_OPS,
        "uptime.yml":               UPTIME,
        "seo-monitor.yml":          SEO_MONITOR,
        "self-improvement.yml":     SELF_IMPROVE,
        "lead-pipeline.yml":        LEADS,
        "competitor-monitor.yml":   COMPETITOR,
    }

    for filename, content in workflows.items():
        (base / filename).write_text(content.strip())
        print(f"✅ {filename}")

    print(SECRETS)
    print(f"\n✅ {len(workflows)} workflow files created.")
    print("Push to GitHub and add secrets. All bots run automatically.")
