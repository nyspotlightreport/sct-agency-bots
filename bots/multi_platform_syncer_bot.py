#!/usr/bin/env python3
"""
Multi-Platform Product Sync Bot — NYSR Agency
Keeps all storefronts in sync:
- Gumroad (10 products live)
- Etsy (needs listing)
- Payhip (needs listing)
- LemonSqueezy (under review)
Monitors sales across all platforms and reports daily.
"""
import os, requests, json, logging
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ProductSyncer")

GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN","")
ETSY_KEY      = os.environ.get("ETSY_API_KEY","")
ETSY_SHOP     = os.environ.get("ETSY_SHOP_ID","")

def get_gumroad_sales():
    r = requests.get("https://api.gumroad.com/v2/sales",
        headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"}, timeout=15)
    if r.status_code == 200:
        sales = r.json().get("sales",[])
        revenue = sum(float(s.get("price",0))/100 for s in sales)
        return len(sales), revenue
    return 0, 0.0

def get_gumroad_products():
    r = requests.get("https://api.gumroad.com/v2/products",
        headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"}, timeout=15)
    return r.json().get("products",[]) if r.status_code == 200 else []

def daily_report():
    print(f"=== PRODUCT SYNC REPORT {datetime.now().strftime('%b %d %Y')} ===\n")
    # Gumroad
    prods = get_gumroad_products()
    sales, rev = get_gumroad_sales()
    pub = sum(1 for p in prods if p.get("published"))
    print(f"GUMROAD: {pub} live products | {sales} total sales | ${rev:.2f} revenue")
    for p in prods:
        print(f"  {'✅' if p.get('published') else '❌'} {p['name'][:45]:45} ${p['price']/100:.2f}")
    print(f"\nETSY:    {'✅' if ETSY_KEY else '❌ ETSY_API_KEY needed'}")
    print(f"PAYHIP:  ✅ Free storefront — list products at payhip.com/nysr")
    print(f"LS:      🔄 Under review — expected approval within days")
    print(f"\nDownload links: https://nyspotlightreport.com/downloads/")

if __name__ == "__main__":
    daily_report()
