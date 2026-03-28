# ============================================================
# GITHUB ACTIONS DEPLOYMENT — All Agency Bots
# S.C. Thomas Internal Agency
# ============================================================
# How to use:
# 1. Create a GitHub repo (can be private)
# 2. Upload all bot .py files to /bots/ folder
# 3. Create .github/workflows/ folder
# 4. Add each .yml file below as a separate file
# 5. Go to repo Settings → Secrets → add all API keys
# ============================================================

# ─────────────────────────────────────────────────────────────
# FILE: .github/workflows/weekly-report.yml
# ─────────────────────────────────────────────────────────────
WEEKLY_REPORT_YML = """
name: Weekly Report Bot
on:
  schedule:
    - cron: '0 13 * * 1'   # Every Monday 1pm UTC (8am ET)
  workflow_dispatch:         # Manual trigger from GitHub UI

jobs:
  weekly-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install schedule requests
      - name: Run weekly report
        run: python bots/weekly_report_bot.py --now
        env:
# AG-NUCLEAR-GMAIL-ZERO-20260328:           GMAIL_USER:       ${{ secrets.GMAIL_USER }}
# AG-NUCLEAR-GMAIL-ZERO-20260328:           GMAIL_APP_PASS:   ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:   ${{ secrets.CHAIRMAN_EMAIL }}
          AHREFS_API_KEY:   ${{ secrets.AHREFS_API_KEY }}
          HUBSPOT_API_KEY:  ${{ secrets.HUBSPOT_API_KEY }}
          TARGET_DOMAIN:    ${{ secrets.TARGET_DOMAIN }}
"""

# ─────────────────────────────────────────────────────────────
# FILE: .github/workflows/competitor-monitor.yml
# ─────────────────────────────────────────────────────────────
COMPETITOR_MONITOR_YML = """
name: Competitor Monitor Bot
on:
  schedule:
    - cron: '0 23 * * 0'   # Every Sunday 11pm UTC
  workflow_dispatch:

jobs:
  competitor-monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Restore state
        uses: actions/cache@v3
        with:
          path: competitor_state.json
          key: competitor-state-${{ github.run_id }}
          restore-keys: competitor-state-
      - name: Install deps
        run: pip install requests
      - name: Run monitor
        run: python bots/competitor_monitor_bot.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
# AG-NUCLEAR-GMAIL-ZERO-20260328:           GMAIL_USER:        ${{ secrets.GMAIL_USER }}
# AG-NUCLEAR-GMAIL-ZERO-20260328:           GMAIL_APP_PASS:    ${{ secrets.GMAIL_APP_PASS }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}
"""

# ─────────────────────────────────────────────────────────────
# FILE: .github/workflows/lead-pipeline.yml
# ─────────────────────────────────────────────────────────────
LEAD_PIPELINE_YML = """
name: Lead Pipeline Bot
on:
  schedule:
    - cron: '0 12 * * 2'   # Every Tuesday noon UTC
  workflow_dispatch:
    inputs:
      search_query:
        description: 'Apollo search query'
        required: false
        default: 'founder CEO media company New York'
      limit:
        description: 'Number of leads'
        required: false
        default: '25'

jobs:
  lead-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install requests
      - name: Run lead pipeline
        run: |
          python bots/lead_pipeline_bot.py \\
            --search "${{ github.event.inputs.search_query || 'founder CEO media company New York' }}" \\
            --limit ${{ github.event.inputs.limit || '25' }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          APOLLO_API_KEY:    ${{ secrets.APOLLO_API_KEY }}
          HUBSPOT_API_KEY:   ${{ secrets.HUBSPOT_API_KEY }}
          CHAIRMAN_EMAIL:    ${{ secrets.CHAIRMAN_EMAIL }}
      - name: Upload lead results
        uses: actions/upload-artifact@v3
        with:
          name: lead-results
          path: leads_*.json
          retention-days: 30
"""

# ─────────────────────────────────────────────────────────────
# FILE: .github/workflows/content-repurpose.yml  
# ─────────────────────────────────────────────────────────────
CONTENT_REPURPOSE_YML = """
name: Content Repurpose Bot
on:
  workflow_dispatch:
    inputs:
      content:
        description: 'Content to repurpose'
        required: true
      title:
        description: 'Content title'
        required: false
        default: 'content'
      platforms:
        description: 'Platforms (comma-separated: twitter_thread,linkedin_post,email_newsletter)'
        required: false
        default: 'all'

jobs:
  repurpose:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install requests
      - name: Repurpose content
        run: |
          python bots/content_repurpose_bot.py \\
            --input "${{ github.event.inputs.content }}" \\
            --title "${{ github.event.inputs.title }}"
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Upload repurposed content
        uses: actions/upload-artifact@v3
        with:
          name: repurposed-content
          path: repurposed_content/
          retention-days: 14
"""

# ─────────────────────────────────────────────────────────────
# SECRETS TO ADD IN GITHUB REPO SETTINGS
# ─────────────────────────────────────────────────────────────
REQUIRED_SECRETS = """
Go to: GitHub Repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
  ANTHROPIC_API_KEY    = your Anthropic API key
# AG-NUCLEAR-GMAIL-ZERO-20260328:   GMAIL_USER           = nyspotlightreport@gmail.com
# AG-NUCLEAR-GMAIL-ZERO-20260328:   GMAIL_APP_PASS       = Gmail App Password (not regular password)
                         Get at: myaccount.google.com/apppasswords
  CHAIRMAN_EMAIL       = nyspotlightreport@gmail.com
  AHREFS_API_KEY       = Ahrefs API key (from ahrefs.com/api)
  HUBSPOT_API_KEY      = HubSpot private app token
  APOLLO_API_KEY       = Apollo.io API key
  TARGET_DOMAIN        = yourdomain.com (for SEO tracking)
"""

if __name__ == "__main__":
    import os
    from pathlib import Path

    base = Path(".github/workflows")
    base.mkdir(parents=True, exist_ok=True)

    workflows = {
        "weekly-report.yml":       WEEKLY_REPORT_YML,
        "competitor-monitor.yml":  COMPETITOR_MONITOR_YML,
        "lead-pipeline.yml":       LEAD_PIPELINE_YML,
        "content-repurpose.yml":   CONTENT_REPURPOSE_YML,
    }

    for filename, content in workflows.items():
        with open(base / filename, "w") as f:
            f.write(content.strip())
        print(f"✅ Created: .github/workflows/{filename}")

    print("\n" + REQUIRED_SECRETS)
    print("✅ All GitHub Actions workflows created.")
    print("Push to GitHub and add secrets — bots will run automatically.")
