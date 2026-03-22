#!/bin/bash
# ================================================================
# SECRETS BATCH ADDER — Uses GitHub CLI
# Run AFTER creating repo: bash add_secrets.sh
# You'll be prompted for each value
# ================================================================

REPO_NAME="sct-agency-bots"
GITHUB_USER=$(gh api user --jq .login 2>/dev/null)

if [ -z "$GITHUB_USER" ]; then
    echo "❌ Run: gh auth login first"
    exit 1
fi

REPO="$GITHUB_USER/$REPO_NAME"
echo "Adding secrets to: $REPO"
echo ""

add_secret() {
    local name=$1
    local prompt=$2
    local default=$3

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Secret: $name"
    echo "→ $prompt"
    if [ -n "$default" ]; then
        echo "→ Default: $default"
        read -p "Value (press Enter to use default): " VALUE
        VALUE=${VALUE:-$default}
    else
        read -p "Value: " VALUE
    fi

    if [ -n "$VALUE" ]; then
        echo "$VALUE" | gh secret set "$name" --repo "$REPO"
        echo "✅ $name set"
    else
        echo "⚠️  Skipped $name"
    fi
    echo ""
}

add_secret "ANTHROPIC_API_KEY"   "Get from: console.anthropic.com → API Keys" ""
add_secret "GMAIL_USER"          "Your Gmail address" "nyspotlightreport@gmail.com"
add_secret "GMAIL_APP_PASS"      "Get from: myaccount.google.com/apppasswords (create 'Mail' app password)" ""
add_secret "CHAIRMAN_EMAIL"      "Email to receive all reports" "nyspotlightreport@gmail.com"
add_secret "AHREFS_API_KEY"      "Get from: ahrefs.com/api" ""
add_secret "HUBSPOT_API_KEY"     "Get from: HubSpot → Settings → Integrations → Private Apps → Create App" ""
add_secret "APOLLO_API_KEY"      "Get from: Apollo.io → Settings → Integrations → API" ""
add_secret "TARGET_DOMAIN"       "Your main domain (no https://), e.g. yourdomain.com" ""
add_secret "MONITORED_SITES"     "Comma-separated sites to monitor, e.g. https://site1.com,https://site2.com" ""
add_secret "PAYPAL_ME_LINK"      "Your PayPal.me link, e.g. https://paypal.me/yourhandle" ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL SECRETS ADDED"
echo ""
echo "Verify at: https://github.com/$REPO/settings/secrets/actions"
echo ""
echo "Your bots are now LIVE and running on schedule."
echo "You'll start receiving emails automatically."
