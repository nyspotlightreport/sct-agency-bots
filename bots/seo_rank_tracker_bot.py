#!/usr/bin/env python3
"""
SEO RANK TRACKER + BACKLINK MONITOR BOT — S.C. Thomas Internal Agency
Tracks keyword rankings and new/lost backlinks via Ahrefs API.
Alerts Chairman when rankings move significantly or new backlinks appear.
Schedule: Every Monday + Thursday (twice weekly)
"""

import os
import json
import smtplib
import requests
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── CONFIG ───────────────────────────────────────────────────────────────────
AHREFS_API_KEY  = os.getenv("AHREFS_API_KEY", "")
GMAIL_USER      = os.getenv("GMAIL_USER", "nyspotlightreport@gmail.com")
GMAIL_APP_PASS  = os.getenv("GMAIL_APP_PASS", "")
CHAIRMAN_EMAIL  = os.getenv("CHAIRMAN_EMAIL", "nyspotlightreport@gmail.com")
TARGET_DOMAIN   = os.getenv("TARGET_DOMAIN", "")   # e.g. "yourdomain.com"
STATE_FILE      = Path("seo_state.json")

# Keywords to track (add your target keywords)
TRACKED_KEYWORDS = os.getenv("TRACKED_KEYWORDS", "").split(",") if os.getenv("TRACKED_KEYWORDS") else [
    # Add your keywords here or set TRACKED_KEYWORDS env var
    # "your main keyword",
    # "second keyword",
]

RANK_ALERT_THRESHOLD = 3  # Alert if rank changes by this many positions

# ─── STATE MANAGEMENT ─────────────────────────────────────────────────────────
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f: return json.load(f)
    return {"rankings": {}, "backlinks": {}, "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)

# ─── AHREFS API ───────────────────────────────────────────────────────────────
def get_headers():
    return {"Authorization": f"Bearer {AHREFS_API_KEY}"}

def get_keyword_rankings(domain):
    """Pull organic keyword rankings for domain"""
    if not AHREFS_API_KEY or not domain:
        return []
    try:
        r = requests.get(
            "https://api.ahrefs.com/v3/site-explorer/organic-keywords",
            params={
                "select": "keyword,sum_traffic,pos,volume,keyword_difficulty",
                "target": domain,
                "mode": "domain",
                "limit": 100,
                "order_by": "sum_traffic:desc"
            },
            headers=get_headers(), timeout=15
        )
        return r.json().get("keywords", [])
    except Exception as e:
        print(f"[seo-bot] Rankings error: {e}")
        return []

def get_new_backlinks(domain):
    """Pull recently acquired backlinks"""
    if not AHREFS_API_KEY or not domain:
        return []
    try:
        r = requests.get(
            "https://api.ahrefs.com/v3/site-explorer/all-backlinks",
            params={
                "select": "url_from,domain_rating_source,title,anchor,first_seen",
                "target": domain,
                "mode": "domain",
                "limit": 50,
                "order_by": "first_seen:desc"
            },
            headers=get_headers(), timeout=15
        )
        return r.json().get("backlinks", [])
    except Exception as e:
        print(f"[seo-bot] Backlinks error: {e}")
        return []

def get_domain_metrics(domain):
    """Pull DR, traffic, keywords count"""
    if not AHREFS_API_KEY or not domain:
        return {}
    try:
        r = requests.get(
            "https://api.ahrefs.com/v3/site-explorer/metrics",
            params={"select": "domain_rating,org_traffic,org_keywords,ref_domains", "target": domain, "mode": "domain"},
            headers=get_headers(), timeout=15
        )
        return r.json().get("metrics", {})
    except Exception as e:
        print(f"[seo-bot] Metrics error: {e}")
        return {}

# ─── ANALYSIS ─────────────────────────────────────────────────────────────────
def analyze_rank_changes(current_rankings, previous_rankings):
    changes = {"improved": [], "dropped": [], "new": [], "lost": []}
    
    current_map = {kw["keyword"]: kw.get("pos", 999) for kw in current_rankings}
    prev_map    = previous_rankings.copy()

    for keyword, current_pos in current_map.items():
        if keyword not in prev_map:
            changes["new"].append({"keyword": keyword, "position": current_pos})
        else:
            prev_pos = prev_map[keyword]
            delta = prev_pos - current_pos  # positive = improved
            if delta >= RANK_ALERT_THRESHOLD:
                changes["improved"].append({"keyword": keyword, "from": prev_pos, "to": current_pos, "delta": delta})
            elif delta <= -RANK_ALERT_THRESHOLD:
                changes["dropped"].append({"keyword": keyword, "from": prev_pos, "to": current_pos, "delta": delta})

    return changes

def analyze_new_backlinks(current_backlinks, previous_urls):
    new_links = []
    current_urls = {bl.get("url_from","") for bl in current_backlinks}
    for bl in current_backlinks:
        url = bl.get("url_from","")
        if url and url not in previous_urls:
            new_links.append(bl)
    return new_links[:20]  # Top 20 newest

# ─── REPORT ───────────────────────────────────────────────────────────────────
def build_report(metrics, rank_changes, new_backlinks):
    date_str = datetime.now().strftime("%b %d, %Y")
    
    improved_rows = "".join([
        f"<tr><td style='padding:6px 8px;'>{c['keyword']}</td><td style='padding:6px 8px;color:#2e7d32;font-weight:bold;'>#{c['to']} ▲{c['delta']}</td><td style='padding:6px 8px;color:#888;'>was #{c['from']}</td></tr>"
        for c in rank_changes.get("improved", [])[:10]
    ])
    dropped_rows = "".join([
        f"<tr><td style='padding:6px 8px;'>{c['keyword']}</td><td style='padding:6px 8px;color:#c62828;font-weight:bold;'>#{c['to']} ▼{abs(c['delta'])}</td><td style='padding:6px 8px;color:#888;'>was #{c['from']}</td></tr>"
        for c in rank_changes.get("dropped", [])[:10]
    ])
    backlink_rows = "".join([
        f"<tr><td style='padding:6px 8px;font-size:12px;'><a href='{bl.get('url_from','')}' style='color:#1565c0;'>{bl.get('url_from','')[:60]}</a></td><td style='padding:6px 8px;'>DR {bl.get('domain_rating_source',0)}</td></tr>"
        for bl in new_backlinks[:10]
    ])
    
    return f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#111;">
<div style="background:#111;color:#fff;padding:20px 24px;">
  <h2 style="margin:0;font-size:18px;">📈 SEO REPORT — {date_str}</h2>
  <p style="margin:4px 0 0;color:#aaa;font-size:12px;">{TARGET_DOMAIN}</p>
</div>
<div style="padding:24px;">
  <table width="100%" style="border-collapse:collapse;margin-bottom:24px;">
    <tr>
      <td style="padding:12px;background:#f5f5f5;text-align:center;"><strong>DR</strong><br>{metrics.get('domain_rating','—')}</td>
      <td style="padding:12px;background:#f5f5f5;text-align:center;"><strong>Organic Traffic</strong><br>{metrics.get('org_traffic','—')}</td>
      <td style="padding:12px;background:#f5f5f5;text-align:center;"><strong>Keywords</strong><br>{metrics.get('org_keywords','—')}</td>
      <td style="padding:12px;background:#f5f5f5;text-align:center;"><strong>Ref Domains</strong><br>{metrics.get('ref_domains','—')}</td>
    </tr>
  </table>

  {"<h3 style='color:#2e7d32;border-bottom:2px solid #2e7d32;padding-bottom:6px;'>🟢 RANKINGS IMPROVED</h3><table width='100%' style='border-collapse:collapse;font-size:13px;'>" + improved_rows + "</table>" if improved_rows else ""}
  {"<h3 style='color:#c62828;margin-top:20px;border-bottom:2px solid #c62828;padding-bottom:6px;'>🔴 RANKINGS DROPPED</h3><table width='100%' style='border-collapse:collapse;font-size:13px;'>" + dropped_rows + "</table>" if dropped_rows else ""}
  {"<h3 style='margin-top:20px;border-bottom:2px solid #111;padding-bottom:6px;'>🔗 NEW BACKLINKS</h3><table width='100%' style='border-collapse:collapse;font-size:13px;'>" + backlink_rows + "</table>" if backlink_rows else ""}

  {"<div style='background:#fff8e1;border-left:4px solid #f9a825;padding:12px 16px;margin-top:20px;'><strong>⚠️ No data returned</strong> — Check AHREFS_API_KEY and TARGET_DOMAIN env vars.</div>" if not metrics else ""}

  <p style="margin-top:24px;font-size:12px;color:#999;">SEO Rank Tracker Bot | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>"""

def send_report(html, subject):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = CHAIRMAN_EMAIL
    msg.attach(MIMEText(html, "html"))
    if not GMAIL_APP_PASS:
        print("[seo-bot] No email password — report printed to console")
        print(f"SUBJECT: {subject}")
        return
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, CHAIRMAN_EMAIL, msg.as_string())
        print(f"[seo-bot] Report sent: {subject}")
    except Exception as e:
        print(f"[seo-bot] Email failed: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run():
    print(f"[seo-bot] Starting {datetime.now()} | Domain: {TARGET_DOMAIN}")
    state = load_state()

    metrics       = get_domain_metrics(TARGET_DOMAIN)
    rankings      = get_keyword_rankings(TARGET_DOMAIN)
    backlinks     = get_new_backlinks(TARGET_DOMAIN)

    # Analyze changes
    prev_rankings = state.get("rankings", {})
    prev_bl_urls  = set(state.get("backlink_urls", []))
    rank_changes  = analyze_rank_changes(rankings, prev_rankings)
    new_backlinks = analyze_new_backlinks(backlinks, prev_bl_urls)

    # Update state
    state["rankings"]      = {kw["keyword"]: kw.get("pos", 999) for kw in rankings}
    state["backlink_urls"] = list({bl.get("url_from","") for bl in backlinks})
    state["last_run"]      = datetime.now().isoformat()
    save_state(state)

    # Build and send
    has_news = rank_changes["improved"] or rank_changes["dropped"] or new_backlinks
    subject  = f"📈 SEO Report — {datetime.now().strftime('%b %d')} {'⚡ Changes detected' if has_news else ''}"
    html     = build_report(metrics, rank_changes, new_backlinks)
    send_report(html, subject)
    print(f"[seo-bot] Complete. Changes: {sum(len(v) for v in rank_changes.values())} | New backlinks: {len(new_backlinks)}")

if __name__ == "__main__":
    run()

# GITHUB ACTIONS SCHEDULE:
# cron: '0 12 * * 1,4'  # Monday + Thursday noon UTC
# Secrets: AHREFS_API_KEY, GMAIL_APP_PASS, TARGET_DOMAIN, CHAIRMAN_EMAIL
