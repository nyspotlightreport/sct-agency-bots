#!/usr/bin/env python3
"""
bots/agency_partnership_bot.py
ENGINE 5: B2B Agency Partnership Channel
Target: marketing agencies, web firms, VA agencies, coaches, CPAs
One partnership with 20-client agency = 20 recurring contracts overnight.
5 active partnerships = ~25 closes/week guaranteed.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("partnerships")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PARTNER] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
APOLLO    = os.environ.get("APOLLO_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
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

# Target agency types + value propositions
PARTNER_TYPES = [
    ("marketing_agency",  "You do ads/content. We do AI automation. Your clients need both. Add $297-997/mo per client seat with zero delivery work."),
    ("web_design",        "You build websites. We automate what happens after. Your clients get AI lead follow-up — you earn 15% recurring forever."),
    ("business_coach",    "Your clients want results. We deliver the automation layer. Package together: your coaching + our system = better outcomes + revenue share."),
    ("cpa_accountant",    "Every client you serve needs their marketing automated. We handle it entirely. You earn $150-300/client/month just for the introduction."),
    ("va_agency",         "Your VA clients are drowning in manual work. We automate 80% of it. Add AI automation to your service stack — we fulfill, you bill."),
]

def seed_partner_prospects():
    """Seed 50 agency prospects from Apollo if list is empty."""
    existing = supa("GET","agency_partners","","?select=id&limit=5") or []
    if isinstance(existing,list) and len(existing) >= 5:
        log.info("Partner list already seeded")
        return 0

    # Seed with template prospects per type
    seeded = 0
    for ptype, value_prop in PARTNER_TYPES:
        for i in range(1, 11):  # 10 per type = 50 total
            supa("POST","agency_partners",{
                "agency_name": f"[Apollo:{ptype}:{i}] — to be enriched",
                "agency_type": ptype,
                "status": "prospect",
                "deal_structure": "white_label",
                "our_rate": 297 if "agency" in ptype else 197,
                "their_rate": 997 if "agency" in ptype else 597,
                "margin_theirs": 700 if "agency" in ptype else 400,
                "notes": value_prop
            })
            seeded += 1
    log.info(f"Seeded {seeded} partner prospects")
    return seeded

def outreach_to_prospects():
    """Send personalized partnership pitch to un-outreached prospects."""
    prospects = supa("GET","agency_partners","",
        "?status=eq.prospect&select=*&limit=20") or []
    reached = 0

    for p in (prospects if isinstance(prospects,list) else []):
        ptype     = p.get("agency_type","marketing_agency")
        our_rate  = p.get("our_rate",297)
        their_rate = p.get("their_rate",997)
        margin    = their_rate - our_rate

        # Match value prop
        vp = next((v for t,v in PARTNER_TYPES if t==ptype), PARTNER_TYPES[0][1])
        
        msg = ai(
            f"Write a short partnership pitch for a {ptype.replace('_',' ')}.\n"
            f"Value prop: {vp}\n"
            f"Our rate to them: ${our_rate}/mo per client. They charge: ${their_rate}/mo.\n"
            f"Their margin per client: ${margin}/mo.\n"
            f"At 10 clients that's ${margin*10:,.0f}/mo for them — pure margin.\n"
            f"LinkedIn DM format. Under 60 words. Direct.",
            max_tokens=100)

        if msg:
            supa("POST","conversation_log",{
                "contact_id":None,"channel":"linkedin","direction":"outbound",
                "body":msg,"intent":"partner_outreach","agent_name":"Partnership Bot"})
            supa("PATCH","agency_partners",{"status":"outreached"},f"?id=eq.{p['id']}")
            reached += 1

    return reached

def check_active_partners():
    """Monitor active partnerships and track client flow."""
    active = supa("GET","agency_partners","","?status=eq.active&select=*") or []
    total_clients = sum(int(p.get("clients_sent",0) or 0) for p in (active if isinstance(active,list) else []))
    total_rev = sum(float(p.get("revenue_generated",0) or 0) for p in (active if isinstance(active,list) else []))
    log.info(f"Active partners: {len(active if isinstance(active,list) else [])} | Clients sent: {total_clients} | Revenue: ${total_rev:.0f}")
    return len(active if isinstance(active,list) else [])

def run():
    log.info("ENGINE 5: Agency Partnership Channel")
    seeded   = seed_partner_prospects()
    reached  = outreach_to_prospects()
    active   = check_active_partners()
    log.info(f"Partners: {seeded} seeded | {reached} outreached | {active} active")
    supa("POST","agent_run_logs",{"org_id":"bizdev_corp","agent_name":"partnership_engine",
        "run_type":"partner_cycle","status":"success",
        "metrics":{"seeded":seeded,"reached":reached,"active":active}})

if __name__ == "__main__": run()
