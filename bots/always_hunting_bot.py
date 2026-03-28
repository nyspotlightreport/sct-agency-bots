# AG-GMAIL-ZERO ENFORCED: Gmail credentials removed. Use Resend API.
# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
bots/always_hunting_bot.py — PRODUCTION FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SMTP architecture (zero new credentials needed):
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: SMTP server:  [GMAIL-SMTP-REDACTED]:465
# AG-NUCLEAR-GMAIL-ZERO-20260328:   Auth:         [GMAIL-REDACTED-USE-RESEND] + # GMAIL_APP_PASS_DISABLED (already live)
  From header:  "Sean Thomas | NY Spotlight Report <[GMAIL-REDACTED-USE-RESEND]>"
  Reply-To:     [GMAIL-REDACTED-USE-RESEND]
  
Recipient sees: From → NY Spotlight Report
Replies go to:  [GMAIL-REDACTED-USE-RESEND] (business inbox)

Runs every 30 min. Finds 5 fresh ICP prospects via Apollo.
Claude personalizes each email. Sends immediately. Logs to Supabase.
"""
import os, json, logging, smtplib, urllib.request, urllib.parse, time, random

from genius_thinking_engine import genius_email, get_genius_engine
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

log = logging.getLogger("hunting")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# ── SMTP CONFIG — uses existing working credentials ───────
# SMTP_DISABLED_USER    = os.environ.get("# SMTP_DISABLED_USER",     "[GMAIL-REDACTED-USE-RESEND]")
# SMTP_DISABLED_PASS    = os.environ.get("# GMAIL_APP_PASS_DISABLED", os.environ.get("BUSINESS_EMAIL_PASS",""))
FROM_NAME    = os.environ.get("# SMTP_DISABLED_FROM_NAME", "Sean Thomas | NY Spotlight Report")
FROM_EMAIL   = os.environ.get("BUSINESS_EMAIL","[GMAIL-REDACTED-USE-RESEND]")  # display name
REPLY_TO     = os.environ.get("REPLY_TO_EMAIL", "[GMAIL-REDACTED-USE-RESEND]")

# ── OTHER CREDENTIALS ─────────────────────────────────────
APOLLO_KEY   = os.environ.get("APOLLO_API_KEY","")
ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL     = os.environ.get("SUPABASE_URL","")
SUPA_KEY     = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API     = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER    = os.environ.get("PUSHOVER_USER_KEY","")

STORE_URL    = "https://nyspotlightreport.com/store/"
LINKS = {
    "starter":   "https://buy.stripe.com/8x228r2N67QffzdfHp2400c",
    "growth":    "https://buy.stripe.com/00w00jgDW0nNaeT66P2400d",
    "elite":     "https://buy.stripe.com/aFacN5fzSdazfzd3YH2400e",
    "dfy":       "https://buy.stripe.com/9B6dR9fzSeeDev9eDl2400f",
    "agency":    "https://buy.stripe.com/8x214n9bu3zZ86L9j12400g",
    "enterprise":"https://buy.stripe.com/00weVd5ZigmL86Ldzh2400h"}

ICP = [
    {"titles":["CMO","Chief Marketing Officer"],      "industries":["Marketing","Advertising"],       "offer":"growth"},
    {"titles":["Marketing Director","VP Marketing"],   "industries":["SaaS","Software"],               "offer":"starter"},
    {"titles":["Agency Owner","Founder"],              "industries":["Marketing","Digital Agency"],    "offer":"dfy"},
    {"titles":["Content Director","Content Manager"],  "industries":["Media","Publishing"],            "offer":"growth"},
    {"titles":["Head of Marketing"],                   "industries":["E-commerce","Retail"],           "offer":"starter"},
    {"titles":["Marketing Manager","Growth Manager"],  "industries":["Startup","Technology"],          "offer":"starter"},
    {"titles":["CEO","Founder"],                       "industries":["Consulting","Services"],         "offer":"elite"},
    {"titles":["VP Sales","Head of Growth"],           "industries":["SaaS","B2B"],                   "offer":"growth"},
    {"titles":["Creative Director","Brand Manager"],   "industries":["Fashion","Consumer Goods"],      "offer":"starter"},
    {"titles":["Digital Marketing Manager"],           "industries":["Healthcare","Finance"],          "offer":"starter"},
]

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def already_contacted(email):
    r = supa("GET","contacts",query=f"?email=eq.{urllib.parse.quote(email)}&select=id")
    return bool(r and isinstance(r,list) and len(r)>0)

def find_prospects(icp):
    if not APOLLO_KEY: return []
    try:
        data = json.dumps({
            "api_key": APOLLO_KEY,
            "per_page": 10,
            "person_titles": icp["titles"],
            "q_organization_keyword_tags": icp.get("industries",[]),
            "contact_email_status": ["verified","likely to engage"],
            "page": random.randint(1,40)}).encode()
        req = urllib.request.Request("https://api.apollo.io/v1/mixed_people/search",
            data=data, headers={"Content-Type":"application/json","Cache-Control":"no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return [{"first_name":p.get("first_name",""),
                     "last_name": p.get("last_name",""),
                     "email":     p.get("email",""),
                     "title":     p.get("title",""),
                     "company":   (p.get("organization") or {}).get("name",""),
                     "employees": (p.get("organization") or {}).get("estimated_num_employees",0),
                     "offer":     icp.get("offer","starter")}
                    for p in json.loads(r.read()).get("people",[])
                    if p.get("email") and "email_not_unlocked" not in p.get("email","")]
    except Exception as e:
        log.error(f"Apollo: {e}"); return []

def personalize(p):
    if not ANTHROPIC: return None
    link = LINKS.get(p.get("offer","starter"), LINKS["starter"])
    prompt = f"""Cold email from Sean Thomas, founder of NY Spotlight Report ([GMAIL-REDACTED-USE-RESEND]).

TO: {p.get('first_name','')} {p.get('last_name','')}, {p.get('title','')} at {p.get('company','')} ({p.get('employees',50)} employees)

We built AI that runs entire content operations automatically: social posts, blog, email, SEO, outreach. All 24/7. No staff. Running it on our own business.

Write email that is:
- Under 70 words body (strict)
- Subject: 100% specific to {p.get('title','')} at {p.get('company','')} — NOT generic  
- One CTA: {link}
- Peer-to-peer tone, zero corporate speak
- No greetings like "I hope this finds you well"

Format:
Subject: [line]

[body]

Sean Thomas
NY Spotlight Report"""

    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":250,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,
                 "anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude: {e}"); return None

def send(to_email, subject, body):
    """
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: Send via [GMAIL-REDACTED-USE-RESEND] SMTP (working credentials).
    From header displays as [GMAIL-REDACTED-USE-RESEND].
    Reply-To set to [GMAIL-REDACTED-USE-RESEND].
    Recipient sees business email. Replies go to business inbox.
    """
    if not # SMTP_DISABLED_PASS:
# AG-NUCLEAR-GMAIL-ZERO-20260328:         log.error("# GMAIL_APP_PASS_DISABLED not configured")
        return False
    try:
        msg = MIMEMultipart('alternative')
        # This is what recipient sees — the business email
        msg['From']     = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To']       = to_email
        msg['Subject']  = subject
        msg['Reply-To'] = REPLY_TO
        msg.attach(MIMEText(body, 'plain'))
        
        # Auth uses the working smtp account
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.# SMTP_DISABLED_SSL('[GMAIL-SMTP-REDACTED]', 465, timeout=15) as s:
# AG-NUCLEAR-GMAIL-ZERO-20260328:             s.login(# SMTP_DISABLED_USER, # SMTP_DISABLED_PASS)
# AG-NUCLEAR-GMAIL-ZERO-20260328:             s.sendmail(# SMTP_DISABLED_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        log.error(f"SMTP: {e}"); return False

def run():
    log.info(f"{'='*55}")
    log.info(f"HUNTING BOT | SMTP: {# SMTP_DISABLED_USER} | FROM: {FROM_EMAIL}")
    log.info(f"{'='*55}")

    if not # SMTP_DISABLED_PASS:
# AG-NUCLEAR-GMAIL-ZERO-20260328:         log.error("NO # GMAIL_APP_PASS_DISABLED — emails cannot send. Check GitHub Secrets.")
        return {"error": "no_smtp_pass"}

    icp = random.choice(ICP)
    prospects = find_prospects(icp)
    log.info(f"Apollo: {len(prospects)} prospects | ICP: {icp['titles'][0]}")

    sent=0; skipped=0; failed=0
    details=[]

    for p in prospects[:5]:
        email = p.get("email","")
        fname = p.get("first_name","") or email.split("@")[0]
        if not email: continue
        if already_contacted(email): skipped+=1; continue

        # GENIUS ENGINE: Uses Munger-Musk-Da Vinci thinking for email
        employees = p.get("employees", 50)
        offer_map = {"starter":"proflow_ai","growth":"proflow_growth","elite":"proflow_elite",
                     "dfy":"dfy","agency":"agency"}
        offer_key = offer_map.get(p.get("offer","starter"), "proflow_ai")
        genius_result = genius_email(
            fname, p.get("title",""), p.get("company",""), employees, offer_key
        )
        content = genius_result.get("text","") if genius_result else None
        if content and "Subject:" in content:
            parts   = content.strip().split("\n", 2)
            subject = parts[0].replace("Subject:","").strip()
            body    = parts[2].strip() if len(parts)>2 else parts[-1]
        else:
            link    = LINKS.get(p.get("offer","starter"), LINKS["starter"])
            subject = f"Content automation for {p.get('company','your business')}"
            body    = f"{fname},\n\nBuilt AI that runs content ops automatically — social, blog, email, SEO. 24/7 without staff.\n\nThought it might help given your role.\n\n→ {link}\n\nSean Thomas\nNY Spotlight Report"

        if send(email, subject, body):
            sent += 1
            details.append(f"{fname} @ {p.get('company','?')}")
            log.info(f"  ✅ {fname} ({email})")
            supa("POST","contacts",{"email":email,
                "name": f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                "stage":"CONTACTED","score":55,"source":"apollo_hunt",
                "tags":["cold_outreach","apollo_hunt"]})
            supa("POST","conversation_log",{"channel":"email","direction":"outbound",
                "body":f"Cold email: {subject}","intent":"revenue_outreach",
                "agent_name":"HuntingBot"})
        else:
            failed+=1
            log.warning(f"  ❌ Failed: {email}")
        time.sleep(2)

    if sent > 0 and PUSH_API and PUSH_USER:
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"🎯 {sent} emails sent",
            "message":"\n".join(details[:3])+(f"\n+{sent-3}" if sent>3 else "")+
                      f"\n\nFrom: {FROM_EMAIL}\nReplies→ {REPLY_TO}",
            "priority":-1}).encode()
        try: urllib.request.urlopen(urllib.request.Request(
            "https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except Exception:  # noqa: bare-except

            pass
    log.info(f"Done: sent={sent} skipped={skipped} failed={failed}")
    return {"sent":sent,"skipped":skipped,"failed":failed,
            "smtp":# SMTP_DISABLED_USER,"from":FROM_EMAIL}

if __name__ == "__main__": run()
