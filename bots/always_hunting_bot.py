#!/usr/bin/env python3
"""
bots/always_hunting_bot.py - UPGRADED
Uses nyspotlightreportny@gmail.com (business email - just restored)
Better deliverability: company domain looks professional vs personal gmail
"""
import os, json, logging, smtplib, urllib.request, urllib.parse, time, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

log = logging.getLogger("hunting")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [HUNT] %(message)s")

APOLLO_KEY  = os.environ.get("APOLLO_API_KEY","")
# UPGRADED: use business email for sender (better deliverability)
GMAIL_USER  = os.environ.get("GMAIL_USER", os.environ.get("BUSINESS_EMAIL","nyspotlightreportny@gmail.com"))
GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS", os.environ.get("BUSINESS_EMAIL_PASS",""))
SENDER_NAME = os.environ.get("SENDER_NAME","Sean Thomas | NY Spotlight Report")
ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL    = os.environ.get("SUPABASE_URL","")
SUPA_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API    = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER   = os.environ.get("PUSHOVER_USER_KEY","")

STORE_URL   = "https://nyspotlightreport.com/store/"
PAYMENT_LINKS = {
    "starter":  "https://buy.stripe.com/8x228r2N67QffzdfHp2400c",
    "growth":   "https://buy.stripe.com/00w00jgDW0nNaeT66P2400d",
    "elite":    "https://buy.stripe.com/aFacN5fzSdazfzd3YH2400e",
    "dfy":      "https://buy.stripe.com/9B6dR9fzSeeDev9eDl2400f",
    "agency":   "https://buy.stripe.com/8x214n9bu3zZ86L9j12400g",
    "enterprise":"https://buy.stripe.com/00weVd5ZigmL86Ldzh2400h",
}

ICP_SEARCHES = [
    {"titles":["CMO","Chief Marketing Officer"],"industries":["Marketing","Advertising"],"offer":"growth"},
    {"titles":["Marketing Director","VP Marketing"],"industries":["SaaS","Software"],"offer":"starter"},
    {"titles":["Agency Owner","Founder"],"industries":["Marketing","Digital Agency"],"offer":"dfy"},
    {"titles":["Content Director","Content Manager"],"industries":["Media","Publishing"],"offer":"growth"},
    {"titles":["Head of Marketing","Director of Marketing"],"industries":["E-commerce","Retail"],"offer":"starter"},
    {"titles":["Marketing Manager","Growth Manager"],"industries":["Startup","Technology"],"offer":"starter"},
    {"titles":["CEO","Founder"],"industries":["Consulting","Professional Services"],"offer":"elite"},
    {"titles":["VP Sales","Head of Growth"],"industries":["SaaS","B2B"],"offer":"growth"},
]

def supa_req(method, table, data=None, query=""):
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
    result = supa_req("GET","contacts",query=f"?email=eq.{urllib.parse.quote(email)}&select=id")
    return bool(result and isinstance(result,list) and len(result)>0)

def find_prospects(icp, per_page=10):
    if not APOLLO_KEY: return []
    try:
        payload = {
            "api_key": APOLLO_KEY,
            "per_page": per_page,
            "person_titles": icp["titles"],
            "contact_email_status": ["verified","likely to engage"],
            "page": random.randint(1,30),
        }
        if icp.get("industries"):
            payload["q_organization_keyword_tags"] = icp["industries"]
        data = json.dumps(payload).encode()
        req = urllib.request.Request("https://api.apollo.io/v1/mixed_people/search",
            data=data, headers={"Content-Type":"application/json","Cache-Control":"no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            people = json.loads(r.read()).get("people",[])
            return [{"first_name":p.get("first_name",""),
                     "last_name": p.get("last_name",""),
                     "email":     p.get("email",""),
                     "title":     p.get("title",""),
                     "company":   (p.get("organization") or {}).get("name",""),
                     "employees": (p.get("organization") or {}).get("estimated_num_employees",0),
                     "offer":     icp.get("offer","starter")}
                    for p in people if p.get("email") and "email_not_unlocked" not in p.get("email","")]
    except Exception as e:
        log.error(f"Apollo: {e}"); return []

def generate_email(p):
    if not ANTHROPIC: return None
    offer_key = p.get("offer","starter")
    link = PAYMENT_LINKS.get(offer_key, PAYMENT_LINKS["starter"])
    
    prompt = f"""You are writing a cold email FROM Sean Thomas, founder of NY Spotlight Report (nyspotlightreportny@gmail.com).

TO: {p.get('first_name','')} {p.get('last_name','')}, {p.get('title','')} at {p.get('company','')}

NY Spotlight Report automates entire content operations: social posts, blog, email, SEO, outreach - all running 24/7 without manual work. Proven on our own business.

Craft a cold email that:
- Is under 75 words body
- Subject line: hyper-specific to their role/company (never generic)
- One CTA: {link}
- Sounds like a peer texting, not marketing
- No "I hope this finds you well", no buzzwords
- Specific pain point for a {p.get('title','')} at a {p.get('employees',50)}-person company

Return ONLY:
Subject: [line]

[body]

Sean Thomas
NY Spotlight Report
nyspotlightreportny@gmail.com"""

    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":250,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude: {e}"); return None

def send_email(to_email, subject, body):
    if not GMAIL_PASS:
        log.warning(f"No Gmail app pass for {GMAIL_USER} — need to add BUSINESS_EMAIL_PASS secret")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = f"{SENDER_NAME} <{GMAIL_USER}>"
        msg['To']      = to_email
        msg['Subject'] = subject
        msg['Reply-To']= GMAIL_USER
        msg.attach(MIMEText(body,'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com',465,timeout=15) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        log.error(f"SMTP {to_email}: {e}"); return False

def run():
    log.info(f"ALWAYS-HUNTING BOT — sender: {GMAIL_USER}")
    icp = random.choice(ICP_SEARCHES)
    prospects = find_prospects(icp, per_page=10)
    log.info(f"Apollo returned {len(prospects)} prospects for {icp['titles'][0]}")
    
    sent=0; skipped=0
    
    for p in prospects[:5]:
        email = p.get("email","")
        fname = p.get("first_name","") or email.split("@")[0]
        if not email: continue
        if already_contacted(email): skipped+=1; continue
        
        content = generate_email(p)
        if content and "Subject:" in content:
            lines   = content.strip().split("\n",2)
            subject = lines[0].replace("Subject:","").strip()
            body    = lines[2].strip() if len(lines)>2 else lines[-1].strip()
        else:
            offer_link = PAYMENT_LINKS.get(p.get("offer","starter"), PAYMENT_LINKS["starter"])
            subject = f"AI content system for {p.get('company','your business')}"
            body    = f"""{fname},

Running an AI system that handles all content ops automatically — social, blog, email, SEO. 24/7, no staff needed.

Using it at NY Spotlight Report now. Thought it might help.

→ {offer_link}

Sean Thomas
NY Spotlight Report"""
        
        if send_email(email, subject, body):
            sent+=1
            supa_req("POST","contacts",{"email":email,"name":f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                "stage":"CONTACTED","score":55,"source":f"apollo_hunt","tags":["cold_outreach","apollo_hunt"]})
            supa_req("POST","conversation_log",{"channel":"email","direction":"outbound",
                "body":f"Cold email: {subject}","intent":"revenue_outreach","agent_name":"AlwaysHuntingBot",
                "metadata":{"email":email,"company":p.get("company",""),"sender":GMAIL_USER}})
            log.info(f"  ✅ {fname} @ {p.get('company','?')} — {p.get('email','')}")
        else:
            log.warning(f"  ❌ Failed: {email}")
        time.sleep(2)
    
    if sent>0 and PUSH_API and PUSH_USER:
        data=json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"🎯 {sent} emails sent from nyspotlightreportny@gmail.com",
            "message":f"ICP: {icp['titles'][0]}\nSent: {sent}\nSkipped: {skipped}",
            "priority":-1}).encode()
        try: urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except: pass
    
    log.info(f"Done: {sent} sent, {skipped} skipped")
    return {"sent":sent,"skipped":skipped,"sender":GMAIL_USER}

if __name__ == "__main__": run()
