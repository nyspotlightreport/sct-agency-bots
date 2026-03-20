@echo off
echo ╔══════════════════════════════════════════════════╗
echo ║      NYSR REDBUBBLE DESIGN UPLOADER             ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo Installing requirements...
pip install playwright -q
playwright install chromium
echo.
echo Downloading uploader...
curl -sSL "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/redbubble_uploader.py" -o redbubble_uploader.py
echo.
echo Starting uploader...
python redbubble_uploader.py
pause
