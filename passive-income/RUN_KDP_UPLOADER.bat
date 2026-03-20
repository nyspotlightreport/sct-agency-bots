@echo off
echo ╔══════════════════════════════════════════════════╗
echo ║        NYSR KDP BOOK UPLOADER                   ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo Installing requirements...
pip install playwright -q
playwright install chromium
echo.
echo Downloading KDP uploader...
curl -sSL "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/kdp_uploader.py" -o kdp_uploader.py
echo.
echo Starting uploader...
python kdp_uploader.py
pause
