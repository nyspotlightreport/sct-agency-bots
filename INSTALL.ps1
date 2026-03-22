# ================================================================
# AGENCY SYSTEM — WINDOWS POWERSHELL INSTALLER
# S.C. Thomas Internal Agency v2.0
# Run: Right-click -> "Run with PowerShell" OR paste into PowerShell
# ================================================================

$ErrorActionPreference = "Stop"
$REPO_NAME = "sct-agency-bots"

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  S.C. THOMAS AGENCY SYSTEM INSTALLER    ║" -ForegroundColor Cyan
Write-Host "║  v2.0 — Windows Edition                 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── STEP 1: CHECK / INSTALL DEPENDENCIES ──────────────────────────────────────
Write-Host "[ 1/4 ] Checking dependencies..." -ForegroundColor Yellow

# Check Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  Git not found. Installing via winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}
Write-Host "  [OK] git" -ForegroundColor Green

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  Python not found. Installing via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.11 -e --source winget --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}
Write-Host "  [OK] python" -ForegroundColor Green

# Check GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "  GitHub CLI not found. Installing via winget..." -ForegroundColor Yellow
    winget install --id GitHub.cli -e --source winget --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}
Write-Host "  [OK] GitHub CLI" -ForegroundColor Green

# ── STEP 2: GITHUB AUTH ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 2/4 ] GitHub login..." -ForegroundColor Yellow

$ghStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Opening GitHub login in browser..." -ForegroundColor Yellow
    gh auth login --web --git-protocol https
}
$GITHUB_USER = gh api user --jq .login
Write-Host "  [OK] Logged in as: $GITHUB_USER" -ForegroundColor Green

# ── STEP 3: CREATE REPO AND PUSH ──────────────────────────────────────────────
Write-Host ""
Write-Host "[ 3/4 ] Creating repo and pushing code..." -ForegroundColor Yellow

# Navigate to the installer's directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# Create GitHub repo
gh repo create $REPO_NAME --private --description "S.C. Thomas Internal Agency Bot System v2.0" 2>$null
Write-Host "  [OK] Repo created" -ForegroundColor Green

# Init and push
git init 2>$null
git add .
git commit -m "Agency System v2.0 — Initial deployment" 2>$null
git branch -M main 2>$null
git remote remove origin 2>$null
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
git push -u origin main --force

Write-Host "  [OK] Code pushed to github.com/$GITHUB_USER/$REPO_NAME" -ForegroundColor Green

# ── STEP 4: ADD SECRETS ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ 4/4 ] Adding secrets (enter each API key)..." -ForegroundColor Yellow
Write-Host "        Press Enter to skip optional ones." -ForegroundColor Gray
Write-Host ""

function Add-Secret {
    param($Name, $Prompt, $Default = "", $Required = $false)

    Write-Host "  $Name" -ForegroundColor Cyan
    Write-Host "  -> $Prompt" -ForegroundColor Gray
    if ($Default) {
        $Value = Read-Host "  Value [$Default]"
        if (-not $Value) { $Value = $Default }
    } else {
        $Value = Read-Host "  Value"
    }

    if ($Value) {
        $Value | gh secret set $Name --repo "$GITHUB_USER/$REPO_NAME"
        Write-Host "  [OK] $Name set" -ForegroundColor Green
    } else {
        if ($Required) { Write-Host "  [!] WARNING: $Name is required for full functionality" -ForegroundColor Red }
        Write-Host "  [--] Skipped" -ForegroundColor Gray
    }
    Write-Host ""
}

Add-Secret "ANTHROPIC_API_KEY"  "console.anthropic.com -> API Keys" "" $true
Add-Secret "GMAIL_USER"         "Your Gmail address" "nyspotlightreport@gmail.com" $true
Add-Secret "GMAIL_APP_PASS"     "myaccount.google.com/apppasswords -> Create (Mail app password)" "" $true
Add-Secret "CHAIRMAN_EMAIL"     "Email to receive all reports" "nyspotlightreport@gmail.com" $true
Add-Secret "AHREFS_API_KEY"     "ahrefs.com/api -> API Key" ""
Add-Secret "HUBSPOT_API_KEY"    "HubSpot -> Settings -> Private Apps -> Create" ""
Add-Secret "APOLLO_API_KEY"     "Apollo.io -> Settings -> Integrations -> API" ""
Add-Secret "TARGET_DOMAIN"      "Your domain e.g. yourdomain.com (no https://)" ""
Add-Secret "MONITORED_SITES"    "Comma-separated e.g. https://site1.com,https://site2.com" ""
Add-Secret "PAYPAL_ME_LINK"     "e.g. https://paypal.me/yourhandle" ""

# ── DONE ──────────────────────────────────────────────────────────────────────
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  AGENCY SYSTEM DEPLOYED                 ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Repo:    https://github.com/$GITHUB_USER/$REPO_NAME" -ForegroundColor Cyan
Write-Host "  Actions: https://github.com/$GITHUB_USER/$REPO_NAME/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Schedules:" -ForegroundColor White
Write-Host "  Every 15 min  -> Uptime monitor"
Write-Host "  Daily 7am ET  -> Inbox triage + invoice reminders"
Write-Host "  Monday 8am ET -> Weekly KPI report to your email"
Write-Host "  Mon+Thu 9am   -> SEO rank tracker"
Write-Host "  Tuesday noon  -> Lead pipeline"
Write-Host "  Sunday 11pm   -> Competitor monitor"
Write-Host "  Sunday 6am    -> Self-improvement engine"
Write-Host ""
Write-Host "  Cost: `$0/month (GitHub free tier)" -ForegroundColor Green
Write-Host ""

# Open the Actions page
$Open = Read-Host "Open GitHub Actions page now? (y/n)"
if ($Open -eq "y") {
    Start-Process "https://github.com/$GITHUB_USER/$REPO_NAME/actions"
}
