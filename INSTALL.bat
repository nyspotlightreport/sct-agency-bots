@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
:: ================================================================
:: AGENCY SYSTEM INSTALLER — DOUBLE-CLICK TO RUN
:: S.C. Thomas Internal Agency v2.0
:: ================================================================
title Agency System Installer
color 0A

echo.
echo  ==========================================
echo   S.C. THOMAS AGENCY SYSTEM INSTALLER
echo   Double-click installer v2.0
echo  ==========================================
echo.
echo  This will install everything automatically.
echo  A browser window will open for GitHub login.
echo  Then you will be asked for your API keys.
echo.
pause

:: ── CHECK WINGET ──────────────────────────────────────────────
echo [1/5] Checking Windows Package Manager...
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: winget not found.
    echo Open Microsoft Store and install "App Installer"
    echo Then double-click this file again.
    pause
    exit /b 1
)
echo   OK - winget found
echo.

:: ── INSTALL GIT ───────────────────────────────────────────────
echo [2/5] Installing Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing Git...
    winget install --id Git.Git -e --source winget --silent --accept-package-agreements --accept-source-agreements
    :: Refresh PATH
    set "PATH=%PATH%;C:\Program Files\Git\cmd"
) else (
    echo   OK - Git already installed
)

:: ── INSTALL PYTHON ────────────────────────────────────────────
echo [3/5] Installing Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing Python...
    winget install --id Python.Python.3.11 -e --source winget --silent --accept-package-agreements --accept-source-agreements
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
) else (
    echo   OK - Python already installed
)

:: ── INSTALL GITHUB CLI ────────────────────────────────────────
echo [4/5] Installing GitHub CLI...
gh --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing GitHub CLI...
    winget install --id GitHub.cli -e --source winget --silent --accept-package-agreements --accept-source-agreements
    :: Refresh PATH after install
    for /f "tokens=*" %%i in ('where gh 2^>nul') do set "GH_PATH=%%i"
    if not defined GH_PATH set "PATH=%PATH%;C:\Program Files\GitHub CLI"
) else (
    echo   OK - GitHub CLI already installed
)
echo.

:: ── GITHUB LOGIN ──────────────────────────────────────────────
echo [5/5] Logging into GitHub...
echo   A browser window will open. Log in and authorize.
echo.
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    gh auth login --web --git-protocol https
) else (
    echo   OK - Already logged in
)

:: Get GitHub username
for /f "delims=" %%i in ('gh api user --jq .login 2^>nul') do set GITHUB_USER=%%i
if "%GITHUB_USER%"=="" (
    echo ERROR: Could not get GitHub username. Please try again.
    pause
    exit /b 1
)
echo   Logged in as: %GITHUB_USER%
echo.

:: ── CREATE REPO AND PUSH ──────────────────────────────────────
echo Creating GitHub repo: sct-agency-bots ...
set REPO_NAME=sct-agency-bots
set REPO=%GITHUB_USER%/%REPO_NAME%

gh repo create %REPO_NAME% --private --description "S.C. Thomas Internal Agency Bot System v2.0" 2>nul
echo   Repo ready at github.com/%REPO%

:: Init git in this directory
cd /d "%~dp0"
git init >nul 2>&1
git add . >nul 2>&1
git commit -m "Agency System v2.0 — Initial deployment" >nul 2>&1
git branch -M main >nul 2>&1
git remote remove origin >nul 2>&1
git remote add origin https://github.com/%REPO%.git >nul 2>&1
git push -u origin main --force
if %errorlevel% neq 0 (
    echo ERROR: Push failed. Check your GitHub login and try again.
    pause
    exit /b 1
)
echo   Code pushed successfully!
echo.

:: ── ADD SECRETS ───────────────────────────────────────────────
echo ==========================================
echo  NOW ENTERING YOUR API KEYS
echo  Press Enter to skip any you don't have
echo ==========================================
echo.

:: Helper to set a secret
:: Usage: call :set_secret SECRET_NAME "Prompt text" "default"

call :set_secret ANTHROPIC_API_KEY "Anthropic API Key (console.anthropic.com -> API Keys)" ""
call :set_secret GMAIL_USER "Your Gmail address" "seanb041992@gmail.com"
call :set_secret GMAIL_APP_PASS "Gmail App Password (myaccount.google.com/apppasswords)" ""
call :set_secret CHAIRMAN_EMAIL "Email for all reports" "seanb041992@gmail.com"
call :set_secret AHREFS_API_KEY "Ahrefs API Key (ahrefs.com/api) - press Enter to skip" ""
call :set_secret HUBSPOT_API_KEY "HubSpot API Key (HubSpot > Settings > Private Apps) - press Enter to skip" ""
call :set_secret APOLLO_API_KEY "Apollo.io API Key (Apollo > Settings > API) - press Enter to skip" ""
call :set_secret TARGET_DOMAIN "Your domain e.g. yourdomain.com (no https://) - press Enter to skip" ""
call :set_secret MONITORED_SITES "Sites to monitor e.g. https://yoursite.com - press Enter to skip" ""
call :set_secret PAYPAL_ME_LINK "PayPal.me link e.g. https://paypal.me/yourhandle - press Enter to skip" ""

:: ── DONE ──────────────────────────────────────────────────────
echo.
echo  ==========================================
echo   AGENCY SYSTEM IS LIVE
echo  ==========================================
echo.
echo  Repo: https://github.com/%REPO%
echo  Actions: https://github.com/%REPO%/actions
echo.
echo  What you'll receive automatically:
echo  - Daily 7am    : Inbox triage digest
echo  - Monday 8am   : Weekly KPI report  
echo  - Mon+Thu 9am  : SEO rank report
echo  - Tuesday noon : Lead pipeline results
echo  - Immediately  : Site down alerts
echo  - Sunday 6am   : Self-improvement report
echo.
echo  Cost: $0/month
echo.

:: Open GitHub Actions in browser
echo Opening GitHub Actions page...
start https://github.com/%REPO%/actions

echo Press any key to close.
pause >nul
exit /b 0

:: ── SUBROUTINE: SET SECRET ────────────────────────────────────
:set_secret
set SECRET_NAME=%~1
set SECRET_PROMPT=%~2
set SECRET_DEFAULT=%~3

echo  %SECRET_NAME%
echo  -> %SECRET_PROMPT%
if not "%SECRET_DEFAULT%"=="" (
    set /p SECRET_VALUE="  Value [%SECRET_DEFAULT%]: "
    if "!SECRET_VALUE!"=="" set SECRET_VALUE=%SECRET_DEFAULT%
) else (
    set /p SECRET_VALUE="  Value: "
)

if not "!SECRET_VALUE!"=="" (
    echo !SECRET_VALUE! | gh secret set %SECRET_NAME% --repo %REPO%
    echo   OK - %SECRET_NAME% set
) else (
    echo   Skipped %SECRET_NAME%
)
echo.
goto :eof
