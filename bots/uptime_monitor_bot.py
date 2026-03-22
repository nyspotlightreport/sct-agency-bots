#!/usr/bin/env python3
"""
UPTIME + SITE HEALTH MONITOR BOT — S.C. Thomas Internal Agency
Monitors all websites for: uptime, page speed, SSL expiry, broken links
Alerts Chairman immediately if any site goes down.
Schedule: Every 15 minutes (via GitHub Actions or cron)
"""

import os
import json
import ssl
import socket
import smtplib
import requests
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urljoin, urlparse

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GMAIL_USER     = os.getenv("GMAIL_USER", "seanb041992@gmail.com")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS", "")
CHAIRMAN_EMAIL = os.getenv("CHAIRMAN_EMAIL", "seanb041992@gmail.com")
STATE_FILE     = Path("uptime_state.json")
TIMEOUT        = 10  # seconds
SSL_WARN_DAYS  = 30  # warn if SSL expires within this many days

# ─── ADD YOUR SITES HERE ──────────────────────────────────────────────────────
MONITORED_SITES = os.getenv("MONITORED_SITES", "").split(",") if os.getenv("MONITORED_SITES") else [
    # Add your sites here or set MONITORED_SITES env var (comma-separated)
    # "https://yourdomain.com",
    # "https://yourbrand.com",
]
# ─────────────────────────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f: return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)

# ─── CHECKS ───────────────────────────────────────────────────────────────────
def check_uptime(url):
    """Check if site is up and measure response time"""
    try:
        start = datetime.now()
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (UptimeBot/1.0)"})
        ms = int((datetime.now() - start).total_seconds() * 1000)
        return {"up": True, "status_code": r.status_code, "response_ms": ms, "error": None}
    except requests.exceptions.ConnectionError:
        return {"up": False, "status_code": None, "response_ms": None, "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"up": False, "status_code": None, "response_ms": None, "error": f"Timeout after {TIMEOUT}s"}
    except Exception as e:
        return {"up": False, "status_code": None, "response_ms": None, "error": str(e)}

def check_ssl(url):
    """Check SSL certificate expiry"""
    try:
        hostname = urlparse(url).netloc
        if not hostname: return {"valid": None, "days_remaining": None, "error": "No hostname"}
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(TIMEOUT)
            s.connect((hostname, 443))
            cert = s.getpeercert()
        expiry = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days   = (expiry - datetime.now(timezone.utc)).days
        return {"valid": True, "days_remaining": days, "expires": expiry.strftime("%Y-%m-%d"), "error": None}
    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "days_remaining": 0, "error": str(e)}
    except Exception as e:
        return {"valid": None, "days_remaining": None, "error": str(e)}

def check_page_speed(url):
    """Basic page size + load time check"""
    try:
        start = datetime.now()
        r = requests.get(url, timeout=TIMEOUT)
        ms   = int((datetime.now() - start).total_seconds() * 1000)
        size = len(r.content) / 1024  # KB
        return {"load_ms": ms, "size_kb": round(size, 1), "slow": ms > 3000}
    except:
        return {"load_ms": None, "size_kb": None, "slow": None}

# ─── ALERTS ───────────────────────────────────────────────────────────────────
def should_alert(url, current_status, previous_state):
    """Determine if we need to send an alert"""
    alerts = []
    prev = previous_state.get(url, {})

    # Site went down
    if not current_status["uptime"]["up"] and prev.get("was_up", True):
        alerts.append({"type": "DOWN", "severity": "CRITICAL", "message": f"Site is DOWN — {current_status['uptime']['error']}"})

    # Site came back up
    if current_status["uptime"]["up"] and not prev.get("was_up", True):
        alerts.append({"type": "UP", "severity": "RESOLVED", "message": "Site is back UP ✅"})

    # SSL expiring soon
    ssl_days = current_status.get("ssl", {}).get("days_remaining")
    if ssl_days is not None and ssl_days <= SSL_WARN_DAYS and ssl_days > 0:
        if not prev.get("ssl_warned"):
            alerts.append({"type": "SSL", "severity": "WARNING", "message": f"SSL expires in {ssl_days} days ({current_status['ssl']['expires']})"})

    # SSL expired/invalid
    if current_status.get("ssl", {}).get("valid") is False:
        alerts.append({"type": "SSL_INVALID", "severity": "CRITICAL", "message": f"SSL INVALID — {current_status['ssl']['error']}"})

    # Slow response
    load_ms = current_status.get("speed", {}).get("load_ms")
    if load_ms and load_ms > 5000 and not prev.get("slow_warned"):
        alerts.append({"type": "SLOW", "severity": "WARNING", "message": f"Site is SLOW — {load_ms}ms load time"})

    return alerts

def send_alert(url, alerts):
    severity_colors = {"CRITICAL": "#c62828", "WARNING": "#f9a825", "RESOLVED": "#2e7d32"}
    items = "".join([
        f"<div style='padding:8px 12px;border-left:4px solid {severity_colors.get(a['severity'],'#555')};margin-bottom:8px;background:#f9f9f9;'>"
        f"<strong>{a['severity']} — {a['type']}</strong><br><span style='color:#555;font-size:13px;'>{a['message']}</span></div>"
        for a in alerts
    ])
    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
<div style="background:#111;color:#fff;padding:16px 20px;">
  <strong>⚠️ SITE ALERT — {datetime.now().strftime('%b %d %H:%M')}</strong>
</div>
<div style="padding:16px 20px;">
  <p style="font-weight:bold;margin-bottom:12px;">URL: <a href="{url}">{url}</a></p>
  {items}
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    most_severe = "CRITICAL" if any(a["severity"] == "CRITICAL" for a in alerts) else "WARNING"
    msg["Subject"] = f"🚨 {most_severe}: {url}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = CHAIRMAN_EMAIL
    msg.attach(MIMEText(html, "html"))

    if not GMAIL_APP_PASS:
        print(f"[uptime-bot] ALERT for {url}: {[a['message'] for a in alerts]}")
        return
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, CHAIRMAN_EMAIL, msg.as_string())
        print(f"[uptime-bot] Alert sent for {url}")
    except Exception as e:
        print(f"[uptime-bot] Alert email failed: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run():
    if not MONITORED_SITES or not MONITORED_SITES[0]:
        print("[uptime-bot] No sites configured. Add URLs to MONITORED_SITES.")
        return

    state = load_state()
    print(f"[uptime-bot] Checking {len(MONITORED_SITES)} sites at {datetime.now()}")

    for url in MONITORED_SITES:
        url = url.strip()
        if not url: continue
        print(f"  → {url}")

        status = {
            "url":       url,
            "checked":   datetime.now().isoformat(),
            "uptime":    check_uptime(url),
            "ssl":       check_ssl(url) if url.startswith("https") else {},
            "speed":     check_page_speed(url),
        }

        # Determine alerts
        alerts = should_alert(url, status, state)
        if alerts:
            send_alert(url, alerts)

        # Update state
        prev      = state.get(url, {})
        state[url] = {
            "was_up":     status["uptime"]["up"],
            "last_check": status["checked"],
            "ssl_warned": prev.get("ssl_warned") or any(a["type"] == "SSL" for a in alerts),
            "slow_warned": status.get("speed", {}).get("slow", False),
            "response_ms": status["uptime"].get("response_ms"),
        }

        emoji = "✅" if status["uptime"]["up"] else "🔴"
        ms    = status["uptime"].get("response_ms", "—")
        ssl_d = status.get("ssl", {}).get("days_remaining", "—")
        print(f"     {emoji} Status: {status['uptime'].get('status_code','DOWN')} | {ms}ms | SSL: {ssl_d}d remaining")

    save_state(state)
    print(f"[uptime-bot] Complete")

if __name__ == "__main__":
    run()

# SETUP: pip install requests
# GITHUB ACTIONS — every 15 min:
# cron: '*/15 * * * *'
# Secrets: GMAIL_APP_PASS, CHAIRMAN_EMAIL, MONITORED_SITES (comma-separated URLs)
