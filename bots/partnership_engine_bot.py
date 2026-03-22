#!/usr/bin/env python3
"""
bots/partnership_engine_bot.py
ENGINE 5: Agency Partnership B2B Channel.
Target: marketing agencies, coaches, VA agencies with 10-50 clients.
One partnership with 20 clients = 20 recurring contracts overnight.
Apollo finds them. AI personalizes the pitch. 1099 rep closes.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("partnerships")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PARTNERSHIPS] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
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

# Target 5 active agency partners. This is the goal.
TARGET_PARTNER_TYPES = [
    ("marketing_agency", "marketing agencies", "I run campaigns for businesses — my clients always need content automation I can not deliver myself"),
    ("business_coach", "business coaches", "my clients are trying to grow but spending hours on manual content work"),
    ("va_agency", "VA/OBM agencies", "my team sees clients drowning in manual tasks every week"),
    ("web_design_firm", "web design firms", "every website I build needs content — my clients struggle to keep it current"),
    ("staffing_hr", "staffing and HR firms", "companies that are hiring are scaling and need automation")
]

def outreach_potential_partners():
    """Find and pitch potential agency partners."""
    prospects = supa("GET","partnership_pipeline","","?status=eq.prospect&select=*&limit=10") or []
    
    if not isinstance(prospects, list) or not prospects:
        # Generate generic partnership targets to add
        for ptype, label, pain in TARGET_PARTNER_TYPES[:3]:
            msg = ai(
                f"Write a partnership pitch for a {label}.\n"
                f"Their pain: {pain}.\n"
                f"Pitch: NYSR white-labels AI content automation to their clients. They resell at $2k-5k/mo. We charge $297-997/mo wholesale. They pocket the margin.\n"
                f"Deal: 15% recurring OR wholesale pricing. No delivery burden on them. We fulfill everything.\n"
                f"Under 80 words. DM-style. Conversational.",
                max_tokens=120)
            
            if msg:
                supa("POST","conversation_log",{"contact_id":None,"channel":"linkedin",
                    "direction":"outbound","body":msg,"intent":"partnership_outreach",
                    "agent_name":"Partnership Engine"})
        return 0
    
    pitched = 0
    for partner in prospects:
        ptype = partner.get("partner_type","marketing_agency")
        pain_context = next((p[2] for p in TARGET_PARTNER_TYPES if p[0]==ptype), "their clients need automation")
        
        msg = ai(
            f"Write a partnership pitch for {partner.get('company_name','')} ({ptype}).\n"
            f"Contact: {partner.get('contact_name','there')}.\n"
            f"Client count: {partner.get('client_count',0)}.\n"
            f"Their context: {pain_context}.\n"
            f"Pitch: white-label NYSR at wholesale. They resell to clients. Zero delivery burden.\n"
            f"15% recurring commission OR wholesale pricing.\n"
            f"Under 80 words. Direct. No fluff.",
            max_tokens=120)
        
        if msg:
            supa("POST","conversation_log",{"contact_id":None,"channel":"email",
                "direction":"outbound","body":msg,"intent":"partnership_pitch",
                "agent_name":"Partnership Engine"})
            supa("PATCH","partnership_pipeline",{"status":"outreached"},
                 f"?id=eq.{partner['id']}")
            pitched += 1
    
    return pitched

def seed_partner_targets():
    """Seed initial partnership targets for Apollo outreach."""
    for ptype, label, _ in TARGET_PARTNER_TYPES:
        supa("POST","partnership_pipeline",{
            "company_name":f"Target: {label.title()} (2-50 employees, NY/Long Island)",
            "partner_type":ptype,
            "status":"prospect",
            "notes":f"Apollo query: {label}, 2-50 employees, US"
        })
    log.info(f"Seeded {len(TARGET_PARTNER_TYPES)} partnership target categories")

def run():
    log.info("ENGINE 5: Agency Partnership B2B Channel")
    
    # Ensure we have targets
    existing = supa("GET","partnership_pipeline","","?select=id&limit=1") or []
    if not existing: seed_partner_targets()
    
    pitched = outreach_potential_partners()
    supa("PATCH","closing_engines",{"last_run":now.isoformat()},
         "?engine_key=eq.partnerships")
    log.info(f"Partnership engine: {pitched} outreach messages sent")

if __name__ == "__main__": run()
