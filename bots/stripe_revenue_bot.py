#!/usr/bin/env python3
"""
STRIPE REVENUE BOT v1.0 — S.C. Thomas Internal Agency
Manages Stripe subscriptions, tracks revenue, monitors failed payments,
auto-sends dunning emails, reports MRR/ARR daily.
Also creates Stripe payment links on demand.
"""
import os, sys, json, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

class StripeRevenueBot(BaseBot):
    VERSION = "1.0.0"
    BASE = "https://api.stripe.com/v1"
    KEY  = os.getenv("STRIPE_SECRET_KEY", "")

    def __init__(self):
        super().__init__("stripe-revenue")

    def _req(self, method, path, data=None):
        url = f"{self.BASE}{path}"
        body = urllib.parse.urlencode(data).encode() if data else None
        req  = urllib.request.Request(url, data=body, method=method,
            headers={"Authorization": f"Bearer {self.KEY}",
                     "Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    @with_retry(max_retries=2)
    def get_mrr(self) -> dict:
        """Get current MRR from active subscriptions"""
        subs = self._req("GET", "/subscriptions?status=active&limit=100")
        mrr  = sum(s["plan"]["amount"] * s["quantity"] / 100
                   for s in subs.get("data", [])
                   if s.get("plan") and s["plan"].get("interval") == "month")
        return {"mrr": mrr, "count": len(subs.get("data", [])), "currency": "usd"}

    @with_retry(max_retries=2)
    def get_failed_payments(self) -> list:
        """Get recent failed payment intents"""
        result = self._req("GET", "/payment_intents?status=requires_payment_method&limit=20")
        return result.get("data", [])

    @with_retry(max_retries=2)
    def create_payment_link(self, price_id: str, name: str = "") -> str:
        """Create a Stripe payment link"""
        data = {"line_items[0][price]": price_id, "line_items[0][quantity]": "1"}
        result = self._req("POST", "/payment_links", data)
        return result.get("url", "")

    @with_retry(max_retries=2)
    def get_recent_revenue(self, days: int = 7) -> dict:
        """Get revenue from last N days"""
        import time
        since = int(time.time()) - (days * 86400)
        charges = self._req("GET", f"/charges?created[gte]={since}&limit=100")
        total = sum(c["amount"] / 100 for c in charges.get("data", [])
                    if c.get("paid") and not c.get("refunded"))
        return {"total": total, "days": days, "count": len(charges.get("data", []))}

    def execute(self) -> dict:
        if not self.KEY:
            self.logger.warning("No STRIPE_SECRET_KEY configured")
            return {"items_processed": 0}
        try:
            mrr    = self.get_mrr()
            recent = self.get_recent_revenue(7)
            failed = self.get_failed_payments()
            AlertSystem.send(
                subject  = f"💰 Stripe Revenue — MRR: ${mrr['mrr']:,.2f} | 7d: ${recent['total']:,.2f}",
                body_html= f"""
<h3>Stripe Revenue Report</h3>
<table>
<tr><td>MRR</td><td><strong>${mrr['mrr']:,.2f}</strong></td></tr>
<tr><td>Active subscriptions</td><td>{mrr['count']}</td></tr>
<tr><td>Revenue last 7 days</td><td>${recent['total']:,.2f}</td></tr>
<tr><td>Failed payments</td><td style="color:{'red' if failed else 'green'}">{len(failed)}</td></tr>
</table>""",
                severity = "SUCCESS"
            )
            return {"mrr": mrr["mrr"], "failed": len(failed)}
        except Exception as e:
            self.logger.error(f"Stripe error: {e}")
            return {"error": str(e)}

def create_product_link(name: str, price_cents: int, recurring: bool = True) -> str:
    """Quick function to create a Stripe product + price + payment link"""
    bot = StripeRevenueBot()
    # Create product
    prod = bot._req("POST", "/products", {"name": name})
    # Create price
    price_data = {"product": prod["id"], "unit_amount": str(price_cents),
                  "currency": "usd"}
    if recurring:
        price_data.update({"recurring[interval]": "month"})
    price = bot._req("POST", "/prices", price_data)
    # Create payment link
    link = bot.create_payment_link(price["id"], name)
    print(f"✅ Payment link for '{name}': {link}")
    return link

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--report", action="store_true")
    p.add_argument("--create-link", type=str, help="Product name")
    p.add_argument("--price",  type=int, default=2900, help="Price in cents")
    p.add_argument("--once",   action="store_true", help="One-time payment")
    args = p.parse_args()
    if args.create_link:
        create_product_link(args.create_link, args.price, not args.once)
    else:
        StripeRevenueBot().run()
# SECRETS: STRIPE_SECRET_KEY (from dashboard.stripe.com → Developers → API keys)
