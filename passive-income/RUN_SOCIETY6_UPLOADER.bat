@echo off
chcp 65001 > nul
echo Society6 Uploader - NY Spotlight Report
echo ==========================================
pip install playwright -q
playwright install chromium
curl -L -o society6_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/society6_uploader.py"
python society6_uploader.py
pause