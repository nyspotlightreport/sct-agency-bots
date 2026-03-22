#!/usr/bin/env python3
"""
WEEKLY REPORT BOT v2 — S.C. Thomas Internal Agency
Upgraded to use BaseBot with full retry, health tracking, and self-healing.
"""
import sys
import json
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, with_retry

class WeeklyReportBot(BaseBot):
    VERSION = "2.0.0"

    def __init__(self):
        super().__init__("weekly-report", required_config=["GMAIL_APP_PASS"])

    @with_retry(max_retries=3, delay=2.0)
    def pull_ahrefs(self) -> dict:
        if not Config.AHREFS_API_KEY or not Config.TARGET_DOMAIN:
            return {"status": "no_key", "org_traffic": "—", "org_keywords": "—", "domain_rating": "—"}
        r = self.http.get(
            "https://api.ahrefs.com/v3/site-explorer/metrics",
            params={"select": "org_traffic,org_keywords,domain_rating", "target": Config.TARGET_DOMAIN, "mode": "domain"},
            headers={"Authorization": f"Bearer {Config.AHREFS_API_KEY}"}
        )
        data = r.json().get("metrics", {})
        return {"status": "ok", **data}

    @with_retry(max_retries=3, delay=2.0)
    def pull_hubspot(self) -> dict:
        if not Config.HUBSPOT_API_KEY:
            return {"status": "no_key", "open_deals": "—", "pipeline_value": "—"}
        r = self.http.get(
            "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=amount,dealstage",
            headers={"Authorization": f"Bearer {Config.HUBSPOT_API_KEY}"}
        )
        deals  = r.json().get("results", [])
        open_d = [d for d in deals if d.get("properties", {}).get("dealstage") not in ["closedwon", "closedlost"]]
        value  = sum(float(d.get("properties", {}).get("amount") or 0) for d in open_d)
        return {"status": "ok", "open_deals": len(open_d), "pipeline_value": value}

    @with_retry(max_retries=3, delay=2.0)
    def pull_apollo(self) -> dict:
        if not Config.APOLLO_API_KEY:
            return {"status": "no_key", "active_sequences": "—"}
        r = self.http.post(
            "https://api.apollo.io/v1/emailer_campaigns/search",
            json_data={"page": 1, "per_page": 10},
            headers={"X-Api-Key": Config.APOLLO_API_KEY, "Content-Type": "application/json"}
        )
        campaigns = r.json().get("emailer_campaigns", [])
        return {"status": "ok", "active_sequences": len(campaigns)}

    def build_html(self, seo, hubspot, apollo) -> str:
        date_str = datetime.now().strftime("%B %d, %Y")
        def fmt(v): return f"${v:,.0f}" if isinstance(v, (int, float)) else str(v)
        return f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#111;">
<div style="background:#111;color:#fff;padding:20px 24px;">
  <h2 style="margin:0;font-size:20px;">⚡ WEEKLY REPORT — {date_str}</h2>
  <p style="margin:4px 0 0;color:#aaa;font-size:12px;">S.C. Thomas Internal Agency | Drew Sinclair</p>
</div>
<div style="padding:24px;">
  <h3 style="border-bottom:2px solid #111;padding-bottom:6px;">📈 SEO</h3>
  <table width="100%">
    <tr><td style="padding:6px 0;color:#555;">Domain Rating</td><td style="font-weight:bold;">{seo.get('domain_rating','—')}</td></tr>
    <tr><td style="padding:6px 0;color:#555;">Organic Traffic</td><td style="font-weight:bold;">{seo.get('org_traffic','—')}</td></tr>
    <tr><td style="padding:6px 0;color:#555;">Ranking Keywords</td><td style="font-weight:bold;">{seo.get('org_keywords','—')}</td></tr>
  </table>
  <h3 style="border-bottom:2px solid #111;padding-bottom:6px;margin-top:20px;">💰 PIPELINE</h3>
  <table width="100%">
    <tr><td style="padding:6px 0;color:#555;">Open Deals</td><td style="font-weight:bold;">{hubspot.get('open_deals','—')}</td></tr>
    <tr><td style="padding:6px 0;color:#555;">Pipeline Value</td><td style="font-weight:bold;">{fmt(hubspot.get('pipeline_value',0)) if hubspot.get('status')=='ok' else '—'}</td></tr>
  </table>
  <h3 style="border-bottom:2px solid #111;padding-bottom:6px;margin-top:20px;">📨 OUTREACH</h3>
  <table width="100%">
    <tr><td style="padding:6px 0;color:#555;">Active Sequences</td><td style="font-weight:bold;">{apollo.get('active_sequences','—')}</td></tr>
  </table>
  <p style="margin-top:24px;font-size:12px;color:#999;">Weekly Report Bot v{self.VERSION} | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>"""

    def send_email(self, html: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚡ Weekly Report — {datetime.now().strftime('%b %d, %Y')}"
        msg["From"]    = Config.GMAIL_USER
        msg["To"]      = Config.CHAIRMAN_EMAIL
        msg.attach(MIMEText(html, "html"))
        if not Config.GMAIL_APP_PASS:
            self.logger.info("No Gmail password — report built but not sent")
            return
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(Config.GMAIL_USER, Config.GMAIL_APP_PASS)
            s.sendmail(Config.GMAIL_USER, Config.CHAIRMAN_EMAIL, msg.as_string())
        self.logger.info(f"Report sent to {Config.CHAIRMAN_EMAIL}")

    def execute(self) -> dict:
        self.logger.info("Pulling data from all sources...")
        seo      = self.pull_ahrefs()
        hubspot  = self.pull_hubspot()
        apollo   = self.pull_apollo()
        html     = self.build_html(seo, hubspot, apollo)
        self.send_email(html)
        return {"items_processed": 1, "sources": ["ahrefs", "hubspot", "apollo"]}

if __name__ == "__main__":
    bot = WeeklyReportBot()
    bot.run()
