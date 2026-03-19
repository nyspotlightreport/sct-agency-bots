#!/usr/bin/env python3
"""
AFFILIATE TRACKER BOT v1.0 — S.C. Thomas Internal Agency
Tracks affiliate links, clicks, conversions, and commissions.
Monitors top programs: Ahrefs, HubSpot, Shopify, Kinsta, etc.
Adds UTM parameters to all outbound links automatically.
Weekly revenue report from all affiliate programs.
"""
import os, sys, json, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, AlertSystem

# High-value affiliate programs to monitor
PROGRAMS = [
    {"name": "Ahrefs",    "commission": "$200/sale",   "url": "ahrefs.com/affiliates"},
    {"name": "HubSpot",   "commission": "up to $1000", "url": "hubspot.com/partners"},
    {"name": "Shopify",   "commission": "$150/referral","url": "shopify.com/affiliates"},
    {"name": "Kinsta",    "commission": "10% recurring","url": "kinsta.com/affiliates"},
    {"name": "WP Engine", "commission": "$200+/sale",  "url": "wpengine.com/affiliates"},
    {"name": "SEMrush",   "commission": "$200/sale",   "url": "semrush.com/affiliates"},
    {"name": "Anthropic", "commission": "check site",  "url": "anthropic.com"},
]

class AffiliateTrackerBot(BaseBot):
    VERSION = "1.0.0"

    def __init__(self):
        super().__init__("affiliate-tracker")

    def generate_utm_link(self, url: str, campaign: str, medium: str = "content") -> str:
        """Generate UTM-tracked affiliate link"""
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}utm_source=nyspotlightreport&utm_medium={medium}&utm_campaign={campaign}"

    def report_program_status(self) -> list:
        """Check status of all affiliate programs"""
        results = []
        for prog in PROGRAMS:
            results.append({
                "name":       prog["name"],
                "commission": prog["commission"],
                "signup_url": prog["url"],
                "status":     self.state.get(f"affiliate_{prog['name']}_status", "not_joined"),
                "earnings":   self.state.get(f"affiliate_{prog['name']}_earnings", 0.0),
            })
        return results

    def execute(self) -> dict:
        programs = self.report_program_status()
        joined   = [p for p in programs if p["status"] == "active"]
        pending  = [p for p in programs if p["status"] == "not_joined"]

        rows = "".join([f"""
<tr>
  <td>{p['name']}</td>
  <td>{p['commission']}</td>
  <td style="color:{'green' if p['status']=='active' else 'orange'}">{p['status'].upper()}</td>
  <td>${p['earnings']:,.2f}</td>
  <td><a href="https://{p['signup_url']}">{p['signup_url']}</a></td>
</tr>""" for p in programs])

        AlertSystem.send(
            subject  = f"🔗 Affiliate Status — {len(joined)} active | ${sum(p['earnings'] for p in programs):,.2f} earned",
            body_html= f"""
<h3>Affiliate Program Dashboard</h3>
<table border="1" cellpadding="6">
<tr><th>Program</th><th>Commission</th><th>Status</th><th>Earned</th><th>Link</th></tr>
{rows}
</table>
<h4>Programs to join (high value):</h4>
<ul>{''.join(f'<li><a href="https://{p["signup_url"]}">{p["name"]}</a> — {p["commission"]}</li>' for p in pending[:5])}</ul>""",
            severity = "INFO"
        )
        return {"active": len(joined), "pending": len(pending)}

if __name__ == "__main__":
    AffiliateTrackerBot().run()
# No secrets needed. Add earnings manually or via affiliate dashboard webhooks.
