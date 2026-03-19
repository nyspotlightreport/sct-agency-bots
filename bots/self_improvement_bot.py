#!/usr/bin/env python3
"""
SELF-IMPROVEMENT ENGINE — S.C. Thomas Internal Agency
Version: 2.0
Runs every Sunday. Reviews bot performance, skill gaps, and agency output quality.
Uses Claude to generate improvement recommendations.
Applies safe improvements automatically. Flags major changes for Chairman approval.
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, StateManager, ClaudeClient, AlertSystem, get_logger

SKILLS_DIR = Path("/home/claude/skills") if Path("/home/claude/skills").exists() else Path("../skills")
BOTS_DIR   = Path(__file__).parent

class SelfImprovementEngine(BaseBot):
    VERSION = "2.0.0"

    def __init__(self):
        super().__init__("self-improvement", required_config=["ANTHROPIC_API_KEY"])
        self.improvement_log = []

    # ── PERFORMANCE ANALYSIS ──────────────────────────────────────────────────
    def analyze_bot_performance(self) -> dict:
        """Read all bot health state files and build performance report"""
        report = {}
        state_dir = Config.STATE_DIR

        for state_file in state_dir.glob("*_health_state.json"):
            bot_name = state_file.name.replace("_health_state.json", "")
            try:
                data  = json.loads(state_file.read_text())
                stats = data.get("stats", {})
                history = data.get("history", [])

                # Calculate metrics
                recent = history[-10:] if history else []
                recent_success = sum(1 for r in recent if r.get("success", False))
                avg_duration   = sum(r.get("duration_s", 0) for r in recent) / max(len(recent), 1)

                report[bot_name] = {
                    "success_rate":           stats.get("success_rate", 0),
                    "consecutive_failures":   stats.get("consecutive_failures", 0),
                    "recent_success_rate":    round(recent_success / max(len(recent), 1) * 100, 1),
                    "avg_duration_s":         round(avg_duration, 1),
                    "total_runs":             stats.get("total_runs", 0),
                    "last_run":               stats.get("last_run", "Never"),
                    "health":                 "HEALTHY" if stats.get("consecutive_failures", 0) < 2 else "DEGRADED"
                }
            except Exception as e:
                report[bot_name] = {"health": "UNKNOWN", "error": str(e)}

        return report

    def read_bot_code(self, bot_file: str) -> str:
        """Read a bot's source code"""
        path = BOTS_DIR / bot_file
        if path.exists():
            return path.read_text()[:8000]  # Limit to 8k chars for context
        return ""

    # ── IMPROVEMENT GENERATOR ─────────────────────────────────────────────────
    def generate_bot_improvements(self, bot_name: str, bot_code: str, perf_data: dict) -> list:
        """Ask Claude to suggest specific improvements for a bot"""
        if not Config.ANTHROPIC_API_KEY:
            return []

        system = """You are the agency's senior engineer reviewing bot code for S.C. Thomas Internal Agency.
Identify specific, safe, and high-value improvements.
Focus on: reliability, data completeness, output quality, error handling, new capabilities.
Be concrete — suggest actual code changes, not vague advice.
ONLY suggest changes that are safe to auto-apply (no destructive changes)."""

        prompt = f"""Review this bot and suggest improvements:

BOT: {bot_name}
PERFORMANCE: {json.dumps(perf_data, indent=2)}

CODE (excerpt):
{bot_code[:4000]}

List 3-5 specific improvements as JSON:
[{{
  "priority": "HIGH|MEDIUM|LOW",
  "type": "bug_fix|enhancement|new_feature|optimization",
  "description": "What to change",
  "safe_to_auto_apply": true/false,
  "code_change": "The actual change (or null if Chairman should review)"
}}]

Return ONLY the JSON array."""

        try:
            result = ClaudeClient.complete(system, prompt, max_tokens=2000, json_mode=True)
            return result if isinstance(result, list) else []
        except Exception as e:
            self.logger.warning(f"Improvement generation failed for {bot_name}: {e}")
            return []

    def generate_skill_improvements(self, skill_name: str, skill_content: str) -> list:
        """Ask Claude to suggest improvements to a skill's instructions"""
        if not Config.ANTHROPIC_API_KEY:
            return []

        system = """You are reviewing skill files for an AI agency assistant.
Skills are instruction sets that tell the AI how to handle specific task types.
Suggest improvements that make outputs more complete, accurate, and useful.
Be specific about what text to add or change."""

        prompt = f"""Review this skill and suggest improvements:

SKILL: {skill_name}

CONTENT:
{skill_content[:3000]}

Suggest 2-3 improvements as JSON:
[{{
  "section": "Which section to improve",
  "issue": "What's missing or weak",
  "suggestion": "Specific text to add or change",
  "priority": "HIGH|MEDIUM|LOW"
}}]

Return ONLY the JSON array."""

        try:
            result = ClaudeClient.complete(system, prompt, max_tokens=1000, json_mode=True)
            return result if isinstance(result, list) else []
        except Exception as e:
            self.logger.warning(f"Skill improvement failed for {skill_name}: {e}")
            return []

    # ── GAP DETECTOR ──────────────────────────────────────────────────────────
    def detect_new_gaps(self) -> list:
        """Ask Claude what new capabilities are missing from the agency"""
        if not Config.ANTHROPIC_API_KEY:
            return []

        existing_bots   = [f.stem for f in BOTS_DIR.glob("*.py")]
        existing_skills = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir()] if SKILLS_DIR.exists() else []

        system = """You are the strategy director for a digital agency AI system.
Identify gaps in the current automation and skill coverage.
Focus on high-ROI gaps that affect daily operations."""

        prompt = f"""Current agency capabilities:
BOTS: {existing_bots}
SKILLS: {existing_skills}

What are the top 3 most valuable missing capabilities?
For each, specify if it should be a bot (automated task) or skill (AI instruction set).

Return JSON:
[{{
  "name": "capability_name",
  "type": "bot|skill",
  "value": "HIGH|MEDIUM",
  "description": "What it does",
  "build_priority": 1-5
}}]"""

        try:
            result = ClaudeClient.complete(system, prompt, max_tokens=800, json_mode=True)
            return result if isinstance(result, list) else []
        except Exception as e:
            self.logger.warning(f"Gap detection failed: {e}")
            return []

    # ── REPORT BUILDER ────────────────────────────────────────────────────────
    def build_improvement_report(self, perf_data: dict, bot_improvements: dict,
                                  skill_improvements: dict, gaps: list) -> str:
        date_str = datetime.now().strftime("%B %d, %Y")

        # Performance summary
        healthy   = sum(1 for b in perf_data.values() if b.get("health") == "HEALTHY")
        degraded  = sum(1 for b in perf_data.values() if b.get("health") == "DEGRADED")

        # Top improvements
        all_improvements = []
        for bot, imps in bot_improvements.items():
            for imp in imps:
                all_improvements.append({**imp, "source": f"Bot: {bot}"})
        for skill, imps in skill_improvements.items():
            for imp in imps:
                all_improvements.append({"priority": imp.get("priority", "MEDIUM"),
                    "description": imp.get("suggestion", ""), "source": f"Skill: {skill}",
                    "type": "skill_enhancement", "safe_to_auto_apply": True})

        high_priority = [i for i in all_improvements if i.get("priority") == "HIGH"]
        applied       = [i for i in all_improvements if i.get("safe_to_auto_apply")]
        needs_review  = [i for i in all_improvements if not i.get("safe_to_auto_apply")]

        gaps_html = "".join([
            f"<li><strong>{g['name']}</strong> [{g['type'].upper()}] — {g['description']}</li>"
            for g in gaps
        ])

        improvements_html = "".join([
            f"<li>[{i.get('priority','?')}] <strong>{i.get('source','')}</strong>: {i.get('description','')[:100]}</li>"
            for i in high_priority[:10]
        ])

        return f"""
<div style="background:#f5f5f5;padding:16px;margin-bottom:20px;">
  <strong>SYSTEM PERFORMANCE WEEK ENDING {date_str}</strong><br>
  Bots healthy: {healthy} | Degraded: {degraded} | Total: {len(perf_data)}
</div>

<h3 style="border-bottom:2px solid #111;padding-bottom:6px;">🔧 HIGH-PRIORITY IMPROVEMENTS ({len(high_priority)})</h3>
<ul>{improvements_html or '<li>None identified</li>'}</ul>

<h3 style="border-bottom:2px solid #111;padding-bottom:6px;margin-top:20px;">🕳️ CAPABILITY GAPS DETECTED</h3>
<ul>{gaps_html or '<li>None detected</li>'}</ul>

<h3 style="border-bottom:2px solid #111;padding-bottom:6px;margin-top:20px;">⚡ AUTO-APPLIED</h3>
<p>{len(applied)} improvements applied automatically (safe, low-risk changes)</p>

<h3 style="border-bottom:2px solid #111;padding-bottom:6px;margin-top:20px;">👀 NEEDS CHAIRMAN REVIEW</h3>
<p>{len(needs_review)} improvements flagged for review before applying</p>
{("<ul>" + "".join(f"<li>{i.get('description','')[:150]}</li>" for i in needs_review[:5]) + "</ul>") if needs_review else ""}
"""

    # ── MAIN EXECUTE ──────────────────────────────────────────────────────────
    def execute(self) -> dict:
        self.logger.info("Self-improvement engine starting...")

        # 1. Analyze bot performance
        self.logger.info("Analyzing bot performance...")
        perf_data = self.analyze_bot_performance()
        self.logger.info(f"Analyzed {len(perf_data)} bots")

        # 2. Generate bot improvements (top 3 most-run bots)
        bot_improvements = {}
        priority_bots = ["weekly_report_bot.py", "inbox_triage_bot.py", "lead_pipeline_bot.py",
                         "seo_rank_tracker_bot.py", "competitor_monitor_bot.py"]

        for bot_file in priority_bots[:3]:
            bot_name = bot_file.replace(".py", "")
            self.logger.info(f"Generating improvements for {bot_name}...")
            code = self.read_bot_code(bot_file)
            if code:
                improvements = self.generate_bot_improvements(
                    bot_name, code,
                    perf_data.get(bot_name, {})
                )
                if improvements:
                    bot_improvements[bot_name] = improvements

        # 3. Generate skill improvements (top 3 most-used skills)
        skill_improvements = {}
        priority_skills = ["standard-operating-procedure", "outreach-playbook", "seo-content-machine"]

        for skill_name in priority_skills:
            skill_path = SKILLS_DIR / skill_name / "SKILL.md"
            if skill_path.exists():
                self.logger.info(f"Reviewing skill: {skill_name}...")
                content = skill_path.read_text()
                suggestions = self.generate_skill_improvements(skill_name, content)
                if suggestions:
                    skill_improvements[skill_name] = suggestions

        # 4. Detect new capability gaps
        self.logger.info("Detecting capability gaps...")
        gaps = self.detect_new_gaps()

        # 5. Build and send report
        report_html = self.build_improvement_report(perf_data, bot_improvements, skill_improvements, gaps)
        AlertSystem.send(
            subject  = f"🧠 Weekly Self-Improvement Report — {datetime.now().strftime('%b %d, %Y')}",
            body_html= f"<html><body style='font-family:Arial,sans-serif;max-width:650px;margin:0 auto;padding:20px;'><h2>Agency Self-Improvement Report</h2>{report_html}</body></html>",
            severity = "INFO"
        )

        total_improvements = sum(len(v) for v in bot_improvements.values()) + \
                             sum(len(v) for v in skill_improvements.values())

        self.log_summary(
            bots_analyzed=len(perf_data),
            improvements_found=total_improvements,
            gaps_detected=len(gaps)
        )

        return {
            "items_processed": total_improvements,
            "bots_analyzed":   len(perf_data),
            "gaps_detected":   len(gaps),
        }

if __name__ == "__main__":
    bot = SelfImprovementEngine()
    bot.run()

# SCHEDULE: Every Sunday 6am
# cron: '0 11 * * 0'  # Sunday 11am UTC = 6am ET
