#!/usr/bin/env python3
"""
WEEKLY REPORT BOT — S.C. Thomas Internal Agency
Runs every Monday 8am ET. Pulls KPIs from connected APIs, formats report, emails Chairman.
Deploy: GitHub Actions (see deploy instructions at bottom)
"""

import os
import json
import smtplib
import schedule
import time
import requests
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── CONFIG (set as environment variables) ───────────────────────────────────
GMAIL_USER       = os.getenv("GMAIL_USER", "seanb041992@gmail.com")
GMAIL_APP_PASS   = os.getenv("GMAIL_APP_PASS", "")        # Gmail App Password
CHAIRMAN_EMAIL   = os.getenv("CHAIRMAN_EMAIL", "seanb041992@gmail.com")
AHREFS_API_KEY   = os.getenv("AHREFS_API_KEY", "")
HUBSPOT_API_KEY  = os.getenv("HUBSPOT_API_KEY", "")
APOLLO_API_KEY   = os.getenv("APOLLO_API_KEY", "")
TARGET_DOMAIN    = os.getenv("TARGET_DOMAIN", "yourdomain.com")  # Update this
MONTHLY_REVENUE_TARGET = int(os.getenv("MONTHLY_REVENUE_TARGET", "10000"))

# ─── DATA PULLERS ─────────────────────────────────────────────────────────────

def pull_ahrefs_data():
    """Pull organic traffic + top keyword rankings"""
    if not AHREFS_API_KEY:
        return {"status": "no_key", "organic_traffic": "—", "top_keywords": []}
    try:
        headers = {"Authorization": f"Bearer {AHREFS_API_KEY}"}
        # Domain overview
        r = requests.get(
            "https://api.ahrefs.com/v3/site-explorer/metrics",
            params={"select": "org_traffic,org_keywords", "target": TARGET_DOMAIN, "mode": "domain"},
            headers=headers, timeout=10
        )
        data = r.json().get("metrics", {})
        return {
            "status": "ok",
            "organic_traffic": data.get("org_traffic", 0),
            "organic_keywords": data.get("org_keywords", 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def pull_hubspot_pipeline():
    """Pull open deals and pipeline value"""
    if not HUBSPOT_API_KEY:
        return {"status": "no_key", "open_deals": 0, "pipeline_value": 0}
    try:
        headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}"}
        r = requests.get(
            "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,closedate",
            headers=headers, timeout=10
        )
        deals = r.json().get("results", [])
        open_deals = [d for d in deals if d.get("properties", {}).get("dealstage") not in ["closedwon", "closedlost"]]
        pipeline_value = sum(float(d.get("properties", {}).get("amount") or 0) for d in open_deals)
        return {
            "status": "ok",
            "open_deals": len(open_deals),
            "pipeline_value": pipeline_value,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def pull_apollo_outreach():
    """Pull recent outreach activity"""
    if not APOLLO_API_KEY:
        return {"status": "no_key", "contacts_reached": 0, "reply_rate": "—"}
    try:
        headers = {"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"}
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        r = requests.post(
            "https://api.apollo.io/v1/emailer_campaigns/search",
            headers=headers,
            json={"page": 1, "per_page": 10},
            timeout=10
        )
        campaigns = r.json().get("emailer_campaigns", [])
        return {
            "status": "ok",
            "active_campaigns": len(campaigns),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ─── REPORT BUILDER ───────────────────────────────────────────────────────────

def build_report():
    now = datetime.now()
    week_str = now.strftime("%B %d, %Y")

    seo   = pull_ahrefs_data()
    pipe  = pull_hubspot_pipeline()
    reach = pull_apollo_outreach()

    def status_icon(val, good, warn):
        if isinstance(val, (int, float)):
            if val >= good: return "🟢"
            if val >= warn: return "🟡"
            return "🔴"
        return "⚪"

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#111;">
<div style="background:#111;color:#fff;padding:20px 24px;">
  <h2 style="margin:0;font-size:20px;">WEEKLY REPORT — {week_str}</h2>
  <p style="margin:4px 0 0;color:#aaa;font-size:13px;">S.C. Thomas Internal Agency | Automated by Drew Sinclair</p>
</div>
<div style="padding:24px;">

  <h3 style="border-bottom:2px solid #111;padding-bottom:8px;">📈 SEO & TRAFFIC</h3>
  <table width="100%" style="border-collapse:collapse;">
    <tr><td style="padding:8px 0;color:#555;width:60%;">Organic Traffic</td>
        <td style="padding:8px 0;font-weight:bold;">{seo.get('organic_traffic','—')}</td></tr>
    <tr><td style="padding:8px 0;color:#555;">Ranking Keywords</td>
        <td style="padding:8px 0;font-weight:bold;">{seo.get('organic_keywords','—')}</td></tr>
  </table>

  <h3 style="border-bottom:2px solid #111;padding-bottom:8px;margin-top:24px;">💰 PIPELINE</h3>
  <table width="100%" style="border-collapse:collapse;">
    <tr><td style="padding:8px 0;color:#555;">Open Deals</td>
        <td style="padding:8px 0;font-weight:bold;">{pipe.get('open_deals','—')}</td></tr>
    <tr><td style="padding:8px 0;color:#555;">Pipeline Value</td>
        <td style="padding:8px 0;font-weight:bold;">${pipe.get('pipeline_value',0):,.0f}</td></tr>
  </table>

  <h3 style="border-bottom:2px solid #111;padding-bottom:8px;margin-top:24px;">📨 OUTREACH</h3>
  <table width="100%" style="border-collapse:collapse;">
    <tr><td style="padding:8px 0;color:#555;">Active Campaigns</td>
        <td style="padding:8px 0;font-weight:bold;">{reach.get('active_campaigns','—')}</td></tr>
  </table>

  <div style="background:#f5f5f5;padding:16px;margin-top:24px;border-left:4px solid #111;">
    <strong>⚡ This Week's Priority Actions:</strong><br>
    <span style="color:#555;font-size:13px;">Review pipeline → Close or next-step each open deal<br>
    Check SEO ranking changes → Brief Cameron Reed on content gaps<br>
    Review outreach reply rate → Adjust sequences if below 15%</span>
  </div>

  <p style="margin-top:24px;font-size:12px;color:#999;">
    Auto-generated by Weekly Report Bot v1.0 | {now.strftime("%Y-%m-%d %H:%M ET")}
  </p>
</div>
</body></html>
"""
    return html

# ─── EMAIL SENDER ─────────────────────────────────────────────────────────────

def send_report():
    print(f"[weekly-report-bot] Building report {datetime.now()}")
    html = build_report()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ Weekly Report — {datetime.now().strftime('%b %d, %Y')}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = CHAIRMAN_EMAIL
    msg.attach(MIMEText(html, "html"))

    if not GMAIL_APP_PASS:
        print("[weekly-report-bot] No Gmail password set. Printing report instead:")
        print(html)
        return

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_USER, CHAIRMAN_EMAIL, msg.as_string())
        print(f"[weekly-report-bot] Report sent to {CHAIRMAN_EMAIL}")
    except Exception as e:
        print(f"[weekly-report-bot] Send failed: {e}")

# ─── SCHEDULER ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--now" in sys.argv:
        send_report()
    else:
        print("[weekly-report-bot] Scheduled for every Monday 8:00 AM ET")
        schedule.every().monday.at("08:00").do(send_report)
        while True:
            schedule.run_pending()
            time.sleep(60)

# ─── DEPLOY: GITHUB ACTIONS ───────────────────────────────────────────────────
# Create .github/workflows/weekly-report.yml with:
#
# name: Weekly Report
# on:
#   schedule:
#     - cron: '0 13 * * 1'  # Every Monday 1pm UTC = 8am ET
#   workflow_dispatch:        # Manual trigger
# jobs:
#   report:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v3
#       - uses: actions/setup-python@v4
#         with: {python-version: '3.11'}
#       - run: pip install schedule requests
#       - run: python weekly_report_bot.py --now
#         env:
#           GMAIL_USER: ${{ secrets.GMAIL_USER }}
#           GMAIL_APP_PASS: ${{ secrets.GMAIL_APP_PASS }}
#           AHREFS_API_KEY: ${{ secrets.AHREFS_API_KEY }}
#           HUBSPOT_API_KEY: ${{ secrets.HUBSPOT_API_KEY }}
#           TARGET_DOMAIN: ${{ secrets.TARGET_DOMAIN }}
