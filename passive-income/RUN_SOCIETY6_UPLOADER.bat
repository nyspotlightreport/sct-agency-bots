@echo off
echo ╔══════════════════════════════════╗
echo ║  SOCIETY6 UPLOADER — NYSR        ║
echo ╚══════════════════════════════════╝
pip install playwright -q
playwright install chromium
curl -sSL "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/society6_uploader.py" -o society6_uploader.py
python society6_uploader.py
pause