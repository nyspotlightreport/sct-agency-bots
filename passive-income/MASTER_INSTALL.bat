@echo off
chcp 65001 > nul
echo ============================================================
echo   NYSR MASTER INSTALLER - ProFlow Digital Income Stack
echo   Running all passive income setup scripts
echo ============================================================
echo.

cd /d %USERPROFILE%

echo [1/6] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo Python not found. Install from python.org then re-run.
    pause
    exit /b 1
)

echo [2/6] Installing requirements...
pip install playwright requests fpdf2 -q
playwright install chromium 2>nul

echo [3/6] Downloading all scripts...
curl -L -o kdp_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/kdp_uploader.py"
curl -L -o redbubble_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/redbubble_uploader.py"
curl -L -o teepublic_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/teepublic_uploader.py"
curl -L -o gumroad_creator.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/gumroad_product_creator.py"
curl -L -o money4band_setup.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/money4band_setup.py"
curl -L -o promptbase_setup.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/promptbase_setup.py"

echo.
echo ============================================================
echo   SELECT WHAT TO RUN:
echo   1) KDP Books Upload (20 min, $50/mo)
echo   2) Redbubble Designs (30 min, $80/mo)
echo   3) Teepublic Designs (30 min, $60/mo)
echo   4) Gumroad Products (10 min, $120/mo)
echo   5) money4band Bandwidth Stack ($60/mo)
echo   6) Run ALL
echo ============================================================
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" python kdp_uploader.py
if "%choice%"=="2" python redbubble_uploader.py
if "%choice%"=="3" python teepublic_uploader.py
if "%choice%"=="4" python gumroad_creator.py
if "%choice%"=="5" python money4band_setup.py
if "%choice%"=="6" (
    echo Running all uploaders in sequence...
    python kdp_uploader.py
    python redbubble_uploader.py
    python teepublic_uploader.py
    python gumroad_creator.py
    python money4band_setup.py
)

echo.
echo Done! Check each platform for live products.
pause
