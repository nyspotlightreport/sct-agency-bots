# S.C. Thomas Internal Agency — System v2.0
## Complete Setup & Operations Guide

---

## WHAT THIS IS

A fully autonomous AI-powered agency infrastructure that:
- Runs 11 bots on automated schedules
- Self-monitors and self-heals failures
- Self-improves weekly using Claude
- Alerts Chairman only when action is needed
- Requires zero ongoing maintenance once deployed

---

## ARCHITECTURE

```
AGENCY COMMAND CENTER (always-on orchestrator)
     │
     ├── CRITICAL (every 15 min)
     │   └── uptime_monitor_bot.py        — Site uptime + SSL + speed
     │
     ├── DAILY (7am ET)
     │   ├── inbox_triage_bot.py          — Gmail categorize + draft replies
     │   └── invoice_bot.py (--remind)    — Payment reminders
     │
     ├── WEEKLY
     │   ├── weekly_report_bot_v2.py      — KPI dashboard email (Mon 8am)
     │   ├── seo_rank_tracker_bot.py      — Rankings + backlinks (Mon + Thu)
     │   ├── lead_pipeline_bot.py         — Apollo → score → HubSpot (Tue noon)
     │   └── competitor_monitor_bot.py    — Site change detection (Sun 11pm)
     │
     ├── MONTHLY
     │   └── content_calendar_bot.py      — Build next month's content calendar
     │
     └── SELF-IMPROVEMENT (Sun 6am)
         └── self_improvement_bot.py      — Review performance, suggest upgrades

ON-DEMAND (Claude triggers these when you ask):
  content_repurpose_bot.py      — 1 input → 5 platform variants
  meeting_notes_bot.py          — Notes → action items → tasks
  invoice_bot.py (--create)     — Generate + send new invoice
```

---

## QUICK START (20 minutes)

### Step 1: GitHub Setup (5 min)
```bash
# Create a new PRIVATE repo on github.com
git init agency-bots
cd agency-bots
cp /path/to/bots/* .
git add .
git commit -m "Agency system v2.0"
git remote add origin https://github.com/YOUR_USERNAME/agency-bots.git
git push -u origin main
```

### Step 2: Deploy GitHub Actions (2 min)
```bash
python deploy_full_system.py
git add .github/
git commit -m "Add automated workflows"
git push
```

### Step 3: Add Secrets (5 min)
Go to: GitHub Repo → Settings → Secrets and variables → Actions

Required:
| Secret | Value |
|--------|-------|
| ANTHROPIC_API_KEY | From console.anthropic.com |
| GMAIL_USER | seanb041992@gmail.com |
| GMAIL_APP_PASS | From myaccount.google.com/apppasswords |
| CHAIRMAN_EMAIL | seanb041992@gmail.com |
| AHREFS_API_KEY | From ahrefs.com/api |
| HUBSPOT_API_KEY | From HubSpot → Settings → Private Apps |
| APOLLO_API_KEY | From Apollo.io → Settings → API |
| TARGET_DOMAIN | yourdomain.com |
| MONITORED_SITES | https://site1.com,https://site2.com |
| PAYPAL_ME_LINK | https://paypal.me/yourhandle |

### Step 4: Configure Your Sites (3 min)
Edit `uptime_monitor_bot.py` — add your sites to `MONITORED_SITES`
Edit `competitor_monitor_bot.py` — add competitors to `COMPETITORS`

### Step 5: Gmail Auth for Inbox Bot (5 min)
```bash
# Run once locally to generate token.pickle
pip install google-auth google-auth-oauthlib google-api-python-client
python inbox_triage_bot.py
# Follow browser auth flow
# token.pickle is saved — add as GitHub secret or commit encrypted
```

---

## WHAT CHAIRMAN RECEIVES AUTOMATICALLY

| Email | When | From |
|-------|------|------|
| Weekly KPI Report | Monday 8am | Drew Sinclair |
| Inbox Triage Digest | Daily 7am | Inbox Triage Bot |
| SEO Report | Mon + Thu | SEO Bot |
| Lead Pipeline Results | Tuesday noon | Lead Bot |
| Competitor Alert | When changes detected | Monitor Bot |
| Site Down Alert | Immediately | Uptime Bot |
| Invoice Reminders sent | Daily (if overdue) | Invoice Bot |
| Self-Improvement Report | Sunday 6am | Improvement Engine |
| System Health Status | Daily 8am | Command Center |

---

## ON-DEMAND BOT USAGE

```bash
# Repurpose content
python content_repurpose_bot.py --file article.txt

# Process meeting notes
python meeting_notes_bot.py --file notes.txt --title "Client Call"

# Create invoice
python invoice_bot.py --create --client "Client Name" --email "client@co.com" --amount 2500 --description "SEO Services"

# Check all invoice status
python invoice_bot.py --status

# Build content calendar
python content_calendar_bot.py --month 2026-05

# Find leads
python lead_pipeline_bot.py --search "founder CEO media NYC" --limit 30

# Check system status
python agency_command_center.py --status
```

---

## SELF-HEALING BEHAVIOR

The system auto-heals in these ways:

1. **Retry logic**: All API calls retry 3x with exponential backoff
2. **Failure alerts**: Chairman is emailed when any bot fails 2+ times
3. **Recovery alerts**: Chairman is emailed when a bot recovers
4. **Health checks**: Command Center checks all bots every hour
5. **Daily status email**: Morning digest shows all bot statuses
6. **Self-improvement**: Weekly Claude review suggests and flags fixes

---

## ADDING A NEW BOT

1. Create `new_bot.py` inheriting from `BaseBot`
2. Implement `execute()` method
3. Add to `BOT_REGISTRY` in `agency_command_center.py`
4. Add GitHub Actions workflow
5. Push — it runs automatically

Template:
```python
from agency_core import BaseBot

class MyNewBot(BaseBot):
    def __init__(self):
        super().__init__("my-bot", required_config=["SOME_API_KEY"])

    def execute(self) -> dict:
        # Your logic here
        result = self.http.get("https://api.example.com/data")
        data   = self.claude.complete("system prompt", "user prompt")
        return {"items_processed": 1}

if __name__ == "__main__":
    MyNewBot().run()
```

---

## FILE STRUCTURE

```
bots/
├── agency_core.py              Core utilities (import by all bots)
├── agency_command_center.py    Master orchestrator
├── self_improvement_bot.py     Weekly self-improvement engine
├── weekly_report_bot_v2.py     KPI reports
├── inbox_triage_bot.py         Gmail management
├── seo_rank_tracker_bot.py     SEO monitoring
├── lead_pipeline_bot.py        Lead generation
├── competitor_monitor_bot.py   Competitor tracking
├── uptime_monitor_bot.py       Site monitoring
├── invoice_bot.py              Invoice management
├── content_calendar_bot.py     Content planning
├── content_repurpose_bot.py    Content repurposing
├── meeting_notes_bot.py        Meeting processing
├── deploy_full_system.py       GitHub Actions generator
└── README.md                   This file

state/                          Persistent bot state (auto-created)
logs/                           Bot logs (auto-created)
```

---

*Agency System v2.0 | S.C. Thomas Internal Agency | Built by Reese Morgan*
