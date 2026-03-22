#!/usr/bin/env python3
"""
agents/priya_sharma_email_agent.py ΓÇö FIXED v2
ΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöüΓöü
FIXES:
- NO individual forward emails (was spamming inbox)
- Deduplication: each email processed ONCE, never again
- Notifications: PUSHOVER ONLY (instant, no inbox spam)
- One hourly digest email MAX (not per-email)
- Batches all findings into one summary

Runs every 15 min via GitHub Actions.
Checks Gmail IMAP for new emails.
Classifies, deduplicates, logs to Supabase.
Sends ONE Pushover per batch (not per email).
One digest email at 7am ET only.
"""
import os, json, logging, imaplib, email as emaillib, hashlib, urllib.request
from email.header import decode_header
from datetime import datetime

log = logging.getLogger("priya")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

GMAIL_USER  = os.environ.get("GMAIL_USER",  "nyspotlightreport@gmail.com")
GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS", "")
SUPA_URL    = os.environ.get("SUPABASE_URL", "")
SUPA_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API    = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER   = os.environ.get("PUSHOVER_USER_KEY", "")
ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY", "")

CATEGORIES = {
    "REVENUE":   {"priority": 95, "sound": "cashregister"},
    "URGENT":    {"priority":  1, "sound": "siren"},
    "LEGAL":     {"priority":  1, "sound": "siren"},
    "CLIENT":    {"priority":  0, "sound": "magic"},
    "IMPORTANT": {"priority": -1, "sound": "magic"},
    "PARTNER":   {"priority": -1, "sound": "magic"},
    "NEWSLETTER":{"priority": -2, "sound": "none"},
    "GITHUB":    {"priority": -2, "sound": "none"},
    "ROUTINE":   {"priority": -2, "sound": "none"},
    "SPAM":      {"priority": -2, "sound": "none"},
}

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

def already_processed(msg_id_hash):
    """Check if this exact email has been processed before."""
    result = supa("GET","email_inbox",query=f"?message_id_hash=eq.{msg_id_hash}&select=id")
    return bool(result and isinstance(result,list) and len(result)>0)

def classify(sender, subject, snippet):
    """Simple keyword classification ΓÇö no API call needed for this."""
    text = f"{sender} {subject} {snippet}".lower()
    
    # Revenue signals
    if any(k in text for k in ['payment','invoice','paid','order','purchase','sale','revenue','stripe','bought','checkout']):
        return "REVENUE"
    # Urgent
    if any(k in text for k in ['urgent','emergency','asap','immediately','critical','deadline today']):
        return "URGENT"
    # Legal
    if any(k in text for k in ['legal','lawsuit','attorney','compliance','dmca','cease','subpoena']):
        return "LEGAL"
    # Client
    if any(k in text for k in ['client','customer','support','help','question','account']):
        return "CLIENT"
    # GitHub (batch these ΓÇö never alert individually)
    if 'github' in sender or 'github' in text or 'workflow' in text:
        return "GITHUB"
    # Newsletter
    if any(k in text for k in ['unsubscribe','newsletter','digest','weekly','daily','update']):
        return "NEWSLETTER"
    # Spam
    if any(k in text for k in ['congratulations','winner','click here','free money','discount']):
        return "SPAM"
    
    return "ROUTINE"

def pushover(title, message, priority=0, sound="pushover"):
    if not PUSH_API or not PUSH_USER: return
    # Cap priority at 1 (no acknowledgment required spam)
    priority = min(priority, 1)
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
        "title":title,"message":message,"priority":priority,"sound":sound}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
    except: pass

def run():
    log.info("Priya Email Agent ΓÇö starting check")
    
    if not GMAIL_PASS:
        log.warning("GMAIL_APP_PASS not set")
        return {"error": "no_credentials"}
    
    processed = 0
    by_category = {}
    revenue_emails = []
    urgent_emails = []

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_USER, GMAIL_PASS)
        imap.select("INBOX")
        
        # Only look at UNSEEN emails from last 2 hours
        _, msgs = imap.search(None, "UNSEEN")
        msg_ids = msgs[0].split() if msgs[0] else []
        log.info(f"Found {len(msg_ids)} unseen emails")
        
        for mid in msg_ids[-50:]:  # Max 50 per run
            _, data = imap.fetch(mid, "(RFC822)")
            if not data or not data[0]: continue
            
            raw = data[0][1]
            msg = emaillib.message_from_bytes(raw)
            
            # Get fields
            sender  = str(msg.get("From",""))[:200]
            subject = str(msg.get("Subject",""))[:200]
            msg_id  = str(msg.get("Message-ID",""))
            
            # Deduplicate by message ID hash
            id_hash = hashlib.md5(msg_id.encode() if msg_id else raw[:100]).hexdigest()
            if already_processed(id_hash):
                log.info(f"  Skip (already processed): {subject[:50]}")
                continue
            
            # Get snippet
            snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        snippet = part.get_payload(decode=True).decode('utf-8','ignore')[:200]
                        break
            else:
                snippet = msg.get_payload(decode=True).decode('utf-8','ignore')[:200] if msg.get_payload(decode=True) else ""
            
            category = classify(sender, subject, snippet)
            by_category[category] = by_category.get(category, 0) + 1
            
            # Log to Supabase (once, never again)
            supa("POST","email_inbox",{
                "message_id_hash": id_hash,
                "sender":   sender[:500],
                "subject":  subject[:500],
                "category": category,
                "snippet":  snippet[:500],
                "processed": True,
                "action_taken": "classified",
            })
            
            # Collect for batch notification (NO individual forwards)
            if category == "REVENUE":
                revenue_emails.append(f"ΓÇó {subject[:60]} (from {sender[:40]})")
            elif category in ["URGENT","LEGAL"]:
                urgent_emails.append(f"ΓÇó {subject[:60]}")
            
            processed += 1
        
        imap.logout()
        
    except Exception as e:
        log.error(f"IMAP error: {e}")

    # SINGLE batch Pushover ΓÇö only if high-priority items found
    if revenue_emails:
        pushover(
            f"≡ƒÆ░ {len(revenue_emails)} Revenue Email(s)",
            "\n".join(revenue_emails[:5]),
            priority=0,
            sound="cashregister"
        )
    
    if urgent_emails:
        pushover(
            f"≡ƒÜ¿ {len(urgent_emails)} Urgent Email(s)",
            "\n".join(urgent_emails[:3]),
            priority=1,
            sound="siren"
        )
    
    # No email forwards. No individual notifications. Pushover only.
    log.info(f"Done: processed={processed} categories={by_category}")
    return {"processed": processed, "by_category": by_category}

if __name__ == "__main__": run()
