@echo off
chcp 65001 > nul
echo Redbubble Design Uploader - NY Spotlight Report
echo =================================================
pip install playwright -q
playwright install chromium
curl -L -o redbubble_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/redbubble_uploader.py"
python redbubble_uploader.py
pause