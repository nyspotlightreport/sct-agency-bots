@echo off
echo ╔══════════════════════════════════════╗
echo ║  GUMROAD PRODUCT CREATOR — 10 new   ║
echo ╚══════════════════════════════════════╝
pip install playwright -q
playwright install chromium
curl -sSL "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/gumroad_product_creator.py" -o gumroad_creator.py
python gumroad_creator.py
pause