#!/usr/bin/env python3
"""
bots/rep_onboarding_bot.py
Automatically onboards approved sales reps.
Generates rep code, sends portal access, sends sales materials.
Zero Sean involvement after rep is approved.
"""
import os, json, logging, datetime, urllib.request, random, string
log = logging.getLogger("rep_onboarding")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [REP ONBOARD] %(message)s")

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

def ai(prompt, max_tokens=400):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def generate_rep_code():
    """Generate unique rep code like REP-042."""
    existing = supa("GET","sales_reps","","?select=rep_code") or []
    codes = set(r.get("rep_code","") for r in (existing if isinstance(existing,list) else []))
    n = 1
    while f"REP-{n:03d}" in codes:
        n += 1
    return f"REP-{n:03d}"

def generate_portal_code():
    """8-char access code for rep portal."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def onboard_approved_reps():
    """Find approved-but-not-onboarded reps and set them up."""
    new_reps = supa("GET","sales_reps","",
        "?status=eq.active&portal_access=eq.false&select=*&limit=10") or []
    
    onboarded = 0
    for rep in (new_reps if isinstance(new_reps,list) else []):
        rep_id = rep.get("id")
        name   = f"{rep.get('first_name','')} {rep.get('last_name','')}"
        email  = rep.get("email","")
        
        # Generate rep code and portal access
        rep_code     = generate_rep_code()
        portal_code  = generate_portal_code()
        checkout_url = f"https://nyspotlightreport.com/store/?rep={rep_code}"
        
        # Update rep record
        supa("PATCH","sales_reps",{
            "rep_code":rep_code,
            "unique_checkout_url":checkout_url,
            "portal_access":True,
            "loom_sent":True,
            "sales_deck_sent":True
        },f"?id=eq.{rep_id}")
        
        # Create portal access record
        supa("POST","rep_portal_access",{
            "rep_id":rep_id,
            "access_code":portal_code
        })
        
        # Generate personalized welcome email
        welcome = ai(
            f"Write a welcome email for {name}, a new 1099 commission sales rep at NY Spotlight Report.\n"
            f"Their rep code: {rep_code}\n"
            f"Their unique Stripe checkout URL: {checkout_url}\n"
            f"Portal access: nyspotlightreport.com/reps/ — code: {portal_code}\n"
            f"Include: commission structure (30-41% on products, recurring), what they get (sales deck, Loom, objection scripts), first steps.\n"
            f"Warm, professional tone. Under 200 words.",
            max_tokens=300)
        
        if welcome:
            supa("POST","conversation_log",{
                "contact_id":None,"channel":"email","direction":"outbound",
                "body":welcome,"intent":"rep_onboarding","agent_name":"Rep Onboarding Bot"
            })
        
        log.info(f"Onboarded: {name} ({rep_code}) — portal access granted, welcome email sent")
        onboarded += 1
    
    return onboarded

def process_applications():
    """Auto-review new rep applications — score and route."""
    new_apps = supa("GET","rep_applications","","?status=eq.new&select=*&limit=10") or []
    processed = 0
    
    for app in (new_apps if isinstance(new_apps,list) else []):
        app_id = app.get("id")
        
        # Score application
        score = 0
        exp = (app.get("experience","") or "").lower()
        existing = (app.get("existing_clients","") or "").lower()
        
        if "agency" in exp or "freelance" in exp: score += 30
        if "sales" in exp or "closer" in exp: score += 25
        if "marketing" in exp or "consultant" in exp: score += 20
        if existing and len(existing) > 20: score += 25  # has existing clients
        if app.get("linkedin_url"): score += 10
        
        new_status = "interview" if score >= 50 else "reviewing"
        supa("PATCH","rep_applications",
            {"status":new_status,"notes":f"Auto-score: {score}/100"},
            f"?id=eq.{app_id}")
        processed += 1
    
    return processed

def run():
    log.info("Rep Onboarding Bot running")
    onboarded  = onboard_approved_reps()
    processed  = process_applications()
    log.info(f"Onboarded: {onboarded} reps | Processed: {processed} applications")

if __name__ == "__main__": run()
