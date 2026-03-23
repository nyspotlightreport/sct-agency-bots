"""
Client Onboarding Bot — Phase 4
Auto-onboards new portal users. Sends welcome sequence, sets up initial project,
creates first ticket, sends CSAT surveys post-resolution.
Every new enterprise client = fully onboarded in <1 hour automatically.
"""
import os, json, logging, datetime, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ONBOARD] %(message)s")
log = logging.getLogger("onboard")

SUPABASE_URL  = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
GMAIL_USER    = os.environ.get("GMAIL_USER","")
GMAIL_PASS    = os.environ.get("GMAIL_APP_PASS","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.error, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}",
               "Content-Type":"application/json","Prefer":"return=representation"}
    req = urllib.request.Request(url,data=payload,method=method,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code}")
        return None

def ai(prompt):
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":800,
                        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,headers={
        "Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def push(title, msg):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER_KEY,"title":title,"message":msg}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req,timeout=10)
    except Exception:  # noqa: bare-except

        pass
def send_email(to_email, subject, html_body):
    if not GMAIL_USER or not GMAIL_PASS:
        log.warning(f"Email not configured — would send to {to_email}: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"NYSR Agency <{GMAIL_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        log.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        log.warning(f"Email failed to {to_email}: {e}")
        return False

def onboard_new_client(user):
    """Full onboarding sequence for a new portal user."""
    name = user.get("name","") or user["email"].split("@")[0]
    plan = user.get("plan","starter")
    email = user["email"]
    portal_url = "https://nyspotlightreport.com/portal/"

    # Generate personalized welcome
    welcome_html = ai(
        f"Write a professional HTML welcome email for a new {plan} plan client named {name} "
        f"onboarding to NY Spotlight Report AI Agency. Include: "
        f"1) Warm welcome 2) What they can do in the portal ({portal_url}) "
        f"3) How to submit a ticket 4) Their dedicated support info "
        f"5) CTA button to access portal. Styled HTML, professional, concise."
    )

    if welcome_html:
        send_email(email, f"Welcome to NYSR Agency, {name}! 🚀", welcome_html)

    # Create onboarding project
    supa("POST","projects",{
        "name":f"{name} — Onboarding",
        "description":f"Client onboarding project for {name} ({plan} plan)",
        "status":"active","priority":"high",
        "client_id":user.get("contact_id"),
        "due_date":(datetime.date.today()+datetime.timedelta(days=7)).isoformat()
    })

    # Create welcome ticket
    supa("POST","tickets",{
        "portal_user_id":user["id"],
        "title":"Welcome to NYSR Agency — Onboarding",
        "description":f"Automated onboarding ticket for {name}. Plan: {plan}.",
        "status":"in_progress","priority":"medium","category":"onboarding","source":"system",
        "first_response_at":datetime.datetime.utcnow().isoformat()
    })

    # Create welcome deliverable
    supa("POST","deliverables",{
        "portal_user_id":user["id"],
        "title":"Welcome Kit & Getting Started Guide",
        "description":"Your complete guide to NYSR Agency tools and automations.",
        "status":"delivered","delivered_at":datetime.datetime.utcnow().isoformat(),
        "file_url":"https://nyspotlightreport.com/wiki/"
    })

    # Mark onboarded
    supa("PATCH","portal_users",{"onboarded":True},query=f"?id=eq.{user['id']}")
    log.info(f"Onboarded: {name} ({email}) — {plan}")
    push("🎉 New Client Onboarded", f"{name} ({plan}) — {email}")

def send_csat_surveys():
    """Send CSAT surveys for recently resolved tickets."""
    cutoff = (datetime.datetime.utcnow()-datetime.timedelta(hours=24)).isoformat()
    resolved = supa("GET","tickets",
        f"?status=eq.resolved&resolved_at=gte.{cutoff}&portal_user_id=not.is.null&select=*") or []
    for t in resolved:
        # Check if survey already sent
        existing = supa("GET","satisfaction_surveys",
            f"?ticket_id=eq.{t['id']}&select=id&limit=1") or []
        if existing: continue
        # Get user email
        user = supa("GET","portal_users",f"?id=eq.{t['portal_user_id']}&select=email,name&limit=1") or []
        if not user: continue
        u = user[0]
        survey = supa("POST","satisfaction_surveys",{
            "portal_user_id":t["portal_user_id"],
            "ticket_id":t["id"],
            "survey_type":"csat",
            "sent_at":datetime.datetime.utcnow().isoformat()
        })
        survey_id = survey[0]["id"] if isinstance(survey,list) and survey else ""
        portal_url = f"https://nyspotlightreport.com/portal/?csat={survey_id}"
        csat_html = f"""
        <div style="font-family:Inter,sans-serif;max-width:500px;margin:0 auto;padding:2rem">
        <h2 style="color:#7c3aed">How did we do? ⭐</h2>
        <p>Hi {u.get('name','there')}, your ticket <strong>"{t['title'][:60]}"</strong> was resolved.</p>
        <p>How would you rate your experience? (1 click)</p>
        <div style="display:flex;gap:.5rem;margin:1.5rem 0">
        {''.join(f'<a href="{portal_url}&score={i}" style="background:#7c3aed;color:#fff;padding:.75rem 1.25rem;border-radius:8px;text-decoration:none;font-weight:600">{i}⭐</a>' for i in range(1,6))}
        </div>
        <p style="color:#64748b;font-size:.875rem">Takes 2 seconds. Helps us improve.</p>
        </div>"""
        send_email(u["email"], f"⭐ How did we do on ticket #{t.get('ticket_number','')}?", csat_html)
        log.info(f"CSAT sent for ticket #{t.get('ticket_number','')} to {u['email']}")

def run():
    log.info("=== Client Onboarding Bot ===")
    # Onboard any un-onboarded users
    new_users = supa("GET","portal_users","?onboarded=eq.false&active=eq.true&select=*") or []
    for u in new_users:
        onboard_new_client(u)
        time.sleep(2)
    send_csat_surveys()
    log.info(f"Onboarded {len(new_users)} users. Done.")

if __name__ == "__main__":
    run()
