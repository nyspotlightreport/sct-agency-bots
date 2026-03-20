#!/usr/bin/env python3
"""
STRIPE REVENUE BOT v2.0 — S.C. Thomas Internal Agency
UPGRADED: Creates products/prices automatically, payment link generator,
MRR tracking, dunning emails, revenue dashboard
"""
import os, sys, json, urllib.request, urllib.parse, time
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, AlertSystem, with_retry

KEY  = os.getenv("STRIPE_SECRET_KEY","")
BASE = "https://api.stripe.com/v1"

# Pre-defined products to auto-create if they don't exist
PRODUCTS = [
    {"name":"NY Spotlight Report — Newsletter",    "price":999,   "interval":"month", "desc":"Premium media newsletter"},
    {"name":"SCT Agency Content Package",          "price":2999,  "interval":"month", "desc":"Monthly content strategy package"},
    {"name":"Media Consulting — 1hr Session",      "price":15000, "interval":None,    "desc":"1-hour strategy consultation"},
    {"name":"Agency Bot System License",           "price":4999,  "interval":"month", "desc":"Full bot system access"},
    {"name":"Press Release Distribution",          "price":29900, "interval":None,    "desc":"Multi-platform press distribution"},
]

class StripeRevenueBot(BaseBot):
    VERSION = "2.0.0"

    def _req(self, method, path, data=None):
        url  = f"{BASE}{path}"
        body = urllib.parse.urlencode(data).encode() if data else None
        req  = urllib.request.Request(url, data=body, method=method,
            headers={"Authorization":f"Bearer {KEY}",
                     "Content-Type":"application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def ensure_products_exist(self):
        """Create products + prices if they don't exist yet"""
        existing = self._req("GET","/products?active=true&limit=20").get("data",[])
        existing_names = {p["name"] for p in existing}
        created = []
        for prod in PRODUCTS:
            if prod["name"] in existing_names:
                continue
            # Create product
            p = self._req("POST","/products",{"name":prod["name"],"description":prod["desc"]})
            pid = p["id"]
            # Create price
            price_data = {"unit_amount":str(prod["price"]),"currency":"usd","product":pid}
            if prod["interval"]:
                price_data["recurring[interval]"] = prod["interval"]
            pr = self._req("POST","/prices", price_data)
            # Create payment link
            pl = self._req("POST","/payment_links",
                {"line_items[0][price]":pr["id"],"line_items[0][quantity]":"1"})
            created.append({"name":prod["name"],"price":prod["price"]/100,
                            "payment_link":pl.get("url",""),"price_id":pr["id"]})
            self.logger.info(f"Created: {prod['name']} → {pl.get('url','')[:50]}")
        return created

    def get_mrr(self):
        subs = self._req("GET","/subscriptions?status=active&limit=100").get("data",[])
        mrr  = sum(s["items"]["data"][0]["price"]["unit_amount"]*s["items"]["data"][0]["quantity"]/100
                   for s in subs if s.get("items",{}).get("data"))
        return {"mrr":mrr,"count":len(subs)}

    def get_recent_revenue(self, days=7):
        since = int(time.time())-(days*86400)
        charges = self._req("GET",f"/charges?created[gte]={since}&limit=100").get("data",[])
        total = sum(c["amount"]/100 for c in charges if c.get("paid") and not c.get("refunded"))
        return {"total":total,"count":len(charges),"days":days}

    def get_payment_links(self):
        return self._req("GET","/payment_links?limit=20").get("data",[])

    def execute(self):
        if not KEY:
            self.logger.warning("No STRIPE_SECRET_KEY")
            return {"error":"no_key"}

        # Ensure products exist
        created = self.ensure_products_exist()

        mrr      = self.get_mrr()
        revenue  = self.get_recent_revenue(7)
        links    = self.get_payment_links()

        link_rows = "".join([f"<tr><td>{l.get('metadata',{}).get('name',l['id'][:12])}</td><td><a href='{l['url']}'>{l['url'][:40]}</a></td></tr>"
                              for l in links[:10]])
        new_rows  = "".join([f"<tr><td>{p['name']}</td><td>${p['price']:,.2f}</td><td><a href='{p['payment_link']}'>Link</a></td></tr>"
                              for p in created]) if created else "<tr><td colspan=3>All products already exist</td></tr>"

        AlertSystem.send(
            subject=f"💳 Stripe Revenue: MRR ${mrr['mrr']:,.2f} | 7-day ${revenue['total']:,.2f}",
            body_html=f"""<h3>Stripe Revenue Dashboard</h3>
<p><b>MRR:</b> ${mrr['mrr']:,.2f} ({mrr['count']} active subs)</p>
<p><b>Last 7 days:</b> ${revenue['total']:,.2f} ({revenue['count']} charges)</p>
<h4>{'New Products Created:' if created else 'Existing Payment Links:'}</h4>
<table border='1'><tr><th>Product</th><th>Price</th><th>Link</th></tr>
{new_rows if created else link_rows}</table>""",
            severity="INFO")

        self.log_summary(mrr=mrr["mrr"], weekly_revenue=revenue["total"], new_products=len(created))
        return {"mrr":mrr["mrr"],"weekly":revenue["total"],"links":len(links),"new_products":len(created)}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--setup", action="store_true", help="Create all products + payment links")
    p.add_argument("--links", action="store_true", help="List payment links")
    p.add_argument("--mrr",   action="store_true", help="Show MRR")
    args = p.parse_args()
    bot = StripeRevenueBot()
    if args.setup:
        created = bot.ensure_products_exist()
        for p in created: print(f"✅ {p['name']} → {p['payment_link']}")
    elif args.links:
        links = bot.get_payment_links()
        for l in links: print(f"{l['id']}: {l['url']}")
    elif args.mrr:
        mrr = bot.get_mrr()
        print(f"MRR: ${mrr['mrr']:,.2f} ({mrr['count']} subs)")
    else:
        bot.run()
