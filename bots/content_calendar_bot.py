#!/usr/bin/env python3
"""
CONTENT CALENDAR AUTO-BUILDER BOT — S.C. Thomas Internal Agency
Generates a full month of social + blog content ideas + schedule
Uses Claude to create content ideas aligned with brand pillars
Outputs: CSV (import to Buffer/Notion/Sheets) + HTML calendar view
Usage: python content_calendar_bot.py --month 2026-04
"""

import os
import csv
import json
import argparse
import requests
import calendar
from datetime import datetime, timedelta
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OUTPUT_DIR        = Path("content_calendars")
OUTPUT_DIR.mkdir(exist_ok=True)

# Customize these for your brand
BRAND_CONFIG = {
    "name":         os.getenv("BRAND_NAME", "S.C. Thomas"),
    "niche":        os.getenv("BRAND_NICHE", "media, publishing, content, personal brand"),
    "audience":     os.getenv("BRAND_AUDIENCE", "entrepreneurs, creators, media professionals"),
    "pillars":      os.getenv("BRAND_PILLARS", "authority building, media strategy, content monetization, personal brand").split(","),
    "tone":         "Direct, authoritative, sharp, no fluff",
    "platforms":    os.getenv("PLATFORMS", "twitter,linkedin").split(","),
    "post_freq":    int(os.getenv("POST_FREQ", "5")),  # posts per week per platform
}

CONTENT_TYPES = [
    "Educational tip", "Contrarian take", "Personal story",
    "Case study/result", "Industry insight", "Behind the scenes",
    "Question/engagement", "Tactical how-to", "Opinion piece", "Curated resource"
]

# ─── CLAUDE CONTENT GENERATOR ─────────────────────────────────────────────────
def generate_content_ideas(month_str, num_ideas=40):
    if not ANTHROPIC_API_KEY:
        return _mock_ideas(num_ideas)

    system = f"""You are the content strategist for {BRAND_CONFIG['name']}.
Brand niche: {BRAND_CONFIG['niche']}
Target audience: {BRAND_CONFIG['audience']}
Content pillars: {', '.join(BRAND_CONFIG['pillars'])}
Tone: {BRAND_CONFIG['tone']}

Generate content ideas that are specific, actionable, and non-generic.
Each idea must be immediately usable — specific enough to write from directly."""

    prompt = f"""Generate {num_ideas} social media content ideas for {month_str}.

For each idea provide:
- pillar: which content pillar it belongs to
- type: {' | '.join(CONTENT_TYPES)}
- platform: twitter | linkedin | both
- hook: The exact opening line (under 15 words)
- angle: 1-sentence description of the post angle
- cta: What action the post drives

Return ONLY valid JSON array:
[{{"pillar":"...","type":"...","platform":"...","hook":"...","angle":"...","cta":"..."}}]"""

    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 3000, "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=45
        )
        text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[calendar-bot] Claude error: {e}")
        return _mock_ideas(num_ideas)

def _mock_ideas(n):
    return [{"pillar": "authority building", "type": "Contrarian take", "platform": "twitter",
             "hook": f"Unpopular opinion about content strategy #{i+1}",
             "angle": "Challenge conventional wisdom with specific insight",
             "cta": "Follow for more"} for i in range(n)]

# ─── CALENDAR BUILDER ─────────────────────────────────────────────────────────
def build_calendar(year, month, ideas):
    """Assign content ideas to specific dates"""
    cal = []
    _, days_in_month = calendar.monthrange(year, month)
    idea_idx = 0
    
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day)
        weekday = date.weekday()
        
        # Skip weekends for most platforms (adjust as needed)
        if weekday >= 5: continue
        
        # Assign by platform
        for platform in BRAND_CONFIG["platforms"]:
            if idea_idx < len(ideas):
                idea = ideas[idea_idx].copy()
                if idea["platform"] in [platform, "both"]:
                    cal.append({
                        "date":      date.strftime("%Y-%m-%d"),
                        "day":       date.strftime("%A"),
                        "platform":  platform.capitalize(),
                        "pillar":    idea.get("pillar", "").strip(),
                        "type":      idea.get("type", ""),
                        "hook":      idea.get("hook", ""),
                        "angle":     idea.get("angle", ""),
                        "cta":       idea.get("cta", ""),
                        "status":    "Draft",
                        "copy":      "",
                        "published": "",
                    })
                    idea_idx += 1
    return cal

def save_csv(calendar_data, filename):
    fields = ["date", "day", "platform", "pillar", "type", "hook", "angle", "cta", "status", "copy", "published"]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(calendar_data)
    print(f"[calendar-bot] CSV saved: {filename}")

def save_html(calendar_data, filename, month_str):
    rows = "".join([
        f"""<tr style="{'background:#f9f9f9' if i%2 else ''}">
          <td style="padding:8px 10px;font-size:13px;white-space:nowrap;">{r['date']}</td>
          <td style="padding:8px 10px;font-size:13px;">{r['day'][:3]}</td>
          <td style="padding:8px 10px;"><span style="background:{'#1565c0' if r['platform']=='Twitter' else '#0d7a5f'};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">{r['platform']}</span></td>
          <td style="padding:8px 10px;font-size:12px;color:#666;">{r['pillar']}</td>
          <td style="padding:8px 10px;font-size:12px;">{r['type']}</td>
          <td style="padding:8px 10px;font-size:13px;"><strong>{r['hook']}</strong></td>
          <td style="padding:8px 10px;font-size:12px;color:#555;">{r['angle']}</td>
          <td style="padding:8px 10px;"><span style="background:#fff3e0;color:#e65100;padding:2px 8px;border-radius:12px;font-size:11px;">{r['status']}</span></td>
        </tr>"""
        for i, r in enumerate(calendar_data)
    ])

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Content Calendar — {month_str}</title>
<style>body{{font-family:Arial,sans-serif;margin:0;padding:20px;}}
table{{border-collapse:collapse;width:100%;}}
th{{background:#111;color:#fff;padding:10px;text-align:left;font-size:12px;}}
tr:hover{{background:#fffde7!important;}}</style></head>
<body>
<h1 style="margin-bottom:4px;">Content Calendar — {month_str}</h1>
<p style="color:#666;margin-top:0;">{len(calendar_data)} posts planned | {BRAND_CONFIG['name']}</p>
<table>
  <thead><tr>
    <th>Date</th><th>Day</th><th>Platform</th><th>Pillar</th>
    <th>Type</th><th>Hook</th><th>Angle</th><th>Status</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>
</body></html>"""
    with open(filename, "w") as f: f.write(html)
    print(f"[calendar-bot] HTML saved: {filename}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def run(month_str):
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except:
        print(f"[calendar-bot] Invalid month format. Use YYYY-MM (e.g. 2026-04)")
        return

    year, month = dt.year, dt.month
    month_label  = dt.strftime("%B %Y")
    print(f"[calendar-bot] Building calendar for {month_label}")

    print(f"[calendar-bot] Generating content ideas...")
    ideas = generate_content_ideas(month_label, num_ideas=60)
    print(f"[calendar-bot] Got {len(ideas)} ideas")

    cal_data  = build_calendar(year, month, ideas)
    print(f"[calendar-bot] Scheduled {len(cal_data)} posts")

    base      = OUTPUT_DIR / f"content_calendar_{month_str}"
    save_csv(cal_data,  Path(str(base) + ".csv"))
    save_html(cal_data, Path(str(base) + ".html"), month_label)

    # Summary
    from collections import Counter
    by_platform = Counter(r["platform"] for r in cal_data)
    by_pillar   = Counter(r["pillar"] for r in cal_data)
    print(f"\n[calendar-bot] SUMMARY:")
    print(f"  Total posts: {len(cal_data)}")
    for platform, count in by_platform.items():
        print(f"  {platform}: {count} posts")
    print(f"  Files: {base}.csv + {base}.html")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--month", default=datetime.now().strftime("%Y-%m"), help="Month in YYYY-MM format")
    args = p.parse_args()
    run(args.month)

# SETUP: pip install requests
# Run: python content_calendar_bot.py --month 2026-04
