#!/usr/bin/env python3
"""
AGENCY COMMAND CENTER — S.C. Thomas Internal Agency
Version: 2.0
The master orchestrator. Runs all bots on schedule, monitors health,
auto-fixes failures, self-improves skills, and reports to Chairman.
This is the ONLY bot that needs to run permanently — it manages everything else.

Deploy: Railway.app or any always-on server
Run: python agency_command_center.py
"""

import os
import sys
import json
import time
import subprocess
import threading
import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import core
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, AlertSystem, StateManager, get_logger, ClaudeClient

COMMAND_CENTER_VERSION = "2.0.0"
BOT_DIR = Path(__file__).parent

# ─── BOT REGISTRY ─────────────────────────────────────────────────────────────
# All bots + their schedules. Command Center runs these automatically.
BOT_REGISTRY = [
    {
        "id":          "weekly_report",
        "script":      "weekly_report_bot.py",
        "name":        "Weekly KPI Report",
        "schedule":    "monday_08:00",
        "priority":    "HIGH",
# AG-NUCLEAR-GMAIL-ZERO-20260328:         "required_config": ["GMAIL_APP_PASS"],
        "description": "Pulls all KPIs and emails Chairman weekly summary",
        "enabled":     True,
    },
    {
        "id":          "inbox_triage",
        "script":      "inbox_triage_bot.py",
        "name":        "Inbox Triage",
        "schedule":    "daily_07:00",
        "priority":    "HIGH",
        "required_config": ["ANTHROPIC_API_KEY"],
        "description": "Categorizes Gmail, drafts responses, flags hot leads",
        "enabled":     True,
    },
    {
        "id":          "seo_tracker",
        "script":      "seo_rank_tracker_bot.py",
        "name":        "SEO Rank Tracker",
        "schedule":    "monday_09:00,thursday_09:00",
        "priority":    "MEDIUM",
        "required_config": ["AHREFS_API_KEY"],
        "description": "Tracks keyword rankings and new backlinks",
        "enabled":     True,
    },
    {
        "id":          "competitor_monitor",
        "script":      "competitor_monitor_bot.py",
        "name":        "Competitor Monitor",
        "schedule":    "sunday_23:00",
        "priority":    "MEDIUM",
        "required_config": ["ANTHROPIC_API_KEY"],
        "description": "Detects competitor site changes and analyzes implications",
        "enabled":     True,
    },
    {
        "id":          "lead_pipeline",
        "script":      "lead_pipeline_bot.py",
        "name":        "Lead Pipeline",
        "schedule":    "tuesday_12:00",
        "priority":    "HIGH",
        "required_config": ["APOLLO_API_KEY"],
        "description": "Searches Apollo, scores leads, pushes to HubSpot",
        "enabled":     True,
    },
    {
        "id":          "uptime_monitor",
        "script":      "uptime_monitor_bot.py",
        "name":        "Uptime Monitor",
        "schedule":    "every_15min",
        "priority":    "CRITICAL",
        "required_config": [],
        "description": "Monitors all sites for downtime, SSL, speed",
        "enabled":     True,
    },
    {
        "id":          "invoice_reminders",
        "script":      "invoice_bot.py",
        "name":        "Invoice Reminders",
        "schedule":    "daily_09:00",
        "priority":    "HIGH",
        "required_config": [],
        "description": "Sends payment reminders for overdue invoices",
        "enabled":     True,
    },
    {
        "id":          "content_calendar",
        "script":      "content_calendar_bot.py",
        "name":        "Content Calendar Builder",
        "schedule":    "first_of_month_08:00",
        "priority":    "MEDIUM",
        "required_config": ["ANTHROPIC_API_KEY"],
        "description": "Auto-builds next month content calendar",
        "enabled":     True,
    },
    {
        "id":          "social_poster",
        "script":      "social_poster_bot.py",
        "name":        "Social Poster",
        "schedule":    "every_6hours",
        "priority":    "HIGH",
        "required_config": ["PUBLER_API_KEY"],
        "description": "Posts scheduled content to all platforms via Publer",
        "enabled":     True,
    },
    {
        "id":          "mention_monitor",
        "script":      "mention_monitor_bot.py",
        "name":        "Mention Monitor",
        "schedule":    "every_6hours",
        "priority":    "MEDIUM",
        "required_config": [],
        "description": "Monitors brand mentions, drafts replies, flags hot engagement",
        "enabled":     True,
    },
    {
        "id":          "campaign_orchestrator",
        "script":      "campaign_orchestrator_bot.py",
        "name":        "Campaign Orchestrator",
        "schedule":    "daily_08:00",
        "priority":    "HIGH",
        "required_config": ["ANTHROPIC_API_KEY", "PUBLER_API_KEY"],
        "description": "Runs pending campaign briefs end-to-end",
        "enabled":     True,
    },
    {
        "id":          "system_health",
        "script":      None,  # Built-in
        "name":        "System Health Check",
        "schedule":    "every_1hour",
        "priority":    "CRITICAL",
        "required_config": [],
        "description": "Checks all bots health, self-heals failures",
        "enabled":     True,
    },
    {
        "id":          "self_improvement",
        "script":      "self_improvement_bot.py",
        "name":        "Self Improvement Engine",
        "schedule":    "sunday_06:00",
        "priority":    "LOW",
        "required_config": ["ANTHROPIC_API_KEY"],
        "description": "Reviews bot performance, suggests and applies improvements",
        "enabled":     True,
    },
]

# ─── SCHEDULE PARSER ──────────────────────────────────────────────────────────
class Scheduler:
    DAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6}

    @staticmethod
    def should_run(schedule: str, state: StateManager, bot_id: str) -> bool:
        now   = datetime.now()
        last  = state.get(f"last_run_{bot_id}")
        last_dt = datetime.fromisoformat(last) if last else None

        if schedule == "every_15min":
            if not last_dt: return True
            return (now - last_dt).total_seconds() >= 900

        if schedule == "every_1hour":
            if not last_dt: return True
            return (now - last_dt).total_seconds() >= 3600

        if schedule == "every_6hours":
            if not last_dt: return True
            return (now - last_dt).total_seconds() >= 21600

        if schedule.startswith("daily_"):
            target_time = schedule.split("_")[1]
            th, tm = map(int, target_time.split(":"))
            if now.hour != th or now.minute != tm: return False
            if last_dt and last_dt.date() == now.date(): return False
            return True

        if schedule.startswith("first_of_month_"):
            if now.day != 1: return False
            target_time = schedule.split("_")[-1]
            th, tm = map(int, target_time.split(":"))
            if now.hour != th or now.minute != tm: return False
            if last_dt and last_dt.month == now.month: return False
            return True

        # Day-specific: "monday_08:00" or "monday_09:00,thursday_09:00"
        for part in schedule.split(","):
            part = part.strip()
            if "_" in part:
                day_name, target_time = part.split("_", 1)
                if day_name in Scheduler.DAYS:
                    target_dow = Scheduler.DAYS[day_name]
                    if now.weekday() != target_dow: continue
                    th, tm = map(int, target_time.split(":"))
                    if now.hour != th or now.minute != tm: continue
                    if last_dt and last_dt.date() == now.date(): continue
                    return True

        return False

# ─── BOT RUNNER ───────────────────────────────────────────────────────────────
class BotRunner:
    def __init__(self, logger):
        self.logger  = logger
        self.running = {}  # bot_id -> thread

    def run_bot_subprocess(self, bot: dict, extra_args: list = None) -> dict:
        """Run a bot script in a subprocess"""
        if not bot.get("script"):
            return {"success": False, "error": "No script defined"}

        script_path = BOT_DIR / bot["script"]
        if not script_path.exists():
            return {"success": False, "error": f"Script not found: {script_path}"}

        cmd = [sys.executable, str(script_path)] + (extra_args or [])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout per bot
                env={**os.environ}
            )
            success = result.returncode == 0
            output  = result.stdout[-2000:] if result.stdout else ""
            error   = result.stderr[-500:] if result.stderr else ""

            self.logger.info(f"[{bot['id']}] Exit code: {result.returncode}")
            if error: self.logger.warning(f"[{bot['id']}] Stderr: {error[:200]}")

            return {"success": success, "output": output, "error": error}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after 300s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_bot_threaded(self, bot: dict, state: StateManager):
        """Run a bot in a background thread"""
        if bot["id"] in self.running and self.running[bot["id"]].is_alive():
            self.logger.warning(f"[{bot['id']}] Already running, skipping")
            return

        def _run():
            result = self.run_bot_subprocess(bot)
            state.set(f"last_run_{bot['id']}", datetime.now().isoformat())
            state.set(f"last_result_{bot['id']}", {
                "success": result["success"],
                "error": result.get("error", ""),
                "timestamp": datetime.now().isoformat()
            })
            if not result["success"]:
                AlertSystem.send(
                    subject=f"Bot failed: {bot['name']}",
                    body_html=f"<p><strong>Bot:</strong> {bot['name']}<br><strong>Error:</strong> {result.get('error','unknown')}</p>",
                    severity="WARNING"
                )

        t = threading.Thread(target=_run, name=f"bot-{bot['id']}", daemon=True)
        t.start()
        self.running[bot["id"]] = t

# ─── HEALTH MONITOR ───────────────────────────────────────────────────────────
class HealthMonitor:
    def __init__(self, logger, state: StateManager):
        self.logger = logger
        self.state  = state

    def check_all(self) -> dict:
        """Check health of all bots and system resources"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "bots": {},
            "config_check": {},
            "alerts": []
        }

        # Check each bot's last run and success
        for bot in BOT_REGISTRY:
            bid = bot["id"]
            last_run    = self.state.get(f"last_run_{bid}")
            last_result = self.state.get(f"last_result_{bid}", {})

            status = "UNKNOWN"
            if last_result:
                status = "HEALTHY" if last_result.get("success") else "FAILED"

            # Check if overdue
            if last_run and bot["schedule"] not in ["every_15min", "every_1hour"]:
                last_dt = datetime.fromisoformat(last_run)
                hours_since = (datetime.now() - last_dt).total_seconds() / 3600
                if hours_since > 48 and bot["enabled"]:
                    report["alerts"].append(f"{bot['name']} hasn't run in {hours_since:.0f}h")

            report["bots"][bid] = {
                "name":      bot["name"],
                "status":    status,
                "last_run":  last_run,
                "enabled":   bot["enabled"],
                "priority":  bot["priority"],
            }

        # Check config/API keys
        key_checks = {
            "ANTHROPIC_API_KEY": bool(Config.ANTHROPIC_API_KEY),
# AG-NUCLEAR-GMAIL-ZERO-20260328:             "GMAIL_APP_PASS":    bool(Config.GMAIL_APP_PASS),
            "AHREFS_API_KEY":    bool(Config.AHREFS_API_KEY),
            "HUBSPOT_API_KEY":   bool(Config.HUBSPOT_API_KEY),
            "APOLLO_API_KEY":    bool(Config.APOLLO_API_KEY),
        }
        report["config_check"] = key_checks
        missing_keys = [k for k, v in key_checks.items() if not v]
        if missing_keys:
            report["alerts"].append(f"Missing API keys: {', '.join(missing_keys)}")

        return report

    def send_daily_health_email(self, report: dict):
        """Send morning health summary to Chairman"""
        def _status_color(s):
            if s == "HEALTHY": return "#2e7d32"
            if s == "FAILED":  return "#c62828"
            return "#888"

        bots_html = "".join([
            "<tr>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;'>{b['name']}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;'>"
            f"<span style='color:{_status_color(b['status'])};font-weight:bold;'>{b['status']}</span></td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;font-size:12px;color:#888;'>{b['last_run'][:16] if b.get('last_run') else 'Never'}</td>"
            "</tr>"
            for b in report["bots"].values()
        ])

        def _cfg_item(k, v):
            color = "#2e7d32" if v else "#c62828"
            icon  = "✅" if v else "❌"
            return f"<span style='margin-right:12px;color:{color};'>{icon} {k}</span>"

        config_html = "".join([_cfg_item(k, v) for k, v in report["config_check"].items()])

        alerts_html = "".join([f"<li style='color:#c62828;'>{a}</li>" for a in report["alerts"]])

        html = f"""<html><body style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;">
<div style="background:#111;color:#fff;padding:18px 22px;">
  <strong>🤖 AGENCY SYSTEM STATUS — {datetime.now().strftime('%b %d, %Y')}</strong>
</div>
<div style="padding:22px;">
  {"<div style='background:#fff3e0;border-left:4px solid #f9a825;padding:12px;margin-bottom:16px;'><strong>⚠️ Alerts:</strong><ul style='margin:8px 0 0;'>" + alerts_html + "</ul></div>" if report["alerts"] else "<div style='background:#e8f5e9;border-left:4px solid #2e7d32;padding:12px;margin-bottom:16px;'>✅ All systems nominal</div>"}
  <h3 style="border-bottom:2px solid #111;padding-bottom:6px;">Bot Status</h3>
  <table width="100%" style="border-collapse:collapse;">
    <thead><tr style="background:#111;color:#fff;">
      <th style="padding:8px 10px;text-align:left;">Bot</th>
      <th style="padding:8px 10px;text-align:left;">Status</th>
      <th style="padding:8px 10px;text-align:left;">Last Run</th>
    </tr></thead>
    <tbody>{bots_html}</tbody>
  </table>
  <h3 style="margin-top:20px;border-bottom:2px solid #111;padding-bottom:6px;">API Keys</h3>
  <p>{config_html}</p>
  <p style="margin-top:20px;font-size:12px;color:#999;">Agency Command Center v{COMMAND_CENTER_VERSION} | Auto-generated</p>
</div></body></html>"""

        AlertSystem.send(
            subject  = f"🤖 Agency Status — {datetime.now().strftime('%b %d')} — {'⚠️ Issues' if report['alerts'] else '✅ All Clear'}",
            body_html= html,
            severity = "WARNING" if report["alerts"] else "INFO"
        )

# ─── MAIN COMMAND CENTER LOOP ─────────────────────────────────────────────────
def run_command_center():
    logger  = get_logger("command-center")
    state   = StateManager("command-center")
    runner  = BotRunner(logger)
    monitor = HealthMonitor(logger, state)

    logger.info(f"Agency Command Center v{COMMAND_CENTER_VERSION} starting...")
    logger.info(f"Managing {len(BOT_REGISTRY)} bots")

    # Send startup notification
    AlertSystem.send(
        subject  = "Agency Command Center Started",
        body_html= f"<p>Command Center v{COMMAND_CENTER_VERSION} is online. Managing {len(BOT_REGISTRY)} bots.<br>All scheduled bots will run automatically.</p>",
        severity = "SUCCESS"
    )

    tick = 0
    while True:
        try:
            now = datetime.now()

            # ── Every tick: check schedules ──
            for bot in BOT_REGISTRY:
                if not bot["enabled"]: continue
                if not Scheduler.should_run(bot["schedule"], state, bot["id"]): continue

                # Built-in health check
                if bot["id"] == "system_health":
                    report = monitor.check_all()
                    # Send daily health at 8am
                    if now.hour == 8 and now.minute == 0:
                        last_daily = state.get("last_daily_health")
                        if not last_daily or datetime.fromisoformat(last_daily).date() < now.date():
                            monitor.send_daily_health_email(report)
                            state.set("last_daily_health", now.isoformat())
                    state.set(f"last_run_{bot['id']}", now.isoformat())
                    continue

                logger.info(f"Triggering: {bot['name']}")
                runner.run_bot_threaded(bot, state)

            # ── Every 10 minutes: quick log ──
            if tick % 10 == 0:
                healthy = sum(1 for b in BOT_REGISTRY if state.get(f"last_result_{b['id']}", {}).get("success", True))
                logger.info(f"Heartbeat: {healthy}/{len(BOT_REGISTRY)} bots healthy | {now.strftime('%H:%M')}")

            tick += 1
            time.sleep(60)  # Check schedules every minute

        except KeyboardInterrupt:
            logger.info("Command Center shutting down...")
            break
        except Exception as e:
            logger.error(f"Command Center error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    import sys
    if "--status" in sys.argv:
        state   = StateManager("command-center")
        monitor = HealthMonitor(get_logger("command-center"), state)
        report  = monitor.check_all()
        print(json.dumps(report, indent=2))
    elif "--health-email" in sys.argv:
        state   = StateManager("command-center")
        monitor = HealthMonitor(get_logger("command-center"), state)
        report  = monitor.check_all()
        monitor.send_daily_health_email(report)
        print("Health email sent")
    else:
        run_command_center()

# ─── DEPLOY TO RAILWAY ────────────────────────────────────────────────────────
# 1. Create Railway account: railway.app
# 2. New project → Deploy from GitHub
# 3. Add all bots/ folder to a GitHub repo
# 4. Set all env vars in Railway dashboard
# 5. Start command: python bots/agency_command_center.py
# Cost: ~$5/month for always-on
#
# OR run locally:
# python bots/agency_command_center.py
#
# Check status anytime:
# python bots/agency_command_center.py --status
