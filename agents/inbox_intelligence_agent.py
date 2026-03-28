#!/usr/bin/env python3
"""
agents/inbox_intelligence_agent.py — Inbox Intelligence Agent
Monitors Gmail inbox for press inquiries, partnership requests,
customer leads, and other actionable emails. Logs to Supabase
and sends Pushover alerts for high-priority items.
"""
import os, json, imaplib, email, logging
from email.header import decode_header
from datetime import datetime, timezone
import urllib.request as urlreq
import urllib.parse

log = logging.getLogger("inbox_intel")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INBOX] %(message)s")

# AG-NUCLEAR-GMAIL-ZERO-20260328: GMAIL_USER = os.environ.get("GMAIL_USER", "")
# AG-NUCLEAR-GMAIL-ZERO-20260328: GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_TOKEN = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")

PRESS_KEYWORDS = ["press release", "media inquiry", "journalist", "editorial", "story tip", "coverage request"]
PARTNER_KEYWORDS = ["partnership", "collaboration", "sponsor", "affiliate", "joint venture", "co-marketing"]
LEAD_KEYWORDS = ["pricing", "quote", "interested in", "demo", "consultation", "service", "how much"]
SPAM_KEYWORDS = ["unsubscribe", "opt out", "no-reply", "noreply", "mailer-daemon"]


def send_pushover(title, message, priority=0):
    """Send push notification via Pushover"""
    if not PUSH_TOKEN or not PUSH_USER:
        log.warning("Pushover credentials not set")
        return
    try:
        data = urllib.parse.urlencode({
            "token": PUSH_TOKEN, "user": PUSH_USER,
            "title": title, "message": message[:500],
            "priority": priority
        }).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json", data=data), timeout=10)
        log.info("Pushover alert sent: %s", title)
    except Exception as e:
        log.error("Pushover failed: %s", e)


def log_to_supabase(table, data):
    """Insert row into Supabase table"""
    if not SUPA_URL:
        log.warning("Supabase URL not set — skipping log")
        return
    try:
        payload = json.dumps(data).encode()
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/{table}",
            data=payload,
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            method="POST"
        )
        urlreq.urlopen(req, timeout=10)
        log.info("Logged to Supabase %s", table)
    except Exception as e:
        log.warning("Supabase insert to %s failed: %s", table, e)


def decode_subject(msg):
    """Decode email subject handling encoded headers"""
    raw = msg.get("Subject", "")
    decoded_parts = decode_header(raw)
    parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return " ".join(parts)


def categorize_email(subject, sender, body_preview):
    """Categorize email by content analysis"""
    combined = f"{subject} {sender} {body_preview}".lower()
    if any(kw in combined for kw in SPAM_KEYWORDS):
        return "spam"
    if any(kw in combined for kw in PRESS_KEYWORDS):
        return "press"
    if any(kw in combined for kw in PARTNER_KEYWORDS):
        return "partnership"
    if any(kw in combined for kw in LEAD_KEYWORDS):
        return "lead"
    return "general"


def get_body_preview(msg, max_chars=300):
    """Extract plain text body preview from email"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception as _silent_e:
                    import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception as _silent_e:
            import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)
    return body[:max_chars].replace("\n", " ").strip()


def check_inbox():
    """Connect to Gmail IMAP, read unseen emails, categorize, log, and alert"""
# AG-NUCLEAR-GMAIL-ZERO-20260328:     if not GMAIL_USER or not GMAIL_APP_PASS:
        log.error("Gmail credentials not set")
        return

    log.info("Connecting to Gmail IMAP...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
# AG-NUCLEAR-GMAIL-ZERO-20260328:         mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("INBOX")
    except Exception as e:
        log.error("IMAP connection failed: %s", e)
        return

    _, msg_ids = mail.search(None, "UNSEEN")
    ids = msg_ids[0].split()
    log.info("Found %d unseen emails", len(ids))

    stats = {"press": 0, "partnership": 0, "lead": 0, "general": 0, "spam": 0}

    for msg_id in ids[:50]:  # Process max 50 per run
        try:
            _, data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            subject = decode_subject(msg)
            sender = msg.get("From", "unknown")
            body_preview = get_body_preview(msg)
            category = categorize_email(subject, sender, body_preview)
            stats[category] = stats.get(category, 0) + 1

            if category == "spam":
                continue

            log.info("[%s] From: %s | Subject: %s", category.upper(), sender, subject[:80])

            # Log to Supabase
            record = {
                "sender_email": sender[:200],
                "subject": subject[:300],
                "category": category,
                "body_preview": body_preview[:500],
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

            if category == "press":
                log_to_supabase("brand_mentions", {
                    "source": "email", "mention_text": subject,
                    "url": sender, "created_at": datetime.now(timezone.utc).isoformat()
                })
                send_pushover("📰 Press Inquiry", f"From: {sender}\n{subject}", priority=1)

            elif category == "partnership":
                log_to_supabase("contacts", {
                    "email": sender, "full_name": sender.split("<")[0].strip(),
                    "source": "partnership_email", "nurture_stage": "new",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                send_pushover("🤝 Partnership Request", f"From: {sender}\n{subject}", priority=1)

            elif category == "lead":
                log_to_supabase("contacts", {
                    "email": sender, "full_name": sender.split("<")[0].strip(),
                    "source": "inbound_email", "nurture_stage": "new",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                send_pushover("💰 New Lead", f"From: {sender}\n{subject}")

        except Exception as e:
            log.warning("Failed to process email %s: %s", msg_id, e)

    mail.logout()
    log.info("Inbox scan complete: %s", json.dumps(stats))
    return stats


def main():
    log.info("=== Inbox Intelligence Agent starting ===")
    stats = check_inbox()
    if stats:
        total = sum(v for k, v in stats.items() if k != "spam")
        log.info("Processed %d actionable emails (skipped %d spam)", total, stats.get("spam", 0))
    log.info("=== Inbox Intelligence Agent complete ===")


if __name__ == "__main__":
    main()
