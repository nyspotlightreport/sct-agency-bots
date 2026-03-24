#!/usr/bin/env python3
"""
MEETING NOTES PROCESSOR BOT — S.C. Thomas Internal Agency
Takes raw meeting notes or transcripts → extracts action items → creates tasks
→ sends summary email → optionally pushes to HubSpot or Google Calendar
Usage:
  python meeting_notes_bot.py --notes "paste meeting notes here"
  python meeting_notes_bot.py --file meeting_transcript.txt
  python meeting_notes_bot.py --granola  (pulls latest from Granola API if connected)
"""

import os
import json
import argparse
import requests
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GMAIL_USER        = os.getenv("GMAIL_USER", "nyspotlightreport@gmail.com")
GMAIL_APP_PASS    = os.getenv("GMAIL_APP_PASS", "")
CHAIRMAN_EMAIL    = os.getenv("CHAIRMAN_EMAIL", "nyspotlightreport@gmail.com")
HUBSPOT_API_KEY   = os.getenv("HUBSPOT_API_KEY", "")
OUTPUT_DIR        = Path("meeting_notes")
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── CLAUDE PROCESSOR ─────────────────────────────────────────────────────────
def process_notes(notes_text, meeting_title="Meeting"):
    if not ANTHROPIC_API_KEY:
        return _mock_output()

    system = """You are the executive assistant for S.C. Thomas (Chairman).
Process meeting notes and extract structured intelligence.
Be specific and actionable. Owners default to 'Chairman' unless another person is clearly assigned.
All deadlines default to 'ASAP' unless specifically mentioned."""

    prompt = f"""Process these meeting notes and return ONLY valid JSON:

MEETING NOTES:
{notes_text}

Return this exact JSON structure:
{{
  "meeting_title": "...",
  "date": "...",
  "attendees": ["..."],
  "summary": "2-3 sentence summary of what was discussed and decided",
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {{"task": "...", "owner": "...", "deadline": "...", "priority": "HIGH|MEDIUM|LOW", "context": "..."}}
  ],
  "follow_ups": ["..."],
  "open_questions": ["..."],
  "key_insights": ["..."],
  "next_meeting": "..."
}}"""

    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000, "system": system,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[meeting-bot] Claude error: {e}")
        return _mock_output()

def _mock_output():
    return {
        "meeting_title": "Meeting",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "attendees": [],
        "summary": "Meeting notes processed (no API key configured)",
        "decisions": [],
        "action_items": [{"task": "Configure ANTHROPIC_API_KEY", "owner": "Chairman", "deadline": "ASAP", "priority": "HIGH", "context": "Required for AI processing"}],
        "follow_ups": [],
        "open_questions": [],
        "key_insights": [],
        "next_meeting": ""
    }

# ─── HubSpot TASK CREATOR ──────────────────────────────────────────────────────
def create_hubspot_tasks(action_items):
    if not HUBSPOT_API_KEY: return 0
    headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}", "Content-Type": "application/json"}
    created = 0
    for item in action_items:
        try:
            r = requests.post(
                "https://api.hubapi.com/crm/v3/objects/tasks",
                headers=headers,
                json={"properties": {
                    "hs_task_subject": item["task"],
                    "hs_task_body":    item.get("context", ""),
                    "hs_task_status":  "NOT_STARTED",
                    "hs_task_priority": item.get("priority", "MEDIUM"),
                }},
                timeout=10
            )
            if r.status_code in [200, 201]: created += 1
        except Exception:  # noqa: bare-except

            pass
    print(f"[meeting-bot] Created {created} HubSpot tasks")
    return created

# ─── EMAIL REPORT ─────────────────────────────────────────────────────────────
def send_summary_email(data, original_notes):
    date_str = datetime.now().strftime("%B %d, %Y")
    title    = data.get("meeting_title", "Meeting")

    def _action_row(item):
        bg = 'background:#fff8e1' if item.get('priority') == 'HIGH' else ''
        icon = '🔴 ' if item.get('priority') == 'HIGH' else '🟡 ' if item.get('priority') == 'MEDIUM' else '⚪ '
        ctx = '<br><span style="color:#888;font-size:12px;">' + item.get('context', '') + '</span>' if item.get('context') else ''
        owner = item.get('owner', 'Chairman')
        deadline = item.get('deadline', 'ASAP')
        return (
            f'<tr style="{bg}">'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;">'
            f'{icon}<strong>{item["task"]}</strong>{ctx}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;white-space:nowrap;">{owner}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #eee;white-space:nowrap;">{deadline}</td>'
            f'</tr>'
        )
    action_rows = "".join([_action_row(item) for item in data.get("action_items", [])])

    decisions_html = "".join([f"<li>{d}</li>" for d in data.get("decisions", [])])
    insights_html  = "".join([f"<li>{i}</li>" for i in data.get("key_insights", [])])
    questions_html = "".join([f"<li>{q}</li>" for q in data.get("open_questions", [])])

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;color:#111;">
<div style="background:#111;color:#fff;padding:20px 24px;">
  <h2 style="margin:0;font-size:18px;">📋 MEETING SUMMARY — {date_str}</h2>
  <p style="margin:4px 0 0;color:#aaa;">{title}</p>
  {'<p style="margin:4px 0 0;color:#888;font-size:13px;">Attendees: ' + ', '.join(data.get('attendees',[])) + '</p>' if data.get('attendees') else ''}
</div>
<div style="padding:24px;">

  <div style="background:#f5f5f5;padding:16px;margin-bottom:24px;">
    <strong>SUMMARY</strong><br>
    <span style="color:#555;">{data.get('summary','')}</span>
  </div>

  {f'<h3 style="border-bottom:2px solid #111;padding-bottom:6px;">✅ DECISIONS MADE</h3><ul>' + decisions_html + '</ul>' if decisions_html else ''}

  <h3 style="border-bottom:2px solid #111;padding-bottom:6px;">⚡ ACTION ITEMS ({len(data.get('action_items',[]))} tasks)</h3>
  <table width="100%" style="border-collapse:collapse;">
    <thead><tr style="background:#111;color:#fff;">
      <th style="padding:8px 10px;text-align:left;">Task</th>
      <th style="padding:8px 10px;text-align:left;">Owner</th>
      <th style="padding:8px 10px;text-align:left;">Deadline</th>
    </tr></thead>
    <tbody>{action_rows}</tbody>
  </table>

  {f'<h3 style="margin-top:24px;border-bottom:2px solid #111;padding-bottom:6px;">💡 KEY INSIGHTS</h3><ul>' + insights_html + '</ul>' if insights_html else ''}
  {f'<h3 style="margin-top:24px;border-bottom:2px solid #111;padding-bottom:6px;">❓ OPEN QUESTIONS</h3><ul>' + questions_html + '</ul>' if questions_html else ''}
  {f'<div style="background:#e8f5e9;padding:12px 16px;margin-top:20px;"><strong>Next Meeting:</strong> {data.get("next_meeting")}</div>' if data.get("next_meeting") else ''}

  <p style="margin-top:24px;font-size:12px;color:#999;">Meeting Notes Bot | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📋 Meeting Summary — {title} — {date_str}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = CHAIRMAN_EMAIL
    msg.attach(MIMEText(html, "html"))

    if not GMAIL_APP_PASS:
        print("[meeting-bot] No email creds — summary:")
        print(f"  Actions: {len(data.get('action_items',[]))}")
        for a in data.get("action_items", []): print(f"    [{a.get('priority')}] {a['task']} → {a.get('owner')} by {a.get('deadline')}")
        return

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, CHAIRMAN_EMAIL, msg.as_string())
        print(f"[meeting-bot] Summary sent to {CHAIRMAN_EMAIL}")
    except Exception as e:
        print(f"[meeting-bot] Email failed: {e}")

def save_notes(data, original_notes):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = "".join(c for c in data.get("meeting_title","meeting")[:30] if c.isalnum() or c==" ").replace(" ","_")
    filepath = OUTPUT_DIR / f"{ts}_{title}.json"
    with open(filepath, "w") as f:
        json.dump({"processed": data, "original": original_notes}, f, indent=2)
    print(f"[meeting-bot] Saved: {filepath}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run(notes_text, meeting_title="Meeting"):
    print(f"[meeting-bot] Processing: {meeting_title[:50]}")
    data = process_notes(notes_text, meeting_title)

    print(f"[meeting-bot] Extracted {len(data.get('action_items',[]))} action items")
    save_notes(data, notes_text)

    if HUBSPOT_API_KEY:
        create_hubspot_tasks(data.get("action_items", []))

    send_summary_email(data, notes_text)
    return data

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--notes", type=str, help="Meeting notes text")
    p.add_argument("--file",  type=str, help="Path to notes file")
    p.add_argument("--title", type=str, default="Meeting")
    args = p.parse_args()

    if args.file:
        with open(args.file) as f: notes = f.read()
    elif args.notes:
        notes = args.notes
    else:
        notes = input("Paste meeting notes (Ctrl+D when done):\n")

    run(notes, args.title)

# SETUP: pip install requests
# Usage: python meeting_notes_bot.py --file transcript.txt --title "Client Call"
