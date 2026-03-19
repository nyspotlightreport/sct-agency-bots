#!/bin/bash
# ================================================================
# AGENCY SYSTEM DEPLOY SCRIPT
# S.C. Thomas Internal Agency v2.0
# Run this ONCE to push everything to GitHub
# ================================================================
# USAGE:
#   chmod +x setup_and_push.sh
#   ./setup_and_push.sh YOUR_GITHUB_USERNAME
# ================================================================

GITHUB_USERNAME=${1:-"YOUR_GITHUB_USERNAME"}
REPO_NAME="sct-agency-bots"

echo "================================================"
echo "  S.C. Thomas Agency System — Deploy Script"
echo "================================================"
echo ""

# Check git installed
if ! command -v git &> /dev/null; then
    echo "❌ git not found. Install from https://git-scm.com"
    exit 1
fi

# Check we're in the right directory
if [ ! -f "bots/agency_core.py" ]; then
    echo "❌ Run this from the agency-deploy/ directory"
    exit 1
fi

echo "Step 1: Initializing git repo..."
git init
git add .
git commit -m "Agency System v2.0 — Initial deployment"
echo "✅ Git initialized"
echo ""

echo "Step 2: Creating GitHub repo..."
echo "→ Opening GitHub new repo page..."
echo "→ Go to: https://github.com/new"
echo "→ Repo name: $REPO_NAME"
echo "→ Set to PRIVATE"
echo "→ Do NOT add README (we have one)"
echo "→ Click Create repository"
echo ""
read -p "Press ENTER when repo is created..."
echo ""

echo "Step 3: Pushing code..."
git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Code pushed to GitHub!"
else
    echo "❌ Push failed. Check your GitHub credentials."
    echo "   You may need: git config --global credential.helper store"
    exit 1
fi

echo ""
echo "================================================"
echo "  STEP 4: ADD SECRETS (do this now)"
echo "================================================"
echo ""
echo "Go to: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/settings/secrets/actions"
echo ""
echo "Add these secrets (Name → Value):"
echo ""
echo "  ANTHROPIC_API_KEY    → Your key from console.anthropic.com"
echo "  GMAIL_USER           → seanb041992@gmail.com"
echo "  GMAIL_APP_PASS       → Get from: myaccount.google.com/apppasswords"
echo "  CHAIRMAN_EMAIL       → seanb041992@gmail.com"
echo "  AHREFS_API_KEY       → From ahrefs.com/api"
echo "  HUBSPOT_API_KEY      → From HubSpot → Settings → Private Apps"
echo "  APOLLO_API_KEY       → From Apollo.io → Settings → API"
echo "  TARGET_DOMAIN        → yourdomain.com (no https://)"
echo "  MONITORED_SITES      → https://site1.com,https://site2.com"
echo "  PAYPAL_ME_LINK       → https://paypal.me/yourhandle"
echo ""
echo "================================================"
echo "  DONE. Bots will start running automatically."
echo "================================================"
echo ""
echo "Schedules:"
echo "  Every 15 min  → Uptime monitor"
echo "  Daily 7am ET  → Inbox triage + invoice reminders"
echo "  Monday 8am ET → Weekly KPI report"
echo "  Mon+Thu 9am   → SEO rank tracker"
echo "  Tuesday noon  → Lead pipeline"
echo "  Sunday 11pm   → Competitor monitor"
echo "  Sunday 6am    → Self-improvement engine"
echo ""
echo "Repo: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
