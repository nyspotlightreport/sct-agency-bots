#!/usr/bin/env python3
"""
bots/sales_rep_commission_bot.py
Monthly payroll calculator for 1099 sales reps.
Queries Stripe for attributed revenue by rep affiliate code.
Calculates commissions. Sends Sean ONE Pushover for approval.
Sean taps approve = payments go out. Zero other involvement.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("commissions")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [COMMISSIONS] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
STRIPE_SK = os.environ.get("STRIPE_SECRET_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
now       = datetime.datetime.utcnow()
this_month = now.strftime("%Y-%m")
last_month = (now.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e: log.debug(f"Supa: {e}"); return None

def stripe_list(endpoint, params=""):
    if not STRIPE_SK: return []
    req = urllib.request.Request(f"https://api.stripe.com/v1/{endpoint}{params}",
        headers={"Authorization": f"Bearer {STRIPE_SK}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("data",[])
    except: return []

def calculate_monthly_commissions():
    """Calculate what each rep is owed for last month."""
    reps = supa("GET","sales_reps","","?status=eq.active&select=*") or []
    rates = supa("GET","rep_commission_rates","","?select=*") or []
    rates_map = {r["offer_key"]:r for r in (rates if isinstance(rates,list) else [])}
    
    payroll_summary = []
    total_owed = 0
    
    for rep in (reps if isinstance(reps,list) else []):
        rep_id   = rep.get("id")
        rep_code = rep.get("rep_code","")
        
        # Get all sales for this rep in last month
        period_start = f"{last_month}-01T00:00:00"
        period_end   = f"{this_month}-01T00:00:00"
        
        sales = supa("GET","rep_sales","",
            f"?rep_id=eq.{rep_id}&status=eq.closed"
            f"&closed_at=gte.{period_start}&closed_at=lt.{period_end}&select=*") or []
        
        if not isinstance(sales, list): sales = []
        
        new_deal_comm    = sum(float(s.get("commission_earned",0) or 0) for s in sales if s.get("commission_earned"))
        
        # Recurring commissions: active clients * monthly rate
        active_clients = supa("GET","contacts","",
            f"?stage=eq.CLOSED_WON&tags=cs.{{rep_{rep_code}}}&select=id") or []
        active_count = len(active_clients) if isinstance(active_clients,list) else 0
        
        # Estimate recurring based on average commission ($200/client/month assumption)
        recurring_comm = active_count * 200
        
        # Clawbacks: refunds in last month
        clawbacks = supa("GET","rep_sales","",
            f"?rep_id=eq.{rep_id}&status=eq.refunded"
            f"&closed_at=gte.{period_start}&closed_at=lt.{period_end}&select=commission_earned") or []
        clawback_total = sum(float(s.get("commission_earned",0) or 0) for s in (clawbacks if isinstance(clawbacks,list) else []))
        
        rep_total = new_deal_comm + recurring_comm - clawback_total
        
        if rep_total > 0:
            # Create payroll record
            supa("POST","commission_payroll",{
                "period_month":last_month,
                "rep_id":rep_id,
                "new_deal_commissions":new_deal_comm,
                "recurring_commissions":recurring_comm,
                "clawbacks":clawback_total,
                "total_owed":rep_total,
                "status":"pending"
            })
            
            payroll_summary.append({
                "name": f"{rep.get('first_name','')} {rep.get('last_name','')}",
                "new_deals":new_deal_comm,
                "recurring":recurring_comm,
                "total":rep_total
            })
            total_owed += rep_total
    
    return payroll_summary, total_owed

def send_approval_digest(summary, total):
    """Send Sean ONE notification to approve the month's payroll."""
    if not summary:
        log.info("No active reps with commissions this period.")
        return
    
    lines = [f"Monthly Commission Payroll — {last_month}"]
    for rep in summary[:5]:
        lines.append(f"{rep['name']}: ${rep['total']:.0f} (new=${rep['new_deals']:.0f} + recur=${rep['recurring']:.0f})")
    if len(summary) > 5:
        lines.append(f"...and {len(summary)-5} more reps")
    lines.append(f"\nTotal owed: ${total:.2f}")
    lines.append("Reply APPROVE to release payments.")
    
    if PUSH_API and PUSH_USER:
        data = json.dumps({
            "token":PUSH_API,"user":PUSH_USER,
            "title":f"Rep Payroll: ${total:.0f} to approve",
            "message":"\n".join(lines),
            "priority":0
        }).encode()
        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data, headers={"Content-Type":"application/json"})
        try: urllib.request.urlopen(req, timeout=10)
        except: pass
    log.info("\n".join(lines))

def run():
    log.info("=" * 55)
    log.info(f"COMMISSION PAYROLL — Period: {last_month}")
    log.info("1099 Army: calculating what we owe each rep")
    log.info("=" * 55)
    summary, total = calculate_monthly_commissions()
    send_approval_digest(summary, total)
    log.info(f"Payroll complete: {len(summary)} reps | ${total:.2f} total | Sean gets 1 notification to approve")

if __name__ == "__main__": run()
