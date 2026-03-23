#!/usr/bin/env python3
# Automation Engineer Agent - GitHub Actions, CI/CD, workflow automation, monitoring.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

WORKFLOW_TEMPLATES = {
    "daily_bot": "name: Daily Bot
on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install requests -q
      - run: python bots/BOT_NAME.py",
    "deploy":    "name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g vercel
      - run: vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }}",
    "test":      "name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install pytest pytest-cov
      - run: pytest --cov=. --cov-report=xml",
}

def generate_workflow(bot_name, schedule="0 9 * * *", env_vars=None):
    env_section = ""
    if env_vars:
        env_section = "env:
" + "
".join([f"  {k}: ${{{{ secrets.{k} }}}}" for k in env_vars])
    return f"name: {bot_name.replace('_',' ').title()}
on:
  schedule:
    - cron: '{schedule}'
  workflow_dispatch:
{env_section}
jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {{python-version: '3.11'}}
      - run: pip install requests anthropic -q
      - name: Run {bot_name}
        run: python bots/{bot_name}.py
        continue-on-error: true"

def audit_workflows():
    return claude_json(
        "Audit a GitHub Actions workflow setup. Return JSON: {best_practices:[],missing:[],recommendations:[]}",
        "NYSR repo has 80+ workflows running daily bots, CRM sync, deploy, and monitoring.",
        max_tokens=300
    ) or {"best_practices":["Use continue-on-error","Set timeouts","Use actions/cache"],"missing":["Test workflow","Notification on failure"]}

def run():
    wf = generate_workflow("crm_core_agent","0 9 * * *",["ANTHROPIC_API_KEY","APOLLO_API_KEY","HUBSPOT_API_KEY","SUPABASE_URL","SUPABASE_KEY"])
    log.info(f"Generated workflow: {len(wf)} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
