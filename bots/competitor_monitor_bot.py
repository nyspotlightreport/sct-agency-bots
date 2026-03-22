#!/usr/bin/env python3
"""
COMPETITOR MONITOR BOT — S.C. Thomas Internal Agency
Tracks competitor websites for: new content, pricing changes, new offers, positioning shifts
Runs weekly → emails Chairman with changes + opportunities
Usage: python competitor_monitor_bot.py
Deploy: GitHub Actions every Sunday night
"""

import os
import json
import hashlib
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
STATE_FILE        = Path("competitor_state.json")

# ─── ADD YOUR COMPETITORS HERE ────────────────────────────────────────────────
COMPETITORS = [
    # {"name": "CompetitorName", "url": "https://competitor.com", "check_pages": ["/pricing", "/blog"]},
    # {"name": "Competitor2",    "url": "https://competitor2.com", "check_pages": ["/"]},
]
# ─────────────────────────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def fetch_page(url):
    try:
        r = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MonitorBot/1.0)"
        })
        return r.text[:50000]  # Cap at 50k chars
    except Exception as e:
        return f"ERROR: {e}"

def hash_content(content):
    return hashlib.md5(content.encode()).hexdigest()

def analyze_change_with_claude(competitor_name, url, old_content, new_content):
    """Ask Claude what changed and what it means strategically"""
    if not ANTHROPIC_API_KEY:
        return "Changes detected — API key needed for analysis"

    system = """You are a competitive intelligence analyst for S.C. Thomas.
Analyze what changed on a competitor's page and what it means strategically.
Be specific about: new offers, pricing changes, positioning shifts, new content, new features.
Keep response under 200 words. Focus on actionable intelligence."""

    prompt = f"""Competitor: {competitor_name}
URL: {url}

BEFORE (excerpt):
{old_content[:2000]}

AFTER (excerpt):
{new_content[:2000]}

What changed? What does it mean for us? What should Chairman do in response?"""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        return r.json()["content"][0]["text"]
    except Exception as e:
        return f"Analysis failed: {e}"

def run():
    print(f"[competitor-monitor] Starting {datetime.now()}")
    
    if not COMPETITORS:
        print("[competitor-monitor] No competitors configured. Add them to COMPETITORS list.")
        return

    state   = load_state()
    changes = []

    for comp in COMPETITORS:
        name = comp["name"]
        pages_to_check = [comp["url"]] + [comp["url"].rstrip("/") + p for p in comp.get("check_pages", [])]
        
        for page_url in pages_to_check:
            print(f"  Checking: {name} — {page_url}")
            content  = fetch_page(page_url)
            new_hash = hash_content(content)
            state_key = f"{name}::{page_url}"
            old_data  = state.get(state_key, {})
            old_hash  = old_data.get("hash", "")

            if old_hash and old_hash != new_hash:
                print(f"  ⚡ CHANGE DETECTED: {name} — {page_url}")
                analysis = analyze_change_with_claude(name, page_url, old_data.get("content",""), content)
                changes.append({
                    "competitor": name,
                    "url":        page_url,
                    "analysis":   analysis,
                    "detected":   datetime.now().isoformat(),
                })

            state[state_key] = {"hash": new_hash, "content": content[:5000], "last_checked": datetime.now().isoformat()}

    save_state(state)
    print(f"[competitor-monitor] Done. {len(changes)} changes detected.")

    if changes:
        send_alert(changes)
    else:
        print("[competitor-monitor] No changes this week.")

    return changes

def send_alert(changes):
    items_html = ""
    for c in changes:
        items_html += f"""
<div style="background:#f9f9f9;border-left:4px solid #c62828;padding:12px 16px;margin-bottom:16px;">
  <strong>{c['competitor']}</strong><br>
  <a href="{c['url']}" style="color:#1565c0;font-size:13px;">{c['url']}</a><br><br>
  <span style="font-size:14px;">{c['analysis']}</span>
</div>"""

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<div style="background:#c62828;color:#fff;padding:20px 24px;">
  <h2 style="margin:0;">⚡ COMPETITOR ACTIVITY — {datetime.now().strftime('%b %d, %Y')}</h2>
  <p style="margin:4px 0 0;color:#ffcdd2;">{len(changes)} change(s) detected</p>
</div>
<div style="padding:24px;">{items_html}</div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ Competitor Activity Detected — {datetime.now().strftime('%b %d')}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = CHAIRMAN_EMAIL
    msg.attach(MIMEText(html, "html"))

    if not GMAIL_APP_PASS:
        print("[competitor-monitor] No Gmail password — printing alert instead")
        for c in changes:
            print(f"\n{c['competitor']}: {c['analysis']}")
        return

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, CHAIRMAN_EMAIL, msg.as_string())
        print(f"[competitor-monitor] Alert sent to {CHAIRMAN_EMAIL}")
    except Exception as e:
        print(f"[competitor-monitor] Email failed: {e}")

if __name__ == "__main__":
    run()

# ─── SETUP ────────────────────────────────────────────────────────────────────
# 1. pip install requests
# 2. Edit COMPETITORS list above with your actual competitors
# 3. Set env vars: ANTHROPIC_API_KEY, GMAIL_APP_PASS
# 4. Run once to initialize state: python competitor_monitor_bot.py
# 5. Deploy to GitHub Actions (weekly Sunday 11pm):
#    cron: '0 23 * * 0'
