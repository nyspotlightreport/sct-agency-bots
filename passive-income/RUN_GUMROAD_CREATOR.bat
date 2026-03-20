@echo off
chcp 65001 > nul
echo ==========================================
echo   GUMROAD PRODUCT CREATOR - 10 new items
echo ==========================================
echo.
pip install playwright -q
playwright install chromium
curl -L -o gumroad_creator.py "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/gumroad_product_creator.py"
echo.
python gumroad_creator.py
pause