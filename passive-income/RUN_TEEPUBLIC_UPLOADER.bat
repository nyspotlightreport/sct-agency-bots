@echo off
echo ╔══════════════════════════════════╗
echo ║  TEEPUBLIC UPLOADER — NYSR       ║
echo ╚══════════════════════════════════╝
pip install playwright -q
playwright install chromium
curl -sSL "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/teepublic_uploader.py" -o teepublic_uploader.py
python teepublic_uploader.py
pause