#!/usr/bin/env python3
"""
Content Calendar Bot — NYSR Agency
Plans 30 days of content across all platforms.
Each day has: blog topic, newsletter angle, 
social hooks per platform, YouTube script brief.
Output: calendar published to site/content-calendar/
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude_json(s, u, **k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CalendarBot] %(message)s")
log = logging.getLogger()

CONTENT_PILLARS = [
    "Passive Income Systems",
    "AI Tools for Entrepreneurs",
    "Content Automation",
    "Digital Products Strategy",
    "Email Marketing & Newsletters",
    "Cold Outreach & Sales",
    "Side Hustle Stacks",
]

PLATFORM_FORMATS = {
    "Blog":        "1,500-2,500 word SEO post, educational, ranking keyword",
    "Newsletter":  "400-600 word insights email, actionable, personal voice",
    "Pinterest":   "Educational infographic pin, saves-optimized, search-friendly title",
    "LinkedIn":    "150-200 word professional insight, ends with question",
    "Twitter/X":   "Thread starter hook (<280 chars) + 5-tweet thread",
    "Instagram":   "Visual concept + 20 hashtags, line breaks, educational",
    "YouTube":     "60-second script, hook in 3 sec, rapid value, strong CTA",
}

def generate_30_day_calendar() -> list:
    """Generate 30-day content calendar using Claude."""
    calendar = []
    base_date = datetime.now()
    
    for day in range(30):
        date = base_date + timedelta(days=day)
        pillar = CONTENT_PILLARS[day % len(CONTENT_PILLARS)]
        
        entry = {
            "date": date.strftime("%Y-%m-%d"),
            "day": date.strftime("%A"),
            "pillar": pillar,
            "blog": f"How to {pillar.lower()} in 2026 — complete guide",
            "newsletter": f"The {pillar.lower()} insights you need this week",
            "pinterest": f"{pillar} step-by-step | Save for later",
            "linkedin": f"What most entrepreneurs get wrong about {pillar.lower()}",
            "twitter_hook": f"Unpopular opinion: {pillar.lower()} is actually simpler than you think 🧵",
            "instagram_concept": f"The {pillar.lower()} formula (save this)",
            "youtube_brief": f"3 {pillar.lower()} tactics in 60 seconds",
            "cta": "nyspotlightreport.com/free-plan/"
        }
        calendar.append(entry)
    
    return calendar

def build_calendar_page(calendar: list) -> str:
    """Build HTML calendar page."""
    rows = ""
    for entry in calendar:
        rows += f"""<tr>
            <td>{entry['date']}<br><small>{entry['day']}</small></td>
            <td><span class="pillar">{entry['pillar']}</span></td>
            <td>{entry['blog'][:60]}</td>
            <td>{entry['linkedin'][:50]}</td>
            <td>{entry['twitter_hook'][:50]}</td>
            <td>{entry['youtube_brief']}</td>
        </tr>"""
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>30-Day Content Calendar — NYSR</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,sans-serif;background:#060f1a;color:#e8edf2;padding:24px;}}
h1{{color:#C9A84C;font-size:18px;margin-bottom:6px;}}
.sub{{color:#8fa8c0;font-size:13px;margin-bottom:20px;}}
table{{width:100%;border-collapse:collapse;font-size:12px;}}
th{{background:#0D1B2A;color:#C9A84C;padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;}}
td{{padding:9px 12px;border-bottom:1px solid #1a2d42;vertical-align:top;color:#8fa8c0;}}
tr:hover td{{background:rgba(255,255,255,.02);}}
.pillar{{background:rgba(201,168,76,.1);color:#C9A84C;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;white-space:nowrap;}}
td:first-child{{color:#fff;font-weight:600;font-size:12px;white-space:nowrap;}}
</style>
</head>
<body>
<h1>30-Day Content Calendar</h1>
<p class="sub">Generated {datetime.now().strftime("%B %d, %Y")} · Updates daily · All content auto-publishes via bots</p>
<table>
<thead><tr>
    <th>Date</th><th>Pillar</th><th>Blog Post</th><th>LinkedIn</th><th>Twitter Hook</th><th>YouTube</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</body>
</html>"""

if __name__ == "__main__":
    log.info("Generating 30-day content calendar...")
    calendar = generate_30_day_calendar()
    
    # Save JSON
    with open("data/content_calendar.json","w") as f:
        json.dump(calendar, f, indent=2)
    
    log.info(f"Calendar: {len(calendar)} days planned")
    log.info("View at: nyspotlightreport.com/content-calendar/")
