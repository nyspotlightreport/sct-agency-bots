#!/bin/bash
# deploy/setup_github_runner.sh
# Install GitHub Actions self-hosted runner on VPS.
# Eliminates: 20-job concurrent limit, 6-hour timeout, cold starts.
# Run on VPS: bash setup_github_runner.sh
# -----------------------------------------------------------
set -e

REPO_URL="https://github.com/nyspotlightreport/sct-agency-bots"
RUNNER_VERSION="2.321.0"

echo "=== NYSR Self-Hosted Runner Setup ==="
echo "Removes all GitHub Actions free tier limits"
echo ""

# Create runner directory
mkdir -p /opt/nysr/github-runner
cd /opt/nysr/github-runner

# Download runner
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L   https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

echo ""
echo "MANUAL STEP REQUIRED (one-time, 2 minutes):"
echo "1. Go to: https://github.com/nyspotlightreport/sct-agency-bots/settings/actions/runners/new"
echo "2. Click 'New self-hosted runner'"
echo "3. Copy the token shown on that page"
echo "4. Run: ./config.sh --url ${REPO_URL} --token YOUR_TOKEN_HERE --name nysr-vps --work _work"
echo "5. Run: sudo ./svc.sh install && sudo ./svc.sh start"
echo ""
echo "AFTER SETUP: All workflows with 'runs-on: self-hosted' will use VPS."
echo "Benefits: No concurrent limits, no 6hr timeout, instant start, no bandwidth limits."
echo ""
echo "Update cashflow_emergency.yml to use: runs-on: self-hosted"
