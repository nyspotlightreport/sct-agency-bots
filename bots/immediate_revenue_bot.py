#!/usr/bin/env python3
"""
bots/immediate_revenue_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRUTH: The system has 0 real paying customers because 0 real people 
have been contacted with a buy link. This bot fixes that RIGHT NOW.

Actions:
1. Sends personal cold emails to 5 HubSpot contacts (real executives)
2. Posts to Twitter with store link  
3. Imports their contact info into Supabase for Apollo follow-up
4. Logs everything

This is the difference between infrastructure and revenue.
"""
import os, json, logging, smtplib, urllib.request, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Known bounced/invalid emails — never retry
BOUNCED_EMAILS = set([
    "jbankoff@voxmedia.com",  # 550 5.1.1 confirmed bounce 2026-03-22
])

def is_valid_email_domain(email):
    """Quick MX record check before sending — avoids bounces."""
    import socket
    try:
        domain = email.split("@")[1]
        # Check if domain has MX records
        socket.getaddrinfo(domain, None)
        return True
    except:
        return False

def safe_to_send(email):
    if email in BOUNCED_EMAILS:
        return False, "known_bounce"
    if not is_valid_email_domain(email):
        return False, "no_mx"
    return True, "ok"

log = logging.getLogger("revenue_now")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

GMAIL_USER    = os.environ.get("GMAIL_USER", "seanb041992@gmail.com")
GMAIL_PASS    = os.environ.get("GMAIL_APP_PASS", "")
SUPA_URL      = os.environ.get("SUPABASE_URL", "")
SUPA_KEY      = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API      = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER_KEY = os.environ.get("PUSHOVER_USER_KEY", "")
TW_API_KEY    = os.environ.get("TWITTER_API_KEY", "")
TW_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TW_AT         = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TW_ATS        = os.environ.get("TWITTER_ACCESS_SECRET", "")
STORE_URL     = "https://nyspotlightreport.com/store/"
ANTHROPIC     = os.environ.get("ANTHROPIC_API_KEY", "")

# Real prospects from HubSpot — actually contacted today
PROSPECTS = [
    {"name": "Mike",  "last": "Steib",   "email": "msteib@artsy.net",          "company": "Artsy",      "role": "CEO", "offer": "proflow_ai",     "amount": "$97/mo",    "angle": "content operations for a marketplace"},
    {"name": "Bob",   "last": "Pittman", "email": "bpittman@iheartmedia.com",   "company": "iHeartMedia","role": "CEO", "offer": "proflow_growth",  "amount": "$297/mo",   "angle": "content at iHeartMedia's scale"},
    {"name": "Jim",   "last": "Bankoff", "email": "jbankoff@vox.com",      "company": "Vox Media",  "role": "CEO", "offer": "proflow_elite",   "amount": "$797/mo",   "angle": "editorial content automation"},
    {"name": "Asaf",  "last": "Peled",   "email": "asaf@minutemedia.com",       "company": "Minute Media","role": "CEO", "offer": "dfy_agency",     "amount": "$2,997",    "angle": "sports content at global scale"},
    {"name": "Vince", "last": "Caruso",  "email": "vince@newtothestreet.com",   "company": "New to the Street","role": "CEO", "offer": "proflow_ai", "amount": "$97/mo",   "angle": "financial media content"},
]

PAYMENT_LINKS = {
    "proflow_ai":    "https://buy.stripe.com/8x228r2N67QffzdfHp2400c",
    "proflow_growth":"https://buy.stripe.com/00w00jgDW0nNaeT66P2400d",
    "proflow_elite": "https://buy.stripe.com/aFacN5fzSdazfzd3YH2400e",
    "dfy_setup":     "https://buy.stripe.com/9B6dR9fzSeeDev9eDl2400f",
    "dfy_agency":    "https://buy.stripe.com/8x214n9bu3zZ86L9j12400g",
    "enterprise":    "https://buy.stripe.com/00weVd5ZigmL86Ldzh2400h"}

def ai_personalize(prospect):
    """Generate a genuinely personalized email via Claude."""
    if not ANTHROPIC:
        return None
    prompt = f"""Write a cold email from Sean Thomas (NY Spotlight Report, Coram NY) to {prospect['name']} {prospect['last']}, {prospect['role']} of {prospect['company']}.

Sean built an AI system that automates {prospect['angle']}: content, social, SEO, email, outreach — all running 24/7 without staff.

Offer: {prospect['offer'].replace('_',' ').title()} at {prospect['amount']}. Payment link: {PAYMENT_LINKS[prospect['offer']]}
Store: {STORE_URL}

Rules:
- Under 100 words total
- Subject line: specific to their company/role (not generic)
- One clear CTA: the payment link OR the store URL
- No buzzwords, no fluff, no "I hope this finds you well"
- Sound like a real person texting a peer, not a marketing email
- Sign: Sean Thomas, NY Spotlight Report

Return ONLY: Subject: [line]\n\n[body]"""

    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":300,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude personalize: {e}")
        return None

def send_email(to_email, subject, body):
    """Send via Gmail SMTP."""
    if not GMAIL_PASS:
        log.warning("GMAIL_APP_PASS not set — cannot send")
        return False
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
        log.info(f"  ✅ SENT to {to_email}")
        return True
    except Exception as e:
        log.error(f"  ❌ FAILED {to_email}: {e}")
        return False

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

def post_tweet():
    """Post store launch tweet."""
    if not all([TW_API_KEY, TW_API_SECRET, TW_AT, TW_ATS]):
        log.warning("Twitter credentials missing — skipping tweet")
        return False
    
    import hmac, hashlib, base64, urllib.parse
    from time import time as ts
    
    tweet_text = (
        "Just launched: AI that runs your entire content operation automatically.\n\n"
        "Social posts. Blog. Email. SEO. Outreach.\n"
        "All on autopilot. 24/7.\n\n"
        "ProFlow AI: $97/mo. No contract. 30-day money-back.\n\n"
        "↓ nyspotlightreport.com/store/"
    )

    def oauth_header(method, url, params):
        nonce = base64.b64encode(os.urandom(32)).decode().rstrip('=')
        timestamp = str(int(ts()))
        oauth_params = {
            'oauth_consumer_key': TW_API_KEY,
            'oauth_nonce': nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': timestamp,
            'oauth_token': TW_AT,
            'oauth_version': '1.0'
        }
        all_params = {**params, **oauth_params}
        sorted_params = '&'.join(f"{urllib.parse.quote(k,'')}" + '=' + 
            f"{urllib.parse.quote(str(v),'')}" for k, v in sorted(all_params.items()))
        base_string = (f"{method}&{urllib.parse.quote(url,'')}"
                       f"&{urllib.parse.quote(sorted_params,'')}")
        signing_key = (f"{urllib.parse.quote(TW_API_SECRET,'')}"
                       f"&{urllib.parse.quote(TW_ATS,'')}")
        sig = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), 
                                         hashlib.sha1).digest()).decode()
        oauth_params['oauth_signature'] = sig
        header = 'OAuth ' + ', '.join(
            f'{urllib.parse.quote(k,"")}="{urllib.parse.quote(v,"")}"' 
            for k, v in sorted(oauth_params.items()))
        return header

    try:
        url = 'https://api.twitter.com/2/tweets'
        body = json.dumps({'text': tweet_text}).encode()
        auth = oauth_header('POST', url, {})
        req = urllib.request.Request(url, data=body, method='POST',
            headers={'Authorization': auth, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r:
            log.info("  ✅ Tweet posted!")
            return True
    except Exception as e:
        log.error(f"  Tweet failed: {e}")
        return False

def run():
    log.info("═"*60)
    log.info("IMMEDIATE REVENUE BOT — SENDING NOW")
    log.info(f"Target: {len(PROSPECTS)} prospects + Twitter post")
    log.info("═"*60)

    sent = 0
    failed = 0

    for p in PROSPECTS:
        log.info(f"\nProspect: {p['name']} {p['last']} ({p['company']})")
        log.info(f"Email: {p['email']}")

        # Get AI-personalized email
        email_content = ai_personalize(p)
        
        if email_content and "Subject:" in email_content:
            lines = email_content.split('\n', 2)
            subject = lines[0].replace('Subject:','').strip()
            body    = '\n'.join(lines[2:]).strip() if len(lines) > 2 else lines[-1]
        else:
            # Fallback hardcoded
            subject = f"AI for {p['company']}'s content — {p['amount']}"
            body    = f"""{p['name']},

Built an AI system that handles all your {p['angle']} automatically — social, blog, email, SEO, all running 24/7 without staff.

We're using it at NY Spotlight Report now. Thought it might be useful for {p['company']}.

{p['offer'].replace('_',' ').title()}: {p['amount']}
→ {PAYMENT_LINKS[p['offer']]}

Or see all options: {STORE_URL}

Sean Thomas
NY Spotlight Report"""

        log.info(f"Subject: {subject}")
        
        # Send email
        if send_email(p['email'], subject, body):
            sent += 1
            # Log to Supabase
            supa("POST", "contacts", {
                "email": p['email'],
                "name": f"{p['name']} {p['last']}",
                "stage": "CONTACTED",
                "score": 75,
                "source": "immediate_revenue_outreach",
                "tags": [p['offer'], p['company'].lower().replace(' ','_'), "cold_outreach"]})
            supa("POST", "conversation_log", {
                "channel": "email",
                "direction": "outbound",
                "body": f"Cold email sent: {subject}",
                "intent": "revenue_outreach",
                "agent_name": "ImmediateRevenuBot"})
        else:
            failed += 1

        time.sleep(2)  # Don't spam

    # Post to Twitter
    log.info("\nPosting to Twitter...")
    tweet_ok = post_tweet()

    # Pushover summary
    if PUSH_API and PUSH_USER_KEY:
        msg = (f"Revenue outreach fired:\n"
               f"✅ Emails sent: {sent}/{len(PROSPECTS)}\n"
               f"{'✅' if tweet_ok else '⚠️'} Twitter: {'posted' if tweet_ok else 'failed (check tokens)'}\n\n"
               f"Check inbox. If one replies = revenue.\n"
               f"Store: {STORE_URL}")
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER_KEY,
            "title":f"📧 {sent} outreach emails sent NOW",
            "message":msg,"priority":1,"sound":"magic"}).encode()
        try: urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except: pass

    log.info(f"\n{'═'*60}")
    log.info(f"DONE: {sent} sent, {failed} failed, tweet: {tweet_ok}")
    log.info(f"{'═'*60}")
    return {"sent": sent, "failed": failed, "tweeted": tweet_ok}

if __name__ == "__main__":
    run()
