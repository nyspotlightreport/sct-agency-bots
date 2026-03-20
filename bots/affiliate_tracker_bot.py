#!/usr/bin/env python3
"""
AFFILIATE TRACKER BOT v2.0 — S.C. Thomas Internal Agency
Tracks all affiliate programs, generates UTM links, monitors earnings.
UPGRADED: Added Beehiiv, ElevenLabs, Jasper, Semrush, ConvertKit, Publer affiliates
"""
import os, sys, json, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem

PROGRAMS = [
    # HIGH VALUE ($100-$1000+ per sale)
    {"name":"HubSpot",       "commission":"up to $1000/sale", "recurring":False, "url":"https://www.hubspot.com/partners/affiliates", "tier":"TIER1", "category":"CRM"},
    {"name":"Ahrefs",        "commission":"$200/sale",        "recurring":False, "url":"https://ahrefs.com/affiliates", "tier":"TIER1", "category":"SEO"},
    {"name":"Shopify",       "commission":"$150/referral",    "recurring":False, "url":"https://www.shopify.com/affiliates", "tier":"TIER1", "category":"Ecommerce"},
    {"name":"WP Engine",     "commission":"$200+/sale",       "recurring":False, "url":"https://wpengine.com/affiliates", "tier":"TIER1", "category":"Hosting"},
    {"name":"Kinsta",        "commission":"10% recurring",    "recurring":True,  "url":"https://kinsta.com/affiliates", "tier":"TIER1", "category":"Hosting"},
    # MID VALUE ($50-$200 per sale)
    {"name":"Semrush",       "commission":"$200/sale",        "recurring":False, "url":"https://www.semrush.com/affiliates", "tier":"TIER2", "category":"SEO"},
    {"name":"ElevenLabs",    "commission":"22% recurring",    "recurring":True,  "url":"https://elevenlabs.io/affiliates", "tier":"TIER2", "category":"AI"},
    {"name":"Jasper AI",     "commission":"25% recurring",    "recurring":True,  "url":"https://www.jasper.ai/affiliates", "tier":"TIER2", "category":"AI"},
    {"name":"ConvertKit",    "commission":"30% recurring",    "recurring":True,  "url":"https://convertkit.com/referral", "tier":"TIER2", "category":"Email"},
    {"name":"Beehiiv",       "commission":"25% recurring",    "recurring":True,  "url":"https://www.beehiiv.com/affiliates", "tier":"TIER2", "category":"Newsletter"},
    {"name":"Publer",        "commission":"20% recurring",    "recurring":True,  "url":"https://publer.com/affiliates", "tier":"TIER2", "category":"Social"},
    # LOWER VALUE but easy wins
    {"name":"Canva",         "commission":"$36/subscriber",   "recurring":False, "url":"https://www.canva.com/affiliates", "tier":"TIER3", "category":"Design"},
    {"name":"Grammarly",     "commission":"$20/premium",      "recurring":False, "url":"https://www.grammarly.com/affiliates", "tier":"TIER3", "category":"Writing"},
    {"name":"Namecheap",     "commission":"35% first year",   "recurring":False, "url":"https://www.namecheap.com/affiliates", "tier":"TIER3", "category":"Domain"},
]

SITE_URL = "https://nyspotlightreport.com"

class AffiliateTrackerBot(BaseBot):
    VERSION = "2.0.0"

    def generate_affiliate_post(self, program):
        """Generate a content piece promoting an affiliate product"""
        system = "You are S.C. Thomas writing about tools for media professionals."
        prompt = f"""Write a 2-sentence recommendation for {program['name']} that a media executive would find valuable.
Commission: {program['commission']}. Category: {program['category']}.
Include a subtle CTA. No hashtags. Under 200 chars total."""
        return ClaudeClient.complete_safe(system=system, user=prompt, max_tokens=80,
                                          fallback=f"We use {program['name']} — check it out.")

    def get_utm_link(self, program):
        """Get tracking link with UTM params"""
        base = program["url"]
        params = urllib.parse.urlencode({
            "utm_source": "nyspotlightreport",
            "utm_medium": "affiliate",
            "utm_campaign": program["name"].lower().replace(" ","_")
        })
        return f"{base}?{params}" if "?" not in base else f"{base}&{params}"

    def execute(self):
        joined   = [p for p in PROGRAMS if self.state.get(f"affiliate_{p['name']}_status","not_joined") == "active"]
        pending  = [p for p in PROGRAMS if p not in joined]
        earnings = sum(self.state.get(f"affiliate_{p['name']}_earnings", 0.0) for p in PROGRAMS)

        # Build signup priority list
        tier1_pending = [p for p in pending if p["tier"]=="TIER1"]
        recurring_pending = [p for p in pending if p["recurring"] and p["tier"]!="TIER1"]

        rows = "".join([f"""<tr>
          <td><b>{p['name']}</b></td>
          <td>{p['commission']}</td>
          <td>{'♻️ Recurring' if p['recurring'] else 'One-time'}</td>
          <td>{p['tier']}</td>
          <td><a href='{p['url']}'>Sign Up</a></td>
        </tr>""" for p in (tier1_pending + recurring_pending)[:10]])

        AlertSystem.send(
            subject=f"💰 Affiliate Status: {len(joined)} active, {len(pending)} pending signup",
            body_html=f"""<h3>Affiliate Program Status</h3>
<p><b>Active:</b> {len(joined)} | <b>Total Earnings:</b> ${earnings:,.2f}</p>
<h4>Priority Signups (DO THESE FIRST):</h4>
<table border='1'><tr><th>Program</th><th>Commission</th><th>Type</th><th>Tier</th><th>Link</th></tr>
{rows}</table>
<p><i>Sign up for Tier 1 programs first — highest ROI per referral.</i></p>""",
            severity="INFO")

        self.log_summary(active=len(joined), pending=len(pending), earnings=earnings)
        return {"active": len(joined), "pending": len(pending), "programs": len(PROGRAMS)}

if __name__ == "__main__":
    AffiliateTrackerBot().run()
