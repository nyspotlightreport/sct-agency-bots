#!/usr/bin/env python3
"""
bots/always_hunting_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━
Runs on every guardian tick (every 30 min). 
When other bots have nothing to do: this one always does.

Revenue activity every 30 minutes:
1. Apollo: search for 10 new prospects matching ICP
2. Deduplicate against Supabase (never email same person twice)  
3. Claude: write personalized email for each
4. Gmail: send immediately
5. Log results → Supabase

ICP (Ideal Customer Profile):
- Agency owners, marketing directors, content managers
- Small-medium businesses (10-200 employees)
- Titles: CMO, Marketing Director, Content Director, Agency Owner
- Industries: Marketing, Media, SaaS, Consulting
"""
import os, json, logging, smtplib, urllib.request, urllib.parse, time, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

log = logging.getLogger("hunting")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [HUNT] %(message)s")

APOLLO_KEY  = os.environ.get("APOLLO_API_KEY", "")
GMAIL_USER  = os.environ.get("GMAIL_USER", "seanb041992@gmail.com")
GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS", "")
ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL    = os.environ.get("SUPABASE_URL", "")
SUPA_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API    = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER   = os.environ.get("PUSHOVER_USER_KEY", "")

STORE_URL   = "https://nyspotlightreport.com/store/"
PAYMENT_LINKS = {
    "starter":   "https://buy.stripe.com/8x228r2N67QffzdfHp2400c",  # $97
    "growth":    "https://buy.stripe.com/00w00jgDW0nNaeT66P2400d",  # $297
    "dfy":       "https://buy.stripe.com/9B6dR9fzSeeDev9eDl2400f",  # $1,497
}

# ICP search parameters — rotated each run for variety
ICP_SEARCHES = [
    {"titles": ["CMO","Chief Marketing Officer"], "industries": ["Marketing","Advertising"]},
    {"titles": ["Marketing Director","VP Marketing"], "industries": ["SaaS","Software"]},
    {"titles": ["Agency Owner","Founder"], "industries": ["Marketing","Digital Agency"]},
    {"titles": ["Content Director","Content Manager"], "industries": ["Media","Publishing"]},
    {"titles": ["Head of Marketing","Director of Marketing"], "industries": ["E-commerce","Retail"]},
    {"titles": ["Marketing Manager","Growth Manager"], "industries": ["Startup","Technology"]},
]

def supa_request(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY, "Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json", "Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e:
        log.debug(f"Supa {method} {table}: {e}")
        return None

def already_contacted(email):
    """Check if this email is already in our system."""
    result = supa_request("GET", "contacts", 
        query=f"?email=eq.{urllib.parse.quote(email)}&select=id,stage")
    return bool(result and isinstance(result, list) and len(result) > 0)

def find_prospects(titles, industries, per_page=10):
    """Search Apollo for prospects matching ICP."""
    if not APOLLO_KEY:
        log.warning("APOLLO_API_KEY not set")
        return []
    
    try:
        payload = {
            "api_key": APOLLO_KEY,
            "per_page": per_page,
            "person_titles": titles,
            "organization_industry_tag_ids": [],
            "contact_email_status": ["verified", "likely to engage"],
            "page": random.randint(1, 20),  # Random page for variety
        }
        if industries:
            payload["q_organization_keyword_tags"] = industries
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.apollo.io/v1/mixed_people/search",
            data=data,
            headers={"Content-Type": "application/json", "Cache-Control": "no-cache"})
        
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            people = result.get("people", [])
            
            prospects = []
            for p in people:
                email = p.get("email","")
                if not email or email == "email_not_unlocked@domain.com":
                    continue
                prospects.append({
                    "first_name": p.get("first_name",""),
                    "last_name":  p.get("last_name",""),
                    "email":      email,
                    "title":      p.get("title",""),
                    "company":    p.get("organization",{}).get("name","") if p.get("organization") else "",
                    "employees":  p.get("organization",{}).get("estimated_num_employees",0) if p.get("organization") else 0,
                    "linkedin":   p.get("linkedin_url",""),
                })
            return prospects
    except Exception as e:
        log.error(f"Apollo search: {e}")
        return []

def generate_email(prospect):
    """Claude writes a hyper-personalized cold email."""
    if not ANTHROPIC:
        return None
    
    title   = prospect.get("title","")
    company = prospect.get("company","")
    fname   = prospect.get("first_name","")
    
    # Choose offer based on company size
    employees = prospect.get("employees", 0)
    if employees > 100:
        offer_name = "ProFlow Growth ($297/mo)"
        offer_link = PAYMENT_LINKS["growth"]
    else:
        offer_name = "ProFlow AI ($97/mo)"
        offer_link = PAYMENT_LINKS["starter"]
    
    prompt = f"""Cold email from Sean Thomas (NY Spotlight Report) to {fname}, {title} at {company}.

NY Spotlight Report built AI that automates content operations: social posts, blog, email newsletters, SEO — all 24/7 without staff. Currently running it ourselves.

Make it:
- Under 80 words body
- Subject: specific to their role/company (not generic)
- One CTA: {offer_link}
- Sound like a real human texting a peer
- No buzzwords, no "I hope this finds you well"
- Mention something specific about {title} or {company if company else 'their industry'}

Return ONLY:
Subject: [line]

[body]

Sean Thomas
NY Spotlight Report"""

    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":250,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude: {e}")
        return None

def send_email(to_email, subject, body, prospect_name=""):
    """Send via Gmail SMTP."""
    if not GMAIL_PASS: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = f"Sean Thomas <{GMAIL_USER}>"
        msg['To']      = to_email
        msg['Subject'] = subject
        msg['Reply-To']= GMAIL_USER
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        log.debug(f"SMTP {to_email}: {e}")
        return False

def run():
    log.info("ALWAYS-HUNTING BOT — 30min revenue tick")
    
    if not APOLLO_KEY:
        log.warning("No Apollo key — skipping prospect search")
        return {"status": "no_apollo_key"}
    
    # Pick random ICP rotation
    icp = random.choice(ICP_SEARCHES)
    log.info(f"ICP: {icp['titles'][0]} in {icp['industries'][0]}")
    
    # Find prospects
    prospects = find_prospects(icp["titles"], icp["industries"], per_page=10)
    log.info(f"Apollo returned: {len(prospects)} prospects")
    
    sent = 0
    skipped = 0
    errors  = 0
    sent_details = []
    
    for p in prospects[:5]:  # Max 5 per tick to stay under Gmail limits
        email = p.get("email","")
        fname = p.get("first_name","") or email.split("@")[0]
        
        if not email: continue
        
        # Deduplicate — never contact same person twice
        if already_contacted(email):
            skipped += 1
            log.info(f"  Skip (already contacted): {email}")
            continue
        
        # Generate personalized email
        email_content = generate_email(p)
        
        if email_content and "Subject:" in email_content:
            lines = email_content.strip().split('\n', 2)
            subject = lines[0].replace("Subject:","").strip()
            body    = lines[2].strip() if len(lines) > 2 else lines[-1].strip()
        else:
            # Hardcoded fallback
            subject = f"AI content system for {p.get('company','your business')}"
            body    = f"""{fname},

Built AI that runs entire content operations automatically — social, blog, email, SEO. 24/7 without staff.

Using it at NY Spotlight Report now. Thought it might help given your role.

ProFlow AI: $97/mo → {PAYMENT_LINKS['starter']}

Sean Thomas
NY Spotlight Report"""
        
        # Send
        if send_email(email, subject, body, fname):
            sent += 1
            sent_details.append(f"{fname} @ {p.get('company','?')}")
            log.info(f"  ✅ Sent to {fname} ({email})")
            
            # Save to Supabase
            supa_request("POST", "contacts", {
                "email":  email,
                "name":   f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                "stage":  "CONTACTED",
                "score":  55,
                "source": f"apollo_hunt_{icp['titles'][0].lower().replace(' ','_')}",
                "tags":   ["cold_outreach", "apollo_hunt"],
            })
            supa_request("POST", "conversation_log", {
                "channel":    "email",
                "direction":  "outbound",
                "body":       f"Cold email: {subject}",
                "intent":     "revenue_outreach",
                "agent_name": "AlwaysHuntingBot",
                "metadata":   {"email": email, "company": p.get("company",""), "subject": subject}
            })
        else:
            errors += 1
        
        time.sleep(2)  # Rate limit respect
    
    # Pushover only when emails sent (no spam)
    if sent > 0 and PUSH_API and PUSH_USER:
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"🎯 {sent} new outreach emails sent",
            "message":"\n".join(sent_details[:3]) + (f"\n+{sent-3} more" if sent > 3 else ""),
            "priority":-1}).encode()
        try: urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except: pass
    
    log.info(f"Hunt complete: {sent} sent, {skipped} skipped, {errors} errors")
    return {"sent": sent, "skipped": skipped, "errors": errors}

if __name__ == "__main__": run()
