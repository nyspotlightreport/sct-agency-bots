#!/usr/bin/env python3
"""
INBOX TRIAGE BOT — S.C. Thomas Internal Agency
Connects to Gmail → categorizes every unread email → drafts responses for important ones
→ flags hot leads/opportunities → summarizes to Chairman daily
Run: python inbox_triage_bot.py
Deploy: Cron or GitHub Actions (daily at 7am)
"""

import os
import json
import base64
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CHAIRMAN_EMAIL    = os.getenv("CHAIRMAN_EMAIL", "nyspotlightreport@gmail.com")
SCOPES            = ['https://www.googleapis.com/auth/gmail.modify']
MAX_EMAILS        = int(os.getenv("MAX_EMAILS", "30"))  # Process this many unread

CATEGORIES = {
    "HOT_LEAD":      "🔥 HOT — Revenue opportunity, partnership offer, press inquiry",
    "NEEDS_REPLY":   "📨 REPLY — Requires a response from Chairman",
    "FYI":           "📋 FYI — Informational, no action needed",
    "NEWSLETTER":    "📰 NEWSLETTER — Marketing email, can archive",
    "SPAM":          "🗑️ SPAM — Junk, promotional, ignore",
    "FOLLOW_UP":     "⏰ FOLLOW-UP — Someone following up on prior conversation",
    "INVOICE":       "💰 INVOICE — Payment, billing, financial",
}

# ─── GMAIL AUTH ───────────────────────────────────────────────────────────────

def get_gmail_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# ─── EMAIL PROCESSOR ──────────────────────────────────────────────────────────

def get_email_body(msg):
    """Extract plain text body from email"""
    try:
        payload = msg['payload']
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')[:2000]
        elif payload.get('body', {}).get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')[:2000]
    except Exception:  # noqa: bare-except

        pass
    return ""

def extract_headers(msg):
    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
    return {
        'from':    headers.get('From', ''),
        'subject': headers.get('Subject', '(no subject)'),
        'date':    headers.get('Date', ''),
    }

# ─── CLAUDE CLASSIFIER ────────────────────────────────────────────────────────

def classify_and_draft(emails_batch):
    """Send batch of emails to Claude for classification + draft responses"""
    if not ANTHROPIC_API_KEY:
        return [{"category": "FYI", "priority": 3, "draft": None, "summary": "No API key"} for _ in emails_batch]

    batch_text = ""
    for i, email in enumerate(emails_batch):
        batch_text += f"""
EMAIL {i+1}:
From: {email['from']}
Subject: {email['subject']}
Body preview: {email['body'][:500]}
---
"""

    system = """You are the inbox manager for S.C. Thomas (Chairman of an internal agency).
Categorize each email and for HOT_LEAD and NEEDS_REPLY emails, draft a short response.

Categories: HOT_LEAD, NEEDS_REPLY, FYI, NEWSLETTER, SPAM, FOLLOW_UP, INVOICE

Return ONLY valid JSON array, one object per email:
[{
  "email_index": 1,
  "category": "CATEGORY",
  "priority": 1-5,
  "summary": "1 sentence summary",
  "action": "what Chairman should do",
  "draft_response": "draft reply text or null"
}]

Voice for draft responses: Direct, professional, brief. Sign as "Sean"."""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "system": system,
        "messages": [{"role": "user", "content": f"Classify these {len(emails_batch)} emails:\n{batch_text}"}]
    }

    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        text = r.json()["content"][0]["text"]
        # Strip markdown fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[inbox-bot] Claude error: {e}")
        return [{"email_index": i+1, "category": "FYI", "priority": 3, "summary": "Classification failed", "action": "Review manually", "draft_response": None} for i in range(len(emails_batch))]

# ─── DAILY DIGEST BUILDER ─────────────────────────────────────────────────────

def build_digest(categorized):
    hot     = [e for e in categorized if e.get('category') == 'HOT_LEAD']
    replies = [e for e in categorized if e.get('category') == 'NEEDS_REPLY']
    followup= [e for e in categorized if e.get('category') == 'FOLLOW_UP']
    invoice = [e for e in categorized if e.get('category') == 'INVOICE']

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#111;">
<div style="background:#111;color:#fff;padding:20px 24px;">
  <h2 style="margin:0;font-size:18px;">📬 INBOX TRIAGE — {datetime.now().strftime('%b %d, %Y')}</h2>
  <p style="margin:4px 0 0;color:#aaa;font-size:12px;">Processed {len(categorized)} emails | Action required: {len(hot)+len(replies)}</p>
</div>
<div style="padding:24px;">
"""

    if hot:
        html += "<h3 style='color:#c62828;border-bottom:2px solid #c62828;padding-bottom:6px;'>🔥 HOT — ACT NOW</h3>"
        for e in hot:
            html += f"""
<div style="background:#fff8f8;border-left:4px solid #c62828;padding:12px 16px;margin-bottom:12px;">
  <strong>{e.get('from','')}</strong><br>
  <em>{e.get('subject','')}</em><br>
  <span style="color:#555;font-size:13px;">{e.get('summary','')}</span><br>
  <span style="color:#c62828;font-size:12px;font-weight:bold;">→ {e.get('action','')}</span>
</div>"""

    if replies:
        html += "<h3 style='margin-top:24px;border-bottom:2px solid #111;padding-bottom:6px;'>📨 NEEDS REPLY</h3>"
        for e in replies:
            draft = e.get('draft_response','')
            html += f"""
<div style="background:#f9f9f9;border-left:4px solid #555;padding:12px 16px;margin-bottom:12px;">
  <strong>{e.get('from','')}</strong> — <em>{e.get('subject','')}</em><br>
  <span style="color:#555;font-size:13px;">{e.get('summary','')}</span>
  {'<br><br><strong>Draft response:</strong><br><span style="font-style:italic;color:#333;font-size:13px;">' + draft + '</span>' if draft else ''}
</div>"""

    if invoice:
        html += "<h3 style='margin-top:24px;border-bottom:2px solid #111;padding-bottom:6px;'>💰 INVOICES/BILLING</h3>"
        for e in invoice:
            html += f"<div style='padding:8px 0;border-bottom:1px solid #eee;'><strong>{e.get('from','')}</strong> — {e.get('summary','')}</div>"

    html += f"""
  <p style="margin-top:24px;font-size:12px;color:#999;">
    Auto-generated by Inbox Triage Bot | {datetime.now().strftime('%Y-%m-%d %H:%M ET')}
  </p>
</div></body></html>"""
    return html

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run():
    print(f"[inbox-triage-bot] Starting {datetime.now()}")

    try:
        service = get_gmail_service()
    except Exception as e:
        print(f"[inbox-triage-bot] Gmail auth failed: {e}")
        print("Run once locally to authenticate, then deploy token.pickle")
        return

    # Fetch unread emails
    results = service.users().messages().list(
        userId='me', q='is:unread', maxResults=MAX_EMAILS
    ).execute()
    message_ids = [m['id'] for m in results.get('messages', [])]
    print(f"[inbox-triage-bot] Found {len(message_ids)} unread emails")

    emails = []
    for mid in message_ids:
        msg = service.users().messages().get(userId='me', id=mid, format='full').execute()
        h = extract_headers(msg)
        emails.append({
            'id': mid,
            'from': h['from'],
            'subject': h['subject'],
            'date': h['date'],
            'body': get_email_body(msg)
        })

    # Classify in batches of 10
    categorized = []
    for i in range(0, len(emails), 10):
        batch = emails[i:i+10]
        results = classify_and_draft(batch)
        for j, result in enumerate(results):
            if i+j < len(emails):
                merged = {**emails[i+j], **result}
                categorized.append(merged)
        print(f"[inbox-triage-bot] Classified {min(i+10, len(emails))}/{len(emails)}")

    # Print summary
    from collections import Counter
    cats = Counter(e.get('category') for e in categorized)
    print(f"[inbox-triage-bot] Results: {dict(cats)}")

    # Save JSON results
    with open(f"inbox_triage_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(categorized, f, indent=2)

    print("[inbox-triage-bot] Done. Results saved.")
    return categorized

if __name__ == "__main__":
    run()

# ─── SETUP ────────────────────────────────────────────────────────────────────
# 1. pip install google-auth google-auth-oauthlib google-api-python-client requests
# 2. Create Gmail OAuth credentials at console.cloud.google.com
# 3. Save as credentials.json in same directory
# 4. Run once locally: python inbox_triage_bot.py  (browser auth popup)
# 5. token.pickle is saved — deploy this with the script
# 6. Set ANTHROPIC_API_KEY env var
