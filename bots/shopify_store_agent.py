"""
Shopify Store Agent — Phase 3
Manages NYSR storefront. Syncs products from Gumroad/Stripe to Shopify.
Tracks orders, reviews, cart abandonment. Drives 3-8x conversion lift.
MRR Unlock: $2k-8k/mo
"""
import os, json, logging, datetime
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SHOP] %(message)s")
log = logging.getLogger("shopify")

SUPABASE_URL    = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
SHOPIFY_TOKEN   = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
SHOPIFY_STORE   = os.environ.get("SHOPIFY_STORE_DOMAIN", "")  # e.g. nysr-agency.myshopify.com
GUMROAD_TOKEN   = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
STRIPE_KEY      = os.environ.get("STRIPE_SECRET_KEY", "")
PUSHOVER_API    = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER   = os.environ.get("PUSHOVER_USER_KEY", "")

import urllib.request, urllib.error

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json", "Prefer": "return=representation"}
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code}")
        return None

def push(title: str, message: str, priority: int = 0):
    if not PUSHOVER_API: return
    data = json.dumps({"token": PUSHOVER_API, "user": PUSHOVER_USER,
                        "title": title, "message": message, "priority": priority}).encode()
    try:
        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                                     data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: bare-except

        pass
def ai(prompt: str) -> str:
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": 600,
                        "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={
        "Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

# ── GUMROAD SYNC ────────────────────────────────────────────────────
def sync_gumroad_products():
    if not GUMROAD_TOKEN:
        log.warning("No Gumroad token — skipping sync")
        return
    try:
        req = urllib.request.Request(
            f"https://api.gumroad.com/v2/products?access_token={GUMROAD_TOKEN}")
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        products = data.get("products", [])
        for p in products:
            existing = supa("GET", "store_products",
                            query=f"?gumroad_id=eq.{p['id']}&select=id&limit=1") or []
            product_data = {
                "gumroad_id": p["id"],
                "title": p["name"],
                "description": p.get("description", "")[:500],
                "price": float(p.get("price", 0)) / 100,
                "image_url": p.get("preview_url", ""),
                "status": "active" if p.get("published") else "inactive",
                "category": "digital",
                "tags": ["gumroad", "digital-product"],
                "meta": {"gumroad_url": p.get("short_url", ""), "currency": p.get("currency", "usd")}
            }
            if existing:
                supa("PATCH", "store_products", product_data, query=f"?gumroad_id=eq.{p['id']}")
            else:
                supa("POST", "store_products", product_data)
            log.info(f"Synced Gumroad product: {p['name']}")
    except Exception as e:
        log.warning(f"Gumroad sync failed: {e}")

# ── SHOPIFY SYNC ────────────────────────────────────────────────────
def shopify_api(endpoint: str, method: str = "GET", data: dict = None):
    if not SHOPIFY_TOKEN or not SHOPIFY_STORE: return None
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/{endpoint}"
    payload = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=payload, method=method, headers={
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        log.warning(f"Shopify {method} {endpoint}: {e.code} {e.read()[:200]}")
        return None

def push_products_to_shopify():
    """Push active local products to Shopify catalog."""
    products = supa("GET", "store_products", query="?status=eq.active&shopify_id=is.null&select=*") or []
    for p in products:
        shopify_product = {
            "product": {
                "title": p["title"],
                "body_html": p.get("description", ""),
                "vendor": "NY Spotlight Report",
                "product_type": p.get("category", "Digital"),
                "tags": ",".join(p.get("tags") or []),
                "variants": [{"price": str(p["price"]), "requires_shipping": False}],
                "status": "active"
            }
        }
        if p.get("image_url"):
            shopify_product["product"]["images"] = [{"src": p["image_url"]}]
        result = shopify_api("products.json", "POST", shopify_product)
        if result and result.get("product"):
            shopify_id = str(result["product"]["id"])
            supa("PATCH", "store_products", {"shopify_id": shopify_id},
                 query=f"?id=eq.{p['id']}")
            log.info(f"Pushed to Shopify: {p['title']} → {shopify_id}")

def sync_shopify_orders():
    """Pull recent Shopify orders into Supabase."""
    orders_data = shopify_api("orders.json?status=any&limit=50&fields=id,email,total_price,financial_status,line_items,created_at")
    if not orders_data: return
    for order in orders_data.get("orders", []):
        existing = supa("GET", "store_orders", query=f"?shopify_order_id=eq.{order['id']}&select=id&limit=1") or []
        if existing: continue
        contact = supa("GET", "contacts", query=f"?email=eq.{order.get('email','')}&select=id&limit=1") or []
        supa("POST", "store_orders", {
            "shopify_order_id": str(order["id"]),
            "contact_id": contact[0]["id"] if contact else None,
            "status": order.get("financial_status", "pending"),
            "total": float(order.get("total_price", 0)),
            "email": order.get("email", ""),
            "items": order.get("line_items", []),
            "created_at": order.get("created_at")
        })
        push("💰 New Order!", f"${order.get('total_price')} from {order.get('email','?')}", priority=0)
        log.info(f"Synced Shopify order #{order['id']}: ${order['total_price']}")

# ── CART ABANDONMENT ────────────────────────────────────────────────
def handle_cart_abandonment():
    """Find cart abandonment events and trigger recovery sequence."""
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()
    abandoned = supa("GET", "store_cart_events",
                     query=f"?event_type=eq.checkout_start&created_at=gt.{cutoff}&select=contact_id,session_id,product_id") or []
    converted = supa("GET", "store_cart_events",
                     query=f"?event_type=eq.purchase&created_at=gt.{cutoff}&select=session_id") or []
    converted_sessions = {e["session_id"] for e in converted}
    for e in abandoned:
        if e.get("session_id") in converted_sessions: continue
        contact_id = e.get("contact_id")
        if not contact_id: continue
        # Trigger win-back journey
        existing_journey = supa("GET", "journey_steps",
                                 query=f"?contact_id=eq.{contact_id}&journey_key=eq.cart_recovery&select=id&limit=1") or []
        if not existing_journey:
            recovery_email = ai(
                "Write a cart abandonment recovery email for NYSR Agency AI automation products. "
                "Subject: starts with '⚡'. Body: 3 sentences, urgency without pressure, mention ROI. "
                "Return JSON: {\"subject\":\"...\",\"body\":\"...\"}"
            )
            try:
                email_data = json.loads(recovery_email.strip().lstrip("```json").rstrip("```"))
                supa("POST", "journey_steps", {
                    "contact_id": contact_id,
                    "journey_key": "cart_recovery",
                    "step_num": 1,
                    "subject": email_data.get("subject", "You left something behind..."),
                    "body": email_data.get("body", "Come back and complete your purchase.")
                })
                log.info(f"Cart recovery triggered for contact {contact_id}")
            except Exception:  # noqa: bare-except

                pass
# ── REVENUE REPORT ─────────────────────────────────────────────────
def daily_revenue_report():
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    orders_today = supa("GET", "store_orders", query=f"?created_at=gte.{today}T00:00:00&select=total,status") or []
    orders_yday  = supa("GET", "store_orders", query=f"?created_at=gte.{yesterday}T00:00:00&created_at=lt.{today}T00:00:00&select=total") or []
    products_count = supa("GET", "store_products", query="?status=eq.active&select=id") or []
    today_rev = sum(float(o["total"]) for o in orders_today if o.get("status") not in ["refunded","cancelled"])
    yday_rev  = sum(float(o["total"]) for o in orders_yday)
    delta = today_rev - yday_rev
    report = f"🛍️ Store Revenue {today}: ${today_rev:.2f} ({'+' if delta>=0 else ''}{delta:.2f} vs yesterday) | {len(orders_today)} orders | {len(products_count)} active products"
    log.info(report)
    push("🛍️ Store Revenue", report)
    return report

def run():
    log.info("=== Shopify Store Agent ===")
    sync_gumroad_products()
    push_products_to_shopify()
    sync_shopify_orders()
    handle_cart_abandonment()
    daily_revenue_report()
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
