@echo off
chcp 65001 > nul
echo Teepublic Uploader - NY Spotlight Report
echo ==========================================
pip install playwright -q
playwright install chromium
curl -L -o teepublic_uploader.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/teepublic_uploader.py"
python teepublic_uploader.py
pause