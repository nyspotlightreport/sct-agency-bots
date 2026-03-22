@echo off
chcp 65001 > nul
echo KDP Book Uploader - NY Spotlight Report
echo ========================================
pip install playwright -q
playwright install chromium
curl -L -o kdp_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/kdp_uploader.py"
python kdp_uploader.py
pause