# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
agents/outreach_engine.py — NYSR Automated Outreach Engine
Sloane Pierce + Jeff Banks working together.
Pulls leads from Supabase/Apollo → generates personalized emails → sends via SMTP → logs to CRM.
Runs daily. The department that turns $0 into $97+.
"""
# AG-QUARANTINE-GMAIL-ZERO-20260328-1953: import os, sys, json, logging, time, smtplib, base64  # GMAIL_ZERO VIOLATION - DISABLED
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
sys.path.insert(0, ".")
log = logging.getLogger("outreach")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [OUTREACH] %(message)s")
import urllib.request as urlreq, urllib.parse

# === MEMORY ENGINE (auto-wired) ===
import sys as _sys
_sys.path.insert(0, '/opt/nysr')
try:
    from agent_memory_engine import read_memory as _read_memory, write_memory as _write_memory
    _agent_name = __file__.split('/')[-1].replace('.py','')
    _prior_memory = _read_memory(_agent_name)
except:
    _read_memory = lambda x: {}
    _write_memory = lambda x, y: None
    _prior_memory = {}
# === END MEMORY ENGINE ===



ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")
# AG-QUARANTINE-GMAIL-ZERO-20260328-1953: SMTP_USER = os.environ.get("SMTP_USER", "nyspotlightreport@gmail.com")  # GMAIL_ZERO VIOLATION - DISABLED
# AG-QUARANTINE-GMAIL-ZERO-20260328-1953: SMTP_PASS = os.environ.get("GMAIL_APP_PASS", "")  # GMAIL_ZERO VIOLATION - DISABLED
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")

def push(t, m, p=0):
    if not PUSH_API: return
    try: urlreq.urlopen("https://api.pushover.net/1/messages.json", urllib.parse.urlencode({"token": PUSH_API, "user": PUSH_USER, "title": t[:100], "message": m[:1000], "priority": p}).encode(), timeout=5)
    except Exception:  # noqa: bare-except

        pass
def claude(system, user, max_tokens=500):
    if not ANTHROPIC: return ""
    try:
        data = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
        req = urlreq.Request("https://api.anthropic.com/v1/messages", data=data, headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC, "anthropic-version": "2023-06-01"})
        with urlreq.urlopen(req, timeout=60) as r: return json.loads(r.read())["content"][0]["text"]
    except: return ""

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    body = json.dumps(data).encode() if data else None
    req = urlreq.Request(f"{SUPA_URL}/rest/v1/{table}{query}", data=body, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urlreq.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def send_email(to, subject, body_html):
    # AG-GMAIL-ZERO: Gmail SMTP disabled. Reroute to Resend.
    import os,urllib.request,json as _j
    _key=os.getenv("RESEND_API_KEY","")
    if not _key: print("[AG] No RESEND_API_KEY - email blocked"); return False
    try:
        _b=_j.dumps({"from":"editor-in-chief@nyspotlightreport.com","to":[to],"subject":subject,"html":body_html}).encode()
        _r=urllib.request.Request("https://api.resend.com/emails",data=_b,headers={"Authorization":"Bearer "+_key,"Content-Type":"application/json"},method="POST")
        urllib.request.urlopen(_r,timeout=15); return True
    except Exception as _e: print("[RESEND]",_e); return False
    # AG: Original SMTP code disabled below - return above prevents execution
# AG-QUARANTINE-GMAIL-ZERO-20260328-1953:     if not SMTP_PASS: log.warning("No GMAIL_APP_PASS — cannot send"); return False  # GMAIL_ZERO VIOLATION - DISABLED
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Sean Thomas <{SMTP_USER}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg["Reply-To"] = SMTP_USER
        msg.attach(MIMEText(body_html, "html"))
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP_SSL("[GMAIL-SMTP-REDACTED]", 465, timeout=15) as s:
# AG-FINAL-KILL-GMAIL-ZERO-20260328:             s.login(SMTP_USER, SMTP_PASS)
# AG-FINAL-KILL-GMAIL-ZERO-20260328:             s.sendmail(SMTP_USER, to, msg.as_string())
        log.info(f"  SENT to {to}: {subject}")
        return True
    except Exception as e:
        log.error(f"  FAILED {to}: {e}")
        return False

SYSTEM_PROMPT = """You are Sloane Pierce, Sales Director at NY Spotlight Report. Write a personalized cold email.
Rules: 4 sentences max. First line references THEIR company specifically. No fluff. End with soft CTA (15-min call or demo).
Sign as Sean Thomas, Chairman, NY Spotlight Report."""

OFFERS = {
    "starter": {"name": "ProFlow AI", "price": "$97/mo", "hook": "automates daily blog, social, and newsletter content"},
    "dfy": {"name": "DFY Agency Automation", "price": "$4,997", "hook": "full AI agency buildout with 30 days done-for-you content"},
}

def generate_email(prospect):
    name = prospect.get("name", "").split()[0] if prospect.get("name") else "there"
    company = prospect.get("company", "your company")
    title = prospect.get("title", "")
    score = prospect.get("score", 50)
    offer = OFFERS["dfy"] if score >= 80 else OFFERS["starter"]
    body = claude(SYSTEM_PROMPT,
        f"Prospect: {name}, {title} at {company}\nOffer: {offer['name']} — {offer['price']} — {offer['hook']}\nWrite subject line + email body. Keep it under 100 words.")
    if not body:
        body = f"""Subject: Quick question about {company}'s content\n\nHi {name},\n\nI noticed {company} is growing and probably feeling the content bottleneck — more platforms, more posts, more pressure. We built an AI system at NY Spotlight Report that handles daily blog posts, social media, and newsletters autonomously.\n\n{offer['name']} starts at {offer['price']}. Worth a 15-minute call this week?\n\nBest,\nSean Thomas\nChairman, NY Spotlight Report\nnyspotlightreport.com"""
    return body, offer

def run(max_emails=5):
    log.info("="*60)
    log.info("OUTREACH ENGINE — Sloane Pierce + Jeff Banks — SENDING")
    log.info("="*60)
    # Pull leads from Supabase
    leads = supa("GET", "contacts", query="?stage=eq.LEAD&order=score.desc&limit=20") or []
    if not isinstance(leads, list): leads = []
    log.info(f"Found {len(leads)} leads in pipeline")
    sent = 0; failed = 0
    for lead in leads[:max_emails]:
        email = lead.get("email", "")
        if not email or "@" not in email:
            log.info(f"  SKIP {lead.get('name','?')} — no email"); continue
        body, offer = generate_email(lead)
        # Extract subject from Claude output
        lines = body.strip().split("\n")
        subject = lines[0].replace("Subject:", "").strip() if lines[0].lower().startswith("subject") else f"Quick question about {lead.get('company','your company')}"
        email_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else body
        # Wrap in HTML
        html = f'<div style="font-family:Georgia,serif;font-size:15px;line-height:1.7;color:#1a1a1a;max-width:600px">{email_body.replace(chr(10), "<br>")}<br><br><a href="https://nyspotlightreport.com/proflow/" style="color:#c9a84c">nyspotlightreport.com/proflow</a></div>'
        if send_email(email, subject, html):
            sent += 1
            # Update contact stage
            supa("PATCH", "contacts", {"stage": "CONTACTED", "last_activity": datetime.utcnow().isoformat()}, f"?email=eq.{urllib.parse.quote(email)}")
        else:
            failed += 1
    report = f"Outreach: {sent} sent, {failed} failed out of {len(leads)} leads"
    log.info(f"\n{report}")
    push("Outreach Engine", report, 0 if sent > 0 else -1)
    supa("POST", "director_outputs", {"director": "Outreach Engine", "output_type": "daily_outreach",
        "content": report, "metrics": json.dumps({"sent": sent, "failed": failed, "total_leads": len(leads)}),
        "created_at": datetime.utcnow().isoformat()})
    return {"sent": sent, "failed": failed}

if __name__ == "__main__":
    run()
