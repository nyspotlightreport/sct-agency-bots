#!/usr/bin/env python3
"""
agents/priya_sharma_email_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Department: Email Intelligence
Head: Priya Sharma — Chief Email Intelligence Officer (CEIO)

Mission: Sean never opens a low-priority email again.
- Reads inbox every 15 minutes
- AI-classifies every email (Claude Haiku — fast + cheap)
- Executes automated actions: forward, archive, reply, unsubscribe
- REVENUE + URGENT → nysr.priority@gmail.com (Sean's clean inbox)
- Newsletters → killed automatically
- GitHub Actions failures → summarized, not spammed
- Daily digest to Pushover

Architecture:
  Gmail IMAP (GMAIL_APP_PASS) → Claude classification → Rules engine →
  Gmail SMTP (forward/reply) → Supabase log → Pushover alert
"""
import os, json, logging, imaplib, smtplib, email, re, hashlib, time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import urllib.request

log = logging.getLogger("priya")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PRIYA SHARMA] %(message)s")

# ── CREDENTIALS ──────────────────────────────────────────────
GMAIL_USER    = os.environ.get("GMAIL_USER", "seanb041992@gmail.com")
GMAIL_PASS    = os.environ.get("GMAIL_APP_PASS", "")
PRIORITY_INBOX= os.environ.get("PRIORITY_EMAIL", "seanb041992+priority@gmail.com")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL      = os.environ.get("SUPABASE_URL", "")
SUPA_KEY      = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API      = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER     = os.environ.get("PUSHOVER_USER_KEY", "")

# ── CLASSIFICATION CONFIG ─────────────────────────────────────
CATEGORIES = {
    "REVENUE":    {"priority": 95, "action": "forward+label", "sound": "cashregister"},
    "URGENT":     {"priority": 90, "action": "forward+label", "sound": "siren"},
    "LEGAL":      {"priority": 90, "action": "forward+label", "sound": "siren"},
    "IMPORTANT":  {"priority": 70, "action": "forward+label", "sound": "magic"},
    "CLIENT":     {"priority": 85, "action": "forward+label", "sound": "magic"},
    "PARTNER":    {"priority": 80, "action": "forward+label", "sound": "magic"},
    "NEWSLETTER": {"priority": 5,  "action": "archive+unsubscribe", "sound": None},
    "ROUTINE":    {"priority": 20, "action": "archive+label", "sound": None},
    "GITHUB":     {"priority": 15, "action": "archive_if_success", "sound": None},
    "SPAM":       {"priority": 1,  "action": "delete", "sound": None},
    "AUTO":       {"priority": 10, "action": "archive", "sound": None},
}

def decode_str(s):
    """Decode email header strings."""
    if not s: return ""
    parts = decode_header(s)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            decoded.append(str(part))
    return " ".join(decoded)

def get_body(msg):
    """Extract plain text body from email."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in disp:
                try:
                    body += part.get_payload(decode=True).decode('utf-8', errors='replace')
                except: pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except: pass
    return body[:2000]  # Cap at 2000 chars for Claude

def supa(method, table, data=None, query=""):
    """Supabase helper."""
    if not SUPA_URL: return None
    req = urllib.request.Request(
        f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None,
        method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read()
            return json.loads(b) if b else {}
    except Exception as e:
        log.debug(f"Supa {method} {table}: {e}")
        return None

def claude(prompt, max_tokens=300):
    """AI classification via Claude Haiku (fast + cheap)."""
    if not ANTHROPIC_KEY: return None
    data = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude API: {e}")
        return None

def classify_email(sender, subject, snippet, body):
    """Use Claude to classify email. Returns JSON with category + action + summary."""
    prompt = f"""You are Priya Sharma, Email Intelligence Officer for NY Spotlight Report.

Classify this email and return ONLY valid JSON. No other text.

EMAIL:
From: {sender}
Subject: {subject}
Body preview: {snippet or body[:300]}

Classify into exactly ONE category:
- REVENUE: payment received, new client inquiry, purchase, proposal request, partnership opportunity with money
- URGENT: legal threat, contract deadline, compliance, account suspension, time-sensitive business matter
- LEGAL: attorney, lawsuit, contract, terms, DMCA, cease and desist
- CLIENT: reply from existing client, client question, client complaint
- IMPORTANT: business-critical but not urgent (vendor, account, tax, bank)
- PARTNER: agency, collaboration, strategic partnership, affiliate
- NEWSLETTER: marketing email, newsletter, promotional, deal, sale
- GITHUB: GitHub notification, workflow run, CI/CD, pull request, issue
- ROUTINE: general info, low priority, confirmation, receipt under $20
- AUTO: automated system email, noreply, notification bot
- SPAM: unwanted solicitation, scam, irrelevant

Return JSON only:
{{"category":"REVENUE","priority":95,"summary":"One sentence. What is this email actually about.","reply_needed":false,"auto_reply":false,"unsubscribe":false}}"""

    result = claude(prompt, max_tokens=200)
    if not result:
        return {"category": "ROUTINE", "priority": 20, "summary": subject or "No subject", "reply_needed": False}

    try:
        # Strip any markdown
        result = result.strip().strip('`').strip()
        if result.startswith('json'): result = result[4:].strip()
        return json.loads(result)
    except:
        # Fallback: parse category from text
        for cat in CATEGORIES:
            if cat in result.upper():
                return {"category": cat, "priority": CATEGORIES[cat]["priority"],
                        "summary": subject, "reply_needed": False}
        return {"category": "ROUTINE", "priority": 20, "summary": subject, "reply_needed": False}

def send_email(to_addr, subject, body, from_addr=None, reply_to=None):
    """Send email via Gmail SMTP."""
    if not GMAIL_PASS:
        log.warning("GMAIL_APP_PASS not set — cannot send email")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = from_addr or GMAIL_USER
        msg['To']      = to_addr
        msg['Subject'] = subject
        if reply_to:
            msg['Reply-To'] = reply_to
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to_addr, msg.as_string())
        return True
    except Exception as e:
        log.error(f"SMTP error: {e}")
        return False

def forward_to_priority(original_from, subject, body, category, summary):
    """Forward high-priority email to Sean's clean inbox."""
    priority_subject = f"[{category}] {subject}"
    priority_body = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 PRIYA SHARMA — Email Intelligence
Category: {category}
From: {original_from}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI Summary: {summary}

━━ ORIGINAL EMAIL ━━━━━━━━━━━━━━━━
{body[:1500]}
"""
    return send_email(PRIORITY_INBOX, priority_subject, priority_body)

def pushover_alert(title, message, sound=None, priority=0):
    """Send Pushover notification to Sean."""
    if not PUSH_API or not PUSH_USER: return
    payload = {"token": PUSH_API, "user": PUSH_USER,
               "title": title, "message": message, "priority": priority}
    if sound: payload["sound"] = sound
    data = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.debug(f"Pushover: {e}")

def get_processed_ids():
    """Get set of already-processed Gmail IDs."""
    result = supa("GET", "email_inbox", query="?select=gmail_id&processed_at=not.is.null&limit=500")
    if result and isinstance(result, list):
        return {r["gmail_id"] for r in result}
    return set()

def process_inbox():
    """Main inbox processing loop."""
    if not GMAIL_PASS:
        log.error("GMAIL_APP_PASS not configured. Cannot access Gmail.")
        return {"processed": 0, "error": "credentials missing"}

    log.info("═" * 55)
    log.info("PRIYA SHARMA — Email Intelligence Agent")
    log.info(f"Connecting to Gmail: {GMAIL_USER}")
    log.info("═" * 55)

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('INBOX')
    except Exception as e:
        log.error(f"Gmail IMAP connection failed: {e}")
        return {"processed": 0, "error": str(e)}

    # Get recent unread emails (last 24 hours)
    since_date = (datetime.now() - timedelta(hours=24)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'(SINCE {since_date})')

    if status != 'OK' or not messages[0]:
        log.info("No new emails to process")
        mail.logout()
        return {"processed": 0}

    email_ids = messages[0].split()
    log.info(f"Found {len(email_ids)} emails in last 24h")

    processed_ids = get_processed_ids()
    stats = {
        "total": 0, "revenue": 0, "urgent": 0,
        "newsletters_killed": 0, "auto_archived": 0,
        "forwarded": 0, "leads": 0
    }

    github_failures = []
    revenue_alerts  = []
    urgent_alerts   = []

    for eid in email_ids[-50:]:  # Process up to 50 per run
        try:
            status, msg_data = mail.fetch(eid, '(RFC822)')
            if status != 'OK': continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # Extract fields
            gmail_msg_id = msg.get('Message-ID', str(eid.decode()))
            if gmail_msg_id in processed_ids:
                continue  # Already processed

            sender   = decode_str(msg.get('From', ''))
            subject  = decode_str(msg.get('Subject', '(no subject)'))
            date_str = msg.get('Date', '')
            body     = get_body(msg)
            snippet  = (body[:200] if body else subject[:200])

            # Extract clean sender email
            sender_email = re.search(r'<(.+?)>', sender)
            sender_email = sender_email.group(1) if sender_email else sender

            # Skip if we already processed this message ID
            short_id = hashlib.md5(gmail_msg_id.encode()).hexdigest()[:16]

            # ── CLASSIFY ─────────────────────────────────────
            t0 = time.time()
            classification = classify_email(sender, subject, snippet, body)
            elapsed_ms = int((time.time() - t0) * 1000)

            category    = classification.get("category", "ROUTINE")
            priority    = classification.get("priority", 20)
            summary     = classification.get("summary", subject)
            needs_reply = classification.get("auto_reply", False)
            unsubscribe = classification.get("unsubscribe", False)
            cat_config  = CATEGORIES.get(category, CATEGORIES["ROUTINE"])

            log.info(f"  [{category:12s}] {subject[:60]}")

            # ── EXECUTE ACTIONS ───────────────────────────────
            forwarded   = False
            archived    = False
            replied     = False
            unsubscribed= False
            action      = cat_config["action"]

            # FORWARD high-priority to clean inbox
            if "forward" in action and priority >= 70:
                forwarded = forward_to_priority(sender, subject, body, category, summary)
                if forwarded:
                    stats["forwarded"] += 1
                    log.info(f"    → Forwarded to {PRIORITY_INBOX}")

            # ARCHIVE newsletters, auto, github success, routine
            if "archive" in action:
                try:
                    # Mark as read + move to archive in Gmail
                    mail.store(eid, '+FLAGS', '\\Seen')
                    # Apply label via append — archive = remove from INBOX
                    mail.store(eid, '+FLAGS', '\\Deleted')
                    stats["auto_archived"] += 1
                    archived = True
                except: pass

            # UNSUBSCRIBE newsletters
            if "unsubscribe" in action or unsubscribe:
                unsub_link = None
                list_unsub = msg.get('List-Unsubscribe', '')
                if list_unsub:
                    mailto = re.search(r'mailto:(.+?)[\s>]', list_unsub)
                    if mailto:
                        # Send unsubscribe email
                        send_email(mailto.group(1), "Unsubscribe", "Unsubscribe")
                        unsubscribed = True
                        stats["newsletters_killed"] += 1

            # GITHUB: only forward failures
            if category == "GITHUB":
                if "failed" in subject.lower() or "failure" in subject.lower():
                    github_failures.append(f"• {subject[:80]}")
                archived = True

            # REVENUE: collect for single alert
            if category == "REVENUE":
                stats["revenue"] += 1
                revenue_alerts.append(f"• {sender_email}: {summary[:80]}")

            # URGENT/LEGAL: immediate Pushover
            if category in ["URGENT", "LEGAL"]:
                stats["urgent"] += 1
                urgent_alerts.append(summary)
                pushover_alert(
                    f"🚨 URGENT EMAIL: {category}",
                    f"From: {sender_email}\n{summary}",
                    sound="siren", priority=1
                )

            # AUTO-REPLY for lead inquiries
            if needs_reply and category in ["REVENUE", "CLIENT"] and sender_email:
                reply_body = f"""Hi there,

Thank you for your email! I've received your message and will be in touch within 24 hours.

In the meantime, feel free to explore our AI automation packages at:
https://nyspotlightreport.com/store/

Best,
Sean Thomas
NY Spotlight Report
"""
                if send_email(sender_email, f"Re: {subject}", reply_body):
                    replied = True
                    log.info(f"    → Auto-replied to {sender_email}")

            # ── SAVE TO SUPABASE ──────────────────────────────
            supa("POST", "email_inbox", {
                "gmail_id":         gmail_msg_id,
                "from_email":       sender_email,
                "from_name":        sender.split('<')[0].strip(),
                "subject":          subject[:500],
                "snippet":          snippet[:300],
                "category":         category,
                "priority_score":   priority,
                "ai_summary":       summary[:500],
                "ai_action":        action,
                "sentiment":        classification.get("sentiment", "neutral"),
                "forwarded":        forwarded,
                "forwarded_to":     PRIORITY_INBOX if forwarded else None,
                "archived":         archived,
                "replied":          replied,
                "unsubscribed":     unsubscribed,
                "processed_at":     datetime.utcnow().isoformat(),
                "processing_time_ms": elapsed_ms
            })

            stats["total"] += 1

        except Exception as e:
            log.warning(f"Error processing email {eid}: {e}")
            continue

    mail.logout()

    # ── BATCH NOTIFICATIONS ───────────────────────────────────
    # Revenue batch alert (one notification for all revenue emails)
    if revenue_alerts:
        pushover_alert(
            f"💰 {len(revenue_alerts)} Revenue Email(s)",
            "\n".join(revenue_alerts[:5]),
            sound="cashregister", priority=0
        )

    # GitHub failures batch
    if github_failures:
        pushover_alert(
            f"⚠️ {len(github_failures)} GitHub Failure(s)",
            "\n".join(github_failures[:5]),
            sound="none", priority=-1
        )

    # ── DAILY DIGEST LOG ─────────────────────────────────────
    supa("POST", "email_digest", {
        "digest_date":        datetime.utcnow().date().isoformat(),
        "period":             "auto",
        "total_emails":       stats["total"],
        "revenue_emails":     stats["revenue"],
        "urgent_emails":      stats["urgent"],
        "newsletters_killed": stats["newsletters_killed"],
        "auto_replies_sent":  stats.get("replied", 0),
        "pushover_sent":      True
    })

    log.info(f"\n{'═'*55}")
    log.info(f"PRIYA SHARMA — Run Complete")
    log.info(f"  Processed:   {stats['total']}")
    log.info(f"  Revenue:     {stats['revenue']}")
    log.info(f"  Urgent:      {stats['urgent']}")
    log.info(f"  Forwarded:   {stats['forwarded']} → {PRIORITY_INBOX}")
    log.info(f"  Killed:      {stats['newsletters_killed']} newsletters")
    log.info(f"  Archived:    {stats['auto_archived']} auto-emails")
    log.info(f"{'═'*55}")

    return stats

if __name__ == "__main__":
    process_inbox()
