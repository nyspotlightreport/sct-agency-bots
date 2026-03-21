#!/usr/bin/env python3
"""
Inbox Intelligence Agent — NYSR Agency
Powered by Claude. Reads ALL inbound emails, qualifies leads,
and sends autonomous replies — no human needed.

What it handles:
- Replies to ProFlow AI/agency inquiries
- Qualifies leads and routes hot ones with phone notification
- Handles partnership inquiries
- Sends custom proposals
- Follows up on sales rep applications
- Responds to support questions
"""
import os, sys, json, logging, smtplib, imaplib, email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0,".")
from agents.claude_core import claude, claude_json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [InboxAgent] %(message)s")
log = logging.getLogger()

GMAIL_USER  = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
STRIPE_KEY  = os.environ.get("STRIPE_SECRET_KEY","")

REPLY_PERSONA = """You are S.C. Thomas, founder of NY Spotlight Report.
You respond to emails like a sharp, busy founder — fast, direct, helpful.
You never write long emails. You qualify first, then go deep if they're serious.
You're warm but efficient. No corporate speak. No over-promising."""

def read_unread_emails(limit=20) -> list:
    """Connect to Gmail IMAP and read unread emails."""
    if not GMAIL_PASS: return []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        _, data = mail.search(None, "UNSEEN")
        email_ids = data[0].split()[-limit:]
        emails = []
        for eid in email_ids:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8","ignore")[:2000]
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8","ignore")[:2000]
            emails.append({
                "id": eid.decode(),
                "from": msg["From"],
                "subject": msg["Subject"] or "",
                "body": body,
                "date": msg["Date"]
            })
        mail.logout()
        return emails
    except Exception as e:
        log.error(f"IMAP error: {e}")
        return []

def qualify_and_classify(email_data: dict) -> dict:
    """Use Claude to classify and score each email."""
    return claude_json(
        REPLY_PERSONA,
        f"""Classify and qualify this inbound email.

From: {email_data.get('from','')}
Subject: {email_data.get('subject','')}
Body: {email_data.get('body','')[:800]}

Classify this email and determine the right response.

Return JSON with:
- category: one of [proflow_inquiry, agency_inquiry, partnership, support, sales_rep_application, lemon_squeeze_review, spam, other]
- lead_score: 1-10 (10 = ready to buy right now)
- urgency: high/medium/low
- key_intent: what they actually want in one sentence
- recommended_action: reply/forward_to_sc/ignore/notify_chairman
- reply_tone: consultative/friendly/brief/formal
- hot_lead: true/false (true if score >= 7)""",
        max_tokens=400
    )

def write_reply(email_data: dict, classification: dict) -> str:
    """Write a personalized reply using Claude."""
    category   = classification.get("category","other")
    intent     = classification.get("key_intent","")
    tone       = classification.get("reply_tone","friendly")
    
    prompts = {
        "proflow_inquiry": f"""Write a reply to someone interested in ProFlow AI.
Their intent: {intent}
Tone: {tone}

Include:
- Acknowledge their specific situation
- 2-3 sentences on what ProFlow AI does for their use case
- Link to free plan: nyspotlightreport.com/free-plan/
- Offer a 15-min call if they want to see a demo
- Keep it under 100 words""",

        "agency_inquiry": f"""Write a reply to someone interested in our Done-For-You agency.
Their intent: {intent}
Tone: {tone}

Include:
- What we deliver (daily blog, newsletter, social) in 1-2 sentences
- Pricing starts at $997/month
- Offer to schedule a discovery call: calendly.com/nyspotlightreport
- 30-day results guarantee mention
- Under 120 words""",

        "partnership": f"""Write a reply to a potential partner.
Their proposal: {intent}
Tone: {tone}

- Be genuinely interested but concise
- Ask 1-2 qualifying questions to understand the fit
- Suggest a 20-min call
- Under 80 words""",

        "sales_rep_application": f"""Write a reply to someone who wants to be a sales rep.
Tone: friendly

- Welcome them
- Explain: 30% recurring commission, $97-1,997/month plans
- Tell them you'll send their affiliate link + materials
- Ask for their best method of outreach (LinkedIn, email, network)
- Under 100 words""",
    }
    
    prompt = prompts.get(category, f"""Write a brief, helpful reply to this email.
Intent: {intent}
Tone: {tone}
Keep under 80 words. Sign as S.C. Thomas, NY Spotlight Report.""")
    
    from_line = email_data.get("from","")
    first_name = from_line.split("<")[0].strip().split()[0] if "<" in from_line else "there"
    
    return claude(
        REPLY_PERSONA,
        f"The recipient is named {first_name}. " + prompt,
        max_tokens=300
    )

def send_reply(original: dict, reply_body: str) -> bool:
    if not GMAIL_PASS or not reply_body:
        log.info(f"[DRAFT REPLY] → {original.get('from','')}: {reply_body[:80]}")
        return True
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"S.C. Thomas <{GMAIL_USER}>"
        msg["To"]      = original["from"]
        msg["Subject"] = f"Re: {original.get('subject','')}"
        msg.attach(MIMEText(reply_body + "\n\n— S.C. Thomas\nNY Spotlight Report\nhttps://nyspotlightreport.com", "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        log.info(f"✅ Replied to: {original.get('from','')[:50]}")
        return True
    except Exception as e:
        log.error(f"Reply failed: {e}")
        return False

def notify_chairman(email_data: dict, classification: dict):
    """Send phone notification for hot leads."""
    if not PUSHOVER_KEY: return
    msg = f"🔥 HOT LEAD (score: {classification.get('lead_score',0)})
{email_data.get('from','')}
Intent: {classification.get('key_intent','')}"
    requests.post("https://api.pushover.net/1/messages.json",
        data={"token": PUSHOVER_KEY, "user": PUSHOVER_USER, "message": msg, "priority": 1},
        timeout=10)
    log.info(f"📱 Chairman notified: hot lead from {email_data.get('from','')}")

def run():
    log.info("Inbox Intelligence Agent starting...")
    emails = read_unread_emails(20)
    log.info(f"Unread emails to process: {len(emails)}")
    
    replied = hot_leads = 0
    for email_data in emails:
        subj = email_data.get("subject","")
        if not subj or "unsubscribe" in subj.lower(): continue
        
        # Classify with Claude
        classification = qualify_and_classify(email_data)
        if not classification: continue
        
        category = classification.get("category","other")
        score    = classification.get("lead_score",0)
        action   = classification.get("recommended_action","")
        
        log.info(f"Email: [{category}] score={score} | {subj[:50]}")
        
        # Notify chairman on hot leads
        if classification.get("hot_lead") or score >= 7:
            notify_chairman(email_data, classification)
            hot_leads += 1
        
        # Auto-reply for business inquiries
        if action == "reply" and category in ["proflow_inquiry","agency_inquiry",
                                               "partnership","sales_rep_application","support"]:
            reply = write_reply(email_data, classification)
            if reply:
                send_reply(email_data, reply)
                replied += 1
    
    log.info(f"Inbox Agent complete: {replied} replied | {hot_leads} hot leads flagged")

if __name__ == "__main__":
    run()
