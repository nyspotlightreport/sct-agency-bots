#!/bin/bash
# ================================================================
# AGENCY SYSTEM — ONE COMMAND INSTALLER
# Usage: bash INSTALL.sh
# Does everything: checks deps, creates repo, pushes, adds secrets
# ================================================================
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  S.C. THOMAS AGENCY SYSTEM INSTALLER    ║"
echo "║  v2.0 — Full Automated Deployment       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── STEP 1: CHECK DEPENDENCIES ─────────────────────────────────
echo "[ 1/4 ] Checking dependencies..."

if ! command -v git &>/dev/null; then
    echo "❌ git not found. Install: https://git-scm.com"
    exit 1
fi
echo "  ✅ git found"

if ! command -v python3 &>/dev/null; then
    echo "❌ python3 not found. Install: https://python.org"
    exit 1
fi
echo "  ✅ python3 found"

if ! command -v gh &>/dev/null; then
    echo "  ⚠️  GitHub CLI not found — installing..."
    # macOS
    if command -v brew &>/dev/null; then
        brew install gh
    # Linux
    elif command -v apt &>/dev/null; then
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update && sudo apt install gh -y
    else
        echo "  Install GitHub CLI manually: https://cli.github.com"
        echo "  Then run: gh auth login"
        echo "  Then re-run this installer."
        exit 1
    fi
fi
echo "  ✅ GitHub CLI found"

# ── STEP 2: GITHUB AUTH ────────────────────────────────────────
echo ""
echo "[ 2/4 ] GitHub authentication..."
if ! gh auth status &>/dev/null; then
    echo "  You need to log in to GitHub."
    echo "  Running: gh auth login"
    gh auth login
fi
GITHUB_USER=$(gh api user --jq .login)
echo "  ✅ Logged in as: $GITHUB_USER"

# ── STEP 3: CREATE REPO AND PUSH ───────────────────────────────
echo ""
echo "[ 3/4 ] Creating GitHub repo and pushing code..."
REPO_NAME="sct-agency-bots"

gh repo create "$REPO_NAME" --private \
    --description "S.C. Thomas Internal Agency Bot System v2.0" 2>/dev/null \
    && echo "  ✅ Repo created" \
    || echo "  ℹ️  Repo exists — continuing"

git init -q 2>/dev/null || true
git add .
git commit -qm "Agency System v2.0 — Initial deployment" 2>/dev/null || true
git branch -M main 2>/dev/null || true
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
git push -u origin main -q

echo "  ✅ Code pushed to github.com/$GITHUB_USER/$REPO_NAME"

# ── STEP 4: ADD SECRETS ────────────────────────────────────────
echo ""
echo "[ 4/4 ] Adding secrets..."
echo "  You'll enter each API key. Press Enter to skip optional ones."
echo ""

add_secret() {
    local name=$1 prompt=$2 default=$3 required=$4
    printf "  %-25s → %s\n" "$name" "$prompt"
    if [ -n "$default" ]; then
        read -p "    Value [${default}]: " VALUE
        VALUE=${VALUE:-$default}
    else
        read -p "    Value: " VALUE
    fi
    if [ -n "$VALUE" ]; then
        printf "%s" "$VALUE" | gh secret set "$name" --repo "$GITHUB_USER/$REPO_NAME" -b -
        echo "    ✅ Set"
    else
        [ "$required" = "required" ] && echo "    ⚠️  WARNING: This is required for full functionality"
        echo "    ⏭  Skipped"
    fi
}

add_secret "ANTHROPIC_API_KEY"  "console.anthropic.com → API Keys"                              "" "required"
add_secret "GMAIL_USER"         "Your Gmail"                                                     "seanb041992@gmail.com" "required"
add_secret "GMAIL_APP_PASS"     "myaccount.google.com/apppasswords (create Mail app password)"  "" "required"
add_secret "CHAIRMAN_EMAIL"     "Where to send all reports"                                      "seanb041992@gmail.com" "required"
add_secret "AHREFS_API_KEY"     "ahrefs.com/api"                                                 "" ""
add_secret "HUBSPOT_API_KEY"    "HubSpot → Settings → Private Apps"                             "" ""
add_secret "APOLLO_API_KEY"     "Apollo.io → Settings → API"                                    "" ""
add_secret "TARGET_DOMAIN"      "yourdomain.com (no https://)"                                  "" ""
add_secret "MONITORED_SITES"    "https://site1.com,https://site2.com"                           "" ""
add_secret "PAYPAL_ME_LINK"     "https://paypal.me/yourhandle"                                  "" ""

# ── DONE ───────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ AGENCY SYSTEM DEPLOYED               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Repo: https://github.com/$GITHUB_USER/$REPO_NAME"
echo "  Actions: https://github.com/$GITHUB_USER/$REPO_NAME/actions"
echo ""
echo "  What happens next:"
echo "  • Every 15 min  → Uptime monitor"
echo "  • Daily 7am ET  → Inbox triage + invoice reminders"
echo "  • Monday 8am ET → Weekly KPI report to your email"
echo "  • Mon+Thu 9am   → SEO rank tracker"
echo "  • Tuesday noon  → Lead pipeline"
echo "  • Sunday 11pm   → Competitor monitor"
echo "  • Sunday 6am    → Self-improvement engine"
echo ""
echo "  Cost: \$0/month (GitHub free tier)"
echo ""
