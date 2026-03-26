#!/usr/bin/env python3
"""
Commission Tracker Agent
Checks Stripe for rep-attributed sales, calculates commissions,
and logs everything to Supabase.

Env vars: STRIPE_SECRET_KEY, SUPABASE_URL, SUPABASE_KEY
"""

import os, json, logging
from datetime import datetime, timedelta, timezone

try:
    import stripe
except ImportError:
    print("Install stripe: pip install stripe"); raise

try:
    from supabase import create_client, Client
except ImportError:
    print("Install supabase: pip install supabase"); raise

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CommTracker] %(message)s")
logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DEFAULT_COMMISSION_RATE = 0.15
LOOKBACK_HOURS = 24


class CommissionTracker:
    """Pulls Stripe charges with rep metadata, calculates commissions, logs to Supabase."""

    def __init__(self):
        if not all([STRIPE_SECRET_KEY, SUPABASE_URL, SUPABASE_KEY]):
            raise EnvironmentError("STRIPE_SECRET_KEY, SUPABASE_URL, and SUPABASE_KEY required")
        stripe.api_key = STRIPE_SECRET_KEY
        self.sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    def fetch_recent_charges(self, hours=LOOKBACK_HOURS):
        """Fetch Stripe charges from the last N hours with rep attribution."""
        cutoff = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp())
        charges, has_more, starting_after = [], True, None
        while has_more:
            params = {"limit": 100, "created": {"gte": cutoff}}
            if starting_after:
                params["starting_after"] = starting_after
            batch = stripe.Charge.list(**params)
            for c in batch.data:
                m = c.get("metadata", {})
                if m.get("rep_id") or m.get("referral_code"):
                    charges.append(c)
            has_more = batch.has_more
            if batch.data:
                starting_after = batch.data[-1].id
        logger.info(f"Found {len(charges)} rep-attributed charges in last {hours}h")
        return charges

    def get_rep_by_referral_code(self, code):
        r = self.sb.table("sales_reps").select("*").eq("referral_code", code).eq("status", "active").execute()
        return r.data[0] if r.data else None

    def get_rep_by_id(self, rep_id):
        r = self.sb.table("sales_reps").select("*").eq("id", rep_id).execute()
        return r.data[0] if r.data else None

    def sale_already_recorded(self, stripe_charge_id):
        r = self.sb.table("rep_sales").select("id").eq("stripe_charge", stripe_charge_id).execute()
        return len(r.data) > 0

    def record_sale(self, rep_id, charge):
        """Insert a sale record into rep_sales."""
        payload = {
            "rep_id": rep_id,
            "customer_name": charge.get("billing_details", {}).get("name", "Unknown"),
            "customer_email": charge.get("billing_details", {}).get("email"),
            "product": charge.get("description", "Unknown"),
            "amount_cents": charge["amount"],
            "currency": charge["currency"],
            "stripe_charge": charge["id"],
            "stripe_invoice": charge.get("invoice"),
            "sale_date": datetime.fromtimestamp(charge["created"], tz=timezone.utc).isoformat(),
            "status": "completed" if charge["paid"] else "pending",
            "metadata": dict(charge.get("metadata", {})),
        }
        r = self.sb.table("rep_sales").insert(payload).execute()
        return r.data[0] if r.data else payload

    def record_commission(self, rep_id, sale_id, sale_amount, rate, currency="usd"):
        """Calculate and insert a commission record."""
        commission_cents = int(sale_amount * rate)
        payload = {
            "rep_id": rep_id,
            "sale_id": sale_id,
            "commission_rate": rate,
            "amount_cents": commission_cents,
            "currency": currency,
            "status": "pending",
            "pay_period": datetime.now(timezone.utc).strftime("%Y-%m"),
        }
        r = self.sb.table("commissions").insert(payload).execute()
        logger.info(f"Commission: {commission_cents / 100:.2f} for rep {rep_id} (rate={rate})")
        return r.data[0] if r.data else payload

    def run(self, hours=LOOKBACK_HOURS, dry_run=False):
        """Full pipeline: fetch charges, resolve reps, record sales + commissions."""
        charges = self.fetch_recent_charges(hours)
        stats = {"processed": 0, "skipped": 0, "errors": 0, "total_commission_cents": 0}

        for charge in charges:
            meta = charge.get("metadata", {})
            cid = charge["id"]

            if not dry_run and self.sale_already_recorded(cid):
                stats["skipped"] += 1
                continue

            rep = None
            if meta.get("rep_id"):
                rep = self.get_rep_by_id(meta["rep_id"])
            elif meta.get("referral_code"):
                rep = self.get_rep_by_referral_code(meta["referral_code"])

            if not rep:
                stats["errors"] += 1
                continue

            rate = float(rep.get("commission_rate", DEFAULT_COMMISSION_RATE))

            if dry_run:
                stats["processed"] += 1
                stats["total_commission_cents"] += int(charge["amount"] * rate)
                continue

            try:
                sr = self.record_sale(rep["id"], charge)
                cr = self.record_commission(rep["id"], sr.get("id"), charge["amount"], rate, charge["currency"])
                stats["processed"] += 1
                stats["total_commission_cents"] += cr.get("amount_cents", 0)
            except Exception as e:
                logger.error(f"Error processing charge {cid}: {e}")
                stats["errors"] += 1

        logger.info(f"Done: {json.dumps(stats)}")
        return stats

    def get_leaderboard(self, period=None, limit=10):
        """Get top reps by commission earned."""
        q = self.sb.table("commissions").select("rep_id, amount_cents")
        if period:
            q = q.eq("pay_period", period)
        r = q.execute()
        totals = {}
        for c in r.data:
            totals[c["rep_id"]] = totals.get(c["rep_id"], 0) + c["amount_cents"]
        board = []
        for rid, tc in sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]:
            rep = self.get_rep_by_id(rid)
            nm = f"{rep['first_name']} {rep['last_name']}" if rep else "Unknown"
            board.append({"rank": len(board)+1, "rep_id": rid, "name": nm, "total": f"${tc/100:.2f}"})
        return board


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Commission Tracker Agent")
    p.add_argument("--hours", type=int, default=LOOKBACK_HOURS)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--leaderboard", action="store_true")
    p.add_argument("--period", type=str)
    args = p.parse_args()
    t = CommissionTracker()
    if args.leaderboard:
        print(json.dumps(t.get_leaderboard(period=args.period), indent=2))
    else:
        print(json.dumps(t.run(hours=args.hours, dry_run=args.dry_run), indent=2))
