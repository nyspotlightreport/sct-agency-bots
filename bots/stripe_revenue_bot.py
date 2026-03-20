#!/usr/bin/env python3
"""
STRIPE REVENUE BOT v2.1 — S.C. Thomas Internal Agency
Auto-creates products, prices, payment links. Tracks MRR. Dunning emails.
"""
import os, sys, json, urllib.request, urllib.parse, time
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, AlertSystem, with_retry

KEY  = os.getenv("STRIPE_SECRET_KEY","")
BASE = "https://api.stripe.com/v1"

PRODUCTS = [
    {"name":"NY Spotlight Report — Newsletter",  "price":999,   "interval":"month", "desc":"Premium media newsletter"},
    {"name":"SCT Agency Content Package",        "price":2999,  "interval":"month", "desc":"Monthly content strategy"},
    {"name":"Media Consulting — 1hr Session",    "price":15000, "interval":None,    "desc":"1-hour strategy consultation"},
    {"name":"Agency Bot System License",         "price":4999,  "interval":"month", "desc":"Full bot system access"},
    {"name":"Press Release Distribution",        "price":29900, "interval":None,    "desc":"Multi-platform press distribution"},
]

class StripeRevenueBot(BaseBot):
    VERSION = "2.1.0"

    def __init__(self):
        super().__init__("stripe-revenue")  # FIXED: pass name arg

    def _req(self, method, path, data=None):
        url  = f"{BASE}{path}"
        body = urllib.parse.urlencode(data).encode() if data else None
        req  = urllib.request.Request(url, data=body, method=method,
            headers={"Authorization":f"Bearer {KEY}",
                     "Content-Type":"application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def ensure_products_exist(self):
        existing = self._req("GET","/products?active=true&limit=20").get("data",[])
        existing_names = {p["name"] for p in existing}
        created = []
        for prod in PRODUCTS:
            if prod["name"] in existing_names:
                self.logger.info(f"Already exists: {prod['name']}")
                continue
            p  = self._req("POST","/products",{"name":prod["name"],"description":prod["desc"]})
            pid = p["id"]
            pd = {"unit_amount":str(prod["price"]),"currency":"usd","product":pid}
            if prod["interval"]:
                pd["recurring[interval]"] = prod["interval"]
            pr = self._req("POST","/prices",pd)
            pl = self._req("POST","/payment_links",
                {"line_items[0][price]":pr["id"],"line_items[0][quantity]":"1"})
            link = pl.get("url","")
            created.append({"name":prod["name"],"price":prod["price"]/100,
                            "payment_link":link,"price_id":pr["id"]})
            print(f"✅ Created: {prod['name']} → ${prod['price']/100:.2f}/{'mo' if prod['interval'] else 'one-time'}")
            print(f"   Payment link: {link}")
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
        return {"total":total,"count":len(charges)}

    def get_payment_links(self):
        return self._req("GET","/payment_links?limit=20").get("data",[])

    def execute(self):
        if not KEY:
            self.logger.warning("No STRIPE_SECRET_KEY"); return {"error":"no_key"}

        print("=== STRIPE REVENUE BOT ===")
        created  = self.ensure_products_exist()
        mrr      = self.get_mrr()
        revenue  = self.get_recent_revenue(7)
        links    = self.get_payment_links()

        print(f"\nMRR: ${mrr['mrr']:,.2f} ({mrr['count']} active subs)")
        print(f"Last 7 days revenue: ${revenue['total']:,.2f} ({revenue['count']} charges)")
        print(f"Total payment links: {len(links)}")
        if links:
            print("\nActive payment links:")
            for l in links[:10]:
                print(f"  {l['url']}")

        link_rows = "".join([f"<tr><td>{l['id'][:12]}</td><td><a href='{l['url']}'>{l['url'][:50]}</a></td></tr>"
                              for l in links[:10]])
        new_rows  = "".join([f"<tr><td>{p['name']}</td><td>${p['price']:,.2f}</td><td><a href='{p['payment_link']}'>{p['payment_link'][:50]}</a></td></tr>"
                              for p in created]) if created else ""

        AlertSystem.send(
            subject=f"💳 Stripe: MRR ${mrr['mrr']:,.2f} | 7-day ${revenue['total']:,.2f} | {len(created)} new products",
            body_html=f"""<h3>Stripe Revenue Dashboard — {datetime.now().strftime('%b %d, %Y')}</h3>
<p><b>MRR:</b> ${mrr['mrr']:,.2f} | <b>Active Subs:</b> {mrr['count']} | <b>Last 7 Days:</b> ${revenue['total']:,.2f}</p>
{f'<h4>New Products Created:</h4><table border=1><tr><th>Product</th><th>Price</th><th>Payment Link</th></tr>{new_rows}</table>' if created else ''}
<h4>All Payment Links ({len(links)}):</h4>
<table border='1'><tr><th>ID</th><th>URL</th></tr>{link_rows}</table>""",
            severity="INFO")

        self.log_summary(mrr=mrr["mrr"],weekly=revenue["total"],links=len(links),new=len(created))
        return {"mrr":mrr["mrr"],"weekly":revenue["total"],"links":len(links),"new_products":len(created)}

if __name__ == "__main__":
    StripeRevenueBot().run()
