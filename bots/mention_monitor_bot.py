#!/usr/bin/env python3
"""
MENTION MONITOR BOT v2.0 — S.C. Thomas Internal Agency
Monitors brand mentions across web, drafts replies, flags hot engagement.
Sources: Google Alerts RSS, Reddit, news mentions.
Routes draft replies to Gmail for one-tap approval.
Schedule: Every 4 hours.
"""

import os
import sys
import json
import smtplib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, ClaudeClient, with_retry

class MentionMonitorBot(BaseBot):
    VERSION = "2.0.0"

    BRAND_TERMS = os.getenv("BRAND_TERMS", "").split(",") if os.getenv("BRAND_TERMS") else [
        # Add your brand names and terms here
        # "S.C. Thomas", "NYSpotlight", "yourbrand"
    ]

    def __init__(self):
        super().__init__("mention-monitor")
        self.seen_urls = set(self.state.get("seen_urls", []))

    # ── SOURCES ───────────────────────────────────────────────────────────────
    @with_retry(max_retries=2, delay=3.0)
    def fetch_google_alerts_rss(self, term: str) -> list:
        """Fetch Google Alerts RSS for a search term"""
        encoded  = urllib.parse.quote(term)
        rss_url  = f"https://www.google.com/alerts/feeds/0/{encoded}"
        # Note: requires signed-in Google Alerts RSS — use generic news search instead
        # Fallback to news search RSS
        news_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

        try:
            req = urllib.request.Request(news_url,
                headers={"User-Agent": "Mozilla/5.0 (MentionBot/2.0)"})
            with urllib.request.urlopen(req, timeout=15) as r:
                content = r.read()
            root    = ET.fromstring(content)
            channel = root.find("channel")
            items   = []
            for item in (channel.findall("item") if channel else [])[:10]:
                title = item.findtext("title", "")
                link  = item.findtext("link",  "")
                desc  = item.findtext("description", "")
                pubdate = item.findtext("pubDate", "")
                if link and link not in self.seen_urls:
                    items.append({
                        "title":   title,
                        "url":     link,
                        "snippet": desc[:300],
                        "date":    pubdate,
                        "source":  "google_news",
                        "term":    term,
                    })
            return items
        except Exception as e:
            self.logger.warning(f"RSS fetch failed for '{term}': {e}")
            return []

    @with_retry(max_retries=2, delay=2.0)
    def fetch_reddit_mentions(self, term: str) -> list:
        """Search Reddit for brand mentions"""
        encoded = urllib.parse.quote(term)
        url     = f"https://www.reddit.com/search.json?q={encoded}&sort=new&limit=10&type=link"
        try:
            req = urllib.request.Request(url,
                headers={"User-Agent": "MentionBot/2.0 (mention monitoring)"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())

            posts = data.get("data", {}).get("children", [])
            items = []
            for post in posts:
                pd = post.get("data", {})
                url = f"https://reddit.com{pd.get('permalink','')}"
                if url not in self.seen_urls:
                    items.append({
                        "title":    pd.get("title", ""),
                        "url":      url,
                        "snippet":  pd.get("selftext", "")[:300],
                        "score":    pd.get("score", 0),
                        "subreddit":pd.get("subreddit", ""),
                        "source":   "reddit",
                        "term":     term,
                    })
            return items
        except Exception as e:
            self.logger.warning(f"Reddit fetch failed for '{term}': {e}")
            return []

    # ── ANALYZER ──────────────────────────────────────────────────────────────
    def analyze_mentions(self, mentions: list) -> list:
        """Use Claude to analyze and classify mentions"""
        if not mentions or not Config.ANTHROPIC_API_KEY:
            for m in mentions:
                m["sentiment"]  = "neutral"
                m["priority"]   = "LOW"
                m["reply_draft"]= None
            return mentions

        batch_text = "\n".join([
            f"{i+1}. [{m['source']}] {m['title']}\n   {m['snippet'][:200]}"
            for i, m in enumerate(mentions[:10])
        ])

        system = """You are the reputation manager for S.C. Thomas.
Analyze brand mentions and classify them.
For HIGH priority mentions, draft a brief, professional response.
Return ONLY valid JSON array."""

        prompt = f"""Analyze these mentions and return JSON:

{batch_text}

For each mention:
{{
  "index": 1,
  "sentiment": "positive|negative|neutral",
  "priority": "HIGH|MEDIUM|LOW",
  "action": "respond|monitor|ignore",
  "reply_draft": "draft response if action=respond, else null"
}}

HIGH priority = negative press, direct criticism, opportunity to engage positively
Reply drafts should be professional, brief, on-brand for S.C. Thomas."""

        try:
            results = ClaudeClient.complete(system, prompt, max_tokens=1500, json_mode=True)
            if isinstance(results, list):
                for r in results:
                    idx = r.get("index", 1) - 1
                    if 0 <= idx < len(mentions):
                        mentions[idx].update({
                            "sentiment":  r.get("sentiment", "neutral"),
                            "priority":   r.get("priority", "LOW"),
                            "action":     r.get("action", "monitor"),
                            "reply_draft":r.get("reply_draft"),
                        })
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")

        return mentions

    # ── REPORTER ──────────────────────────────────────────────────────────────
    def send_digest(self, mentions: list):
        """Email mention digest to Chairman"""
        high     = [m for m in mentions if m.get("priority") == "HIGH"]
        medium   = [m for m in mentions if m.get("priority") == "MEDIUM"]
        date_str = datetime.now().strftime("%b %d, %Y")

        if not mentions:
            self.logger.info("No new mentions — skipping digest")
            return

        def mention_row(m):
            sentiment_color = {"positive": "#2e7d32", "negative": "#c62828"}.get(
                m.get("sentiment","neutral"), "#555")
            draft_section = ""
            if m.get("reply_draft"):
                draft_section = f"""
<div style="background:#f5f5f5;padding:8px 12px;margin-top:8px;font-style:italic;font-size:12px;">
  <strong>Draft reply:</strong> {m['reply_draft']}
</div>"""
            return f"""
<div style="border-left:4px solid {sentiment_color};padding:10px 14px;margin-bottom:12px;background:#fafafa;">
  <strong><a href="{m.get('url','#')}" style="color:#1565c0;">{m.get('title','')[:80]}</a></strong><br>
  <span style="font-size:12px;color:#666;">{m.get('source','').upper()} | {m.get('term','')} | {m.get('sentiment','').upper()}</span><br>
  <span style="font-size:13px;">{m.get('snippet','')[:150]}</span>
  {draft_section}
</div>"""

        high_html   = "".join(mention_row(m) for m in high)
        medium_html = "".join(mention_row(m) for m in medium[:5])

        html = f"""<html><body style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;">
<div style="background:#111;color:#fff;padding:18px 22px;">
  <h2 style="margin:0;font-size:18px;">🔔 MENTION MONITOR — {date_str}</h2>
  <p style="margin:4px 0 0;color:#aaa;font-size:12px;">{len(mentions)} new mentions | {len(high)} HIGH priority</p>
</div>
<div style="padding:22px;">
{('<h3 style="color:#c62828;border-bottom:2px solid #c62828;padding-bottom:6px;">🔴 HIGH PRIORITY — ACT NOW</h3>' + high_html) if high else ''}
{('<h3 style="margin-top:20px;border-bottom:2px solid #111;padding-bottom:6px;">🟡 MEDIUM PRIORITY</h3>' + medium_html) if medium else ''}
<p style="margin-top:20px;font-size:12px;color:#999;">Mention Monitor Bot v{self.VERSION} | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>"""

        msg = MIMEMultipart("alternative")
        priority_flag = "🔴 " if high else ""
        msg["Subject"] = f"{priority_flag}Mention Monitor — {len(mentions)} new — {date_str}"
        msg["From"]    = Config.GMAIL_USER
        msg["To"]      = Config.CHAIRMAN_EMAIL
        msg.attach(MIMEText(html, "html"))

        if not Config.GMAIL_APP_PASS:
            self.logger.info(f"No email creds — {len(mentions)} mentions found")
            return

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(Config.GMAIL_USER, Config.GMAIL_APP_PASS)
                s.sendmail(Config.GMAIL_USER, Config.CHAIRMAN_EMAIL, msg.as_string())
            self.logger.info(f"Mention digest sent: {len(mentions)} mentions")
        except Exception as e:
            self.logger.error(f"Email failed: {e}")

    # ── MAIN ──────────────────────────────────────────────────────────────────
    def execute(self) -> dict:
        if not self.BRAND_TERMS:
            self.logger.warning(
                "No BRAND_TERMS configured. "
                "Set BRAND_TERMS env var: 'YourBrand,YourProduct,YourName'"
            )
            return {"items_processed": 0, "warning": "No brand terms configured"}

        self.logger.info(f"Checking {len(self.BRAND_TERMS)} brand terms...")
        all_mentions = []

        for term in self.BRAND_TERMS:
            term = term.strip()
            if not term:
                continue
            news_mentions   = self.fetch_google_alerts_rss(term)
            reddit_mentions = self.fetch_reddit_mentions(term)
            all_mentions.extend(news_mentions + reddit_mentions)

        if all_mentions:
            analyzed = self.analyze_mentions(all_mentions)
            self.send_digest(analyzed)

            # Save seen URLs
            new_urls = [m["url"] for m in all_mentions if m.get("url")]
            self.seen_urls.update(new_urls)
            self.state.set("seen_urls", list(self.seen_urls)[-500:])  # Keep last 500

        self.log_summary(
            mentions_found=len(all_mentions),
            terms_checked=len(self.BRAND_TERMS)
        )
        return {"items_processed": len(all_mentions)}


if __name__ == "__main__":
    bot = MentionMonitorBot()
    bot.run()

# SETUP:
# export BRAND_TERMS="YourBrand,YourProduct,YourName"
# export GMAIL_APP_PASS=...
# SCHEDULE: Every 4 hours
# cron: '0 */4 * * *'
