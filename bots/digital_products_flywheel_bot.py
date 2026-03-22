#!/usr/bin/env python3
"""
bots/digital_products_flywheel_bot.py
Automates the Gumroad/digital product flywheel.
Creates product listings, monitors sales, triggers upsells.
Every workflow, bot, and template NYSR built is itself a sellable product.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("products")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PRODUCTS] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
GUMROAD   = os.environ.get("GUMROAD_ACCESS_TOKEN","")
now       = datetime.datetime.utcnow()

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def ai(prompt, max_tokens=300):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def generate_product_descriptions():
    """Use AI to write compelling Gumroad product descriptions."""
    products = supa("GET","digital_products","",
        "?status=eq.ready&description=not.is.null&select=*&limit=5") or []
    updated = 0

    for p in (products if isinstance(products,list) else []):
        desc = p.get("description","")
        if len(desc) < 50: continue  # Already has description

        enhanced = ai(
            f"Write a compelling Gumroad product description for: {p.get('name')}\n"
            f"Current description: {desc}\n"
            f"Price: ${p.get('price')}\n"
            f"Target: Agency owners, consultants, small business owners wanting AI automation\n"
            f"Include: What they get, specific outcomes, why it's worth the price.\n"
            f"Format: Short punchy paragraphs. Under 200 words. No bullet points.",
            max_tokens=250)

        if enhanced:
            supa("PATCH","digital_products",{"description":enhanced},f"?id=eq.{p['id']}")
            updated += 1

    log.info(f"Product descriptions enhanced: {updated}")
    return updated

def track_product_performance():
    """Check Gumroad API for sales data."""
    if not GUMROAD:
        log.warning("No Gumroad token — skipping sales tracking")
        return 0

    req = urllib.request.Request(
        "https://api.gumroad.com/v2/products",
        headers={"Authorization":f"Bearer {GUMROAD}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            products = data.get("products",[])
            total_sales = sum(p.get("sales_count",0) for p in products)
            total_revenue = sum(p.get("revenue",0) for p in products) / 100  # cents to dollars

            # Update our DB
            for p in products:
                db_key = None
                name = p.get("name","").lower()
                if "starter" in name:     db_key = "agency_starter_pack"
                elif "hubspot" in name:   db_key = "hubspot_pipeline"
                elif "email" in name:     db_key = "email_sequence_pack"
                elif "blueprint" in name: db_key = "proflow_blueprint"

                if db_key:
                    supa("PATCH","digital_products",{
                        "sales_count":p.get("sales_count",0),
                        "revenue_total":p.get("revenue",0)/100
                    },f"?product_key=eq.{db_key}")

            log.info(f"Gumroad: {total_sales} total sales | ${total_revenue:.2f} revenue")
            return total_sales
    except Exception as e:
        log.warning(f"Gumroad API: {e}")
        return 0

def run():
    log.info("=== Digital Products Flywheel ===")
    generate_product_descriptions()
    track_product_performance()

if __name__ == "__main__": run()
