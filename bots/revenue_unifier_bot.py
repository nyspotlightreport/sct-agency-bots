"""
Revenue Unifier Bot
Pulls daily revenue from ALL streams: Stripe, Gumroad, Shopify, HubSpot pipeline.
Writes to revenue_daily table for unified P&L. Pushes daily summary to Pushover.
Closes the attribution gap — one source of truth for all money.
"""
import os, json, logging, datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REV] %(message)s")
log = logging.getLogger("revenue")

SUPABASE_URL  = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
STRIPE_KEY    = os.environ.get("STRIPE_SECRET_KEY","")
GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN","")
HUBSPOT_KEY   = os.environ.get("HUBSPOT_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.error

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}",
               "Content-Type":"application/json","Prefer":"return=representation"}
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code}")
        return None

def push(title, msg, priority=0):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req,timeout=10)
    except: pass

def upsert_revenue(date, source, amount, orders, refunds=0):
    existing = supa("GET","revenue_daily",f"?date=eq.{date}&source=eq.{source}&select=id&limit=1") or []
    data = {"date":date,"source":source,"amount":amount,"orders":orders,"refunds":refunds}
    if existing:
        supa("PATCH","revenue_daily",data,query=f"?date=eq.{date}&source=eq.{source}")
    else:
        supa("POST","revenue_daily",data)
    log.info(f"Revenue {source} {date}: ${amount:.2f} ({orders} orders)")

def pull_stripe():
    if not STRIPE_KEY: return 0,0,0
    today = datetime.date.today()
    start = int(datetime.datetime(today.year,today.month,today.day,0,0,0).timestamp())
    end   = int(datetime.datetime(today.year,today.month,today.day,23,59,59).timestamp())
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/charges?created[gte]={start}&created[lte]={end}&limit=100",
            headers={"Authorization":f"Bearer {STRIPE_KEY}"})
        with urllib.request.urlopen(req,timeout=15) as r:
            data = json.loads(r.read())
        charges = data.get("data",[])
        revenue = sum(c["amount"] for c in charges if c["paid"] and not c.get("refunded")) / 100
        refunds = sum(c["amount_refunded"] for c in charges) / 100
        orders  = len([c for c in charges if c["paid"]])
        return revenue, orders, refunds
    except Exception as e:
        log.warning(f"Stripe pull failed: {e}")
        return 0, 0, 0

def pull_gumroad():
    if not GUMROAD_TOKEN: return 0,0
    try:
        today = datetime.date.today().isoformat()
        req = urllib.request.Request(
            f"https://api.gumroad.com/v2/sales?access_token={GUMROAD_TOKEN}&after={today}&before={today}")
        with urllib.request.urlopen(req,timeout=15) as r:
            data = json.loads(r.read())
        sales = data.get("sales",[])
        revenue = sum(float(s.get("price",0))/100 for s in sales)
        return revenue, len(sales)
    except Exception as e:
        log.warning(f"Gumroad pull failed: {e}")
        return 0, 0

def pull_hubspot_pipeline():
    """Pull deals closed today from HubSpot."""
    if not HUBSPOT_KEY: return 0,0
    try:
        today = datetime.date.today().isoformat()
        req = urllib.request.Request(
            "https://api.hubapi.com/crm/v3/objects/deals?properties=dealname,amount,closedate,dealstage&limit=100",
            headers={"Authorization":f"Bearer {HUBSPOT_KEY}"})
        with urllib.request.urlopen(req,timeout=15) as r:
            data = json.loads(r.read())
        deals = data.get("results",[])
        closed_today = [d for d in deals
                        if d.get("properties",{}).get("dealstage","") == "closedwon"
                        and (d.get("properties",{}).get("closedate","") or "").startswith(today)]
        revenue = sum(float(d.get("properties",{}).get("amount",0) or 0) for d in closed_today)
        return revenue, len(closed_today)
    except Exception as e:
        log.warning(f"HubSpot pull failed: {e}")
        return 0, 0

def run():
    log.info("=== Revenue Unifier ===")
    today = datetime.date.today().isoformat()

    stripe_rev, stripe_orders, stripe_refunds = pull_stripe()
    upsert_revenue(today, "stripe", stripe_rev, stripe_orders, stripe_refunds)

    gumroad_rev, gumroad_orders = pull_gumroad()
    upsert_revenue(today, "gumroad", gumroad_rev, gumroad_orders)

    hs_rev, hs_orders = pull_hubspot_pipeline()
    upsert_revenue(today, "hubspot", hs_rev, hs_orders)

    total = stripe_rev + gumroad_rev + hs_rev
    total_orders = stripe_orders + gumroad_orders + hs_orders

    # Get yesterday for comparison
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    yday_rows = supa("GET","revenue_daily",f"?date=eq.{yesterday}&select=amount") or []
    yday_total = sum(float(r.get("amount",0)) for r in yday_rows)
    delta = total - yday_total

    # Monthly total
    month_start = datetime.date.today().replace(day=1).isoformat()
    month_rows = supa("GET","revenue_daily",f"?date=gte.{month_start}&select=amount") or []
    month_total = sum(float(r.get("amount",0)) for r in month_rows) + total

    summary = (
        f"💰 NYSR Revenue {today}\n"
        f"Today: ${total:.2f} ({'+' if delta>=0 else ''}{delta:.2f} vs yday)\n"
        f"Orders: {total_orders}\n"
        f"Stripe: ${stripe_rev:.2f} | Gumroad: ${gumroad_rev:.2f} | Pipeline: ${hs_rev:.2f}\n"
        f"Month-to-date: ${month_total:.2f}"
    )
    log.info(summary)
    priority = 1 if total > 100 else 0
    push("💰 Daily Revenue", summary, priority=priority)
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
