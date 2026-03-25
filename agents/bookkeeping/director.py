#!/usr/bin/env python3
"""
agents/bookkeeping/director.py — Morgan Ellis, AI Bookkeeping Director
Orchestrates: transaction categorization, P&L generation, expense tracking,
anomaly detection, monthly close, cash flow projections.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("bookkeeping_director")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [BOOKKEEPING] %(message)s")
import urllib.request as urlreq

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
STRIPE_SK=os.environ.get("STRIPE_SECRET_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
SITE="https://nyspotlightreport.com"

def push(t,m,p=0):
    if not PUSH_API: return
    try:
        data=json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":t,"message":m[:1000],"priority":p}).encode()
        req=urlreq.Request("https://api.pushover.net/1/messages.json",data=data,headers={"Content-Type":"application/json"})
        urlreq.urlopen(req,timeout=10)
    except: pass

def fetch_stripe_transactions():
    if not STRIPE_SK:
        log.warning("No STRIPE_SECRET_KEY")
        return []
    try:
        import base64
        auth=base64.b64encode((STRIPE_SK+":").encode()).decode()
        req=urlreq.Request("https://api.stripe.com/v1/charges?limit=50",
            headers={"Authorization":"Basic "+auth})
        resp=urlreq.urlopen(req,timeout=15)
        return json.loads(resp.read()).get("data",[])
    except Exception as e:
        log.error("Stripe fetch failed: %s",e)
        return []

def categorize(charge):
    a=charge.get("amount",0)/100
    d=charge.get("description","") or charge.get("statement_descriptor","")
    return {"amount":a,"desc":d,"cat":"revenue" if charge.get("paid") else "refund",
            "date":datetime.fromtimestamp(charge.get("created",0)).isoformat()}

def generate_pl(txns):
    rev=sum(t["amount"] for t in txns if t["cat"]=="revenue")
    ref=sum(t["amount"] for t in txns if t["cat"]=="refund")
    return {"revenue":rev,"refunds":ref,"net":rev-ref,"count":len(txns),
            "period":datetime.utcnow().strftime("%Y-%m")}


def detect_anomalies(txns):
    if len(txns)<2: return []
    amounts=[t["amount"] for t in txns]
    avg=sum(amounts)/len(amounts)
    flags=[]
    for t in txns:
        if t["amount"]>avg*3:
            flags.append(f"ANOMALY: ${t['amount']:.2f} is 3x avg (${avg:.2f})")
    return flags

def run():
    log.info("=== Morgan Ellis Bookkeeping — Daily Run ===")
    charges=fetch_stripe_transactions()
    log.info("Fetched %d Stripe transactions",len(charges))
    txns=[categorize(c) for c in charges]
    pl=generate_pl(txns)
    log.info("P&L: Rev=$%.2f | Ref=$%.2f | Net=$%.2f",pl["revenue"],pl["refunds"],pl["net"])
    anomalies=detect_anomalies(txns)
    if anomalies:
        push("BOOKKEEPING ALERT","\n".join(anomalies),1)
        log.warning("Anomalies detected: %d",len(anomalies))
    if pl["net"]!=0:
        push("Bookkeeping Daily","Net: $%.2f from %d txns"%(pl["net"],pl["count"]))
    log.info("=== Bookkeeping Complete ===")
    return pl

if __name__=="__main__":
    run()
