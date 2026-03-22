#!/bin/bash
# ================================================================
# AUTO GITHUB SETUP — Uses GitHub CLI (gh)
# Run: bash auto_github_setup.sh
# ================================================================

REPO_NAME="sct-agency-bots"
GITHUB_USER=$(gh api user --jq .login 2>/dev/null)

if [ -z "$GITHUB_USER" ]; then
    echo "❌ GitHub CLI not logged in."
    echo "Run: gh auth login"
    echo "Then re-run this script."
    exit 1
fi

echo "✅ Logged in as: $GITHUB_USER"
echo "Creating private repo: $REPO_NAME..."

# Create the repo
gh repo create "$REPO_NAME" --private --description "S.C. Thomas Internal Agency Bot System v2.0" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Repo created: https://github.com/$GITHUB_USER/$REPO_NAME"
else
    echo "Repo may already exist — continuing with push..."
fi

# Init git and push
git init
git add .
git commit -m "Agency System v2.0 — Initial deployment"
git branch -M main
git remote remove origin 2>/dev/null
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
git push -u origin main

echo ""
echo "✅ CODE PUSHED"
echo ""
echo "NOW ADD SECRETS AT:"
echo "https://github.com/$GITHUB_USER/$REPO_NAME/settings/secrets/actions"
echo ""
echo "Open secrets page now? (y/n)"
read -r OPEN
if [ "$OPEN" = "y" ]; then
    open "https://github.com/$GITHUB_USER/$REPO_NAME/settings/secrets/actions" 2>/dev/null || \
    xdg-open "https://github.com/$GITHUB_USER/$REPO_NAME/settings/secrets/actions" 2>/dev/null || \
    echo "Go to: https://github.com/$GITHUB_USER/$REPO_NAME/settings/secrets/actions"
fi
