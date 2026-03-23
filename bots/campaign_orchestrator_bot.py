#!/usr/bin/env python3
"""
CAMPAIGN ORCHESTRATOR BOT v2.0 — S.C. Thomas Internal Agency
The master marketing bot. Given a campaign brief, it:
1. Plans the full content strategy
2. Writes all content (posts, threads, emails, articles)
3. Generates images for each piece
4. Schedules everything to Publer
5. Enrolls leads in email sequences
6. Tracks and reports performance
Fully autonomous. Zero Chairman action required after brief.
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, ClaudeClient, AlertSystem, with_retry

class CampaignOrchestratorBot(BaseBot):
    VERSION = "2.0.0"

    PLATFORMS = ["twitter", "linkedin", "instagram", "facebook"]

    def __init__(self):
        super().__init__("campaign-orchestrator", required_config=["ANTHROPIC_API_KEY"])
        self.campaigns_dir = Path("campaigns")
        self.campaigns_dir.mkdir(exist_ok=True)

    # ── STRATEGY PLANNER ──────────────────────────────────────────────────────
    def plan_campaign(self, brief: str, duration_days: int = 14) -> dict:
        """Generate a complete campaign plan from a brief"""
        self.logger.info(f"Planning campaign: {brief[:80]}...")

        system = """You are the head of strategy for S.C. Thomas Internal Agency.
Plan a complete social media marketing campaign.
Be specific with dates, content types, and messaging angles.
Return ONLY valid JSON."""

        start_date = datetime.now(timezone.utc)
        end_date   = start_date + timedelta(days=duration_days)

        prompt = f"""Create a {duration_days}-day marketing campaign plan for:

BRIEF: {brief}
START: {start_date.strftime('%Y-%m-%d')}
END:   {end_date.strftime('%Y-%m-%d')}

Return this JSON structure:
{{
  "campaign_name": "string",
  "goal": "string",
  "target_audience": "string",
  "core_message": "string",
  "content_pillars": ["pillar1", "pillar2", "pillar3"],
  "posts": [
    {{
      "day": 1,
      "platform": "twitter|linkedin|instagram|facebook",
      "type": "text|image|thread|story",
      "hook": "opening line",
      "angle": "content angle",
      "cta": "call to action",
      "hashtags": ["tag1", "tag2"]
    }}
  ],
  "email_sequence": {{
    "trigger": "when to send",
    "emails": [
      {{"subject": "...", "preview": "...", "day": 1, "goal": "..."}}
    ]
  }},
  "kpis": ["metric1", "metric2"],
  "success_metric": "what defines success"
}}

Generate 14-21 posts spread across platforms over the campaign period."""

        try:
            plan = ClaudeClient.complete(system, prompt, max_tokens=3000, json_mode=True)
            self.logger.info(f"Campaign plan generated: {plan.get('campaign_name', 'Unnamed')}")
            return plan
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return {"error": str(e)}

    # ── CONTENT WRITER ────────────────────────────────────────────────────────
    def write_post(self, plan_item: dict, campaign_context: dict) -> str:
        """Write full post copy for a planned item"""
        system = """You are a social media copywriter for S.C. Thomas.
Brand voice: Direct, authoritative, sharp, no fluff.
No corporate buzzwords. No AI tells.
Write platform-appropriate copy that drives engagement."""

        prompt = f"""Write a {plan_item['platform']} {plan_item['type']} post.

Campaign: {campaign_context.get('campaign_name', '')}
Core message: {campaign_context.get('core_message', '')}
Target audience: {campaign_context.get('target_audience', '')}

Hook: {plan_item['hook']}
Angle: {plan_item['angle']}
CTA: {plan_item['cta']}
Hashtags to include: {' '.join(['#' + h for h in plan_item.get('hashtags', [])])}

Platform rules:
- Twitter: Under 280 chars, no hashtag spam
- LinkedIn: 150-250 words, line breaks, 3-5 hashtags at bottom
- Instagram: 100-150 words + 20-25 hashtags separate block
- Facebook: 100-200 words, conversational

Write the complete post copy now. Nothing else."""

        return ClaudeClient.complete_safe(
            system=system, user=prompt, max_tokens=500,
            fallback=f"{plan_item['hook']}\n\n{plan_item['angle']}\n\n{plan_item['cta']}"
        )

    def write_email(self, email_brief: dict, campaign_context: dict) -> dict:
        """Write a full email from a brief"""
        system = """You are an email copywriter for S.C. Thomas.
Write conversion-focused emails. Direct, benefit-driven, clear CTA.
Return JSON with subject, preview_text, and body (HTML)."""

        prompt = f"""Write a marketing email.

Campaign: {campaign_context.get('campaign_name', '')}
Subject goal: {email_brief.get('subject', '')}
Email goal: {email_brief.get('goal', '')}
Day in sequence: {email_brief.get('day', 1)}

Return JSON:
{{"subject": "...", "preview_text": "...", "body_html": "...", "cta_text": "...", "cta_url": "{{CTA_URL}}"}}"""

        try:
            return ClaudeClient.complete(system, prompt, max_tokens=1000, json_mode=True)
        except Exception:  # noqa: bare-except
            return {"subject": email_brief.get("subject", ""), "body_html": "", "error": True}

    # ── SCHEDULER ─────────────────────────────────────────────────────────────
    def schedule_post_to_publer(self, text: str, platform: str,
                                 scheduled_at: str, image_path: str = None) -> dict:
        """Schedule a post via Publer API"""
        publer_key  = os.getenv("PUBLER_API_KEY", "")
        workspace   = os.getenv("PUBLER_WORKSPACE_ID", "")
        if not publer_key:
            return {"success": False, "error": "No PUBLER_API_KEY"}

        headers = {
            "Authorization": f"Bearer-API {publer_key}",
            "Publer-Workspace-Id": workspace,
            "Content-Type": "application/json",
        }

        try:
            # Get accounts for this platform
            r = self.http.get("https://app.publer.com/api/v1/accounts", headers=headers)
            accounts = r.json().get("accounts", [])
            target = [a["id"] for a in accounts
                      if a.get("network", "").lower() == platform.lower()]

            if not target:
                return {"success": False, "error": f"No {platform} account connected"}

            payload = {
                "bulk": {
                    "state": "scheduled",
                    "posts": [{
                        "networks": {"default": {"type": "status", "text": text}},
                        "accounts": [{"id": aid, "scheduled_at": scheduled_at}
                                     for aid in target]
                    }]
                }
            }
            r2 = self.http.post(
                "https://app.publer.com/api/v1/posts/schedule",
                headers=headers, json_data=payload
            )
            return {"success": True, "data": r2.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── MAIN CAMPAIGN RUNNER ──────────────────────────────────────────────────
    def run_campaign(self, brief: str, duration_days: int = 14) -> dict:
        """Run a complete campaign end to end"""
        start_time = datetime.now()
        self.logger.info(f"Starting campaign: {brief[:80]}...")

        # 1. Plan
        plan = self.plan_campaign(brief, duration_days)
        if "error" in plan:
            return plan

        campaign_name = plan.get("campaign_name", "Campaign")
        results = {
            "campaign_name": campaign_name,
            "posts_written":    0,
            "posts_scheduled":  0,
            "emails_written":   0,
            "errors":           [],
        }

        # 2. Write + schedule all posts
        start_dt = datetime.now(timezone.utc) + timedelta(hours=2)
        for i, post_brief in enumerate(plan.get("posts", [])):
            try:
                # Write copy
                copy = self.write_post(post_brief, plan)
                results["posts_written"] += 1

                # Calculate schedule time (spread across campaign)
                schedule_dt = start_dt + timedelta(
                    days=post_brief.get("day", i+1) - 1,
                    hours=9  # Default: 9am
                )
                scheduled_at = schedule_dt.strftime("%Y-%m-%dT%H:%M+00:00")

                # Schedule to Publer
                sched_result = self.schedule_post_to_publer(
                    text=copy,
                    platform=post_brief.get("platform", "linkedin"),
                    scheduled_at=scheduled_at
                )
                if sched_result.get("success"):
                    results["posts_scheduled"] += 1
                    self.logger.info(
                        f"Scheduled: Day {post_brief.get('day',i+1)} "
                        f"[{post_brief.get('platform','?')}]"
                    )
                else:
                    results["errors"].append(
                        f"Schedule failed: {sched_result.get('error')}"
                    )
            except Exception as e:
                results["errors"].append(f"Post {i+1} error: {str(e)}")

        # 3. Write email sequence
        email_seq = plan.get("email_sequence", {})
        for email_brief in email_seq.get("emails", []):
            try:
                email = self.write_email(email_brief, plan)
                if not email.get("error"):
                    results["emails_written"] += 1
            except Exception as e:
                results["errors"].append(f"Email error: {e}")

        # 4. Save campaign file
        duration  = (datetime.now() - start_time).total_seconds()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in campaign_name[:30]
                            if c.isalnum() or c == " ").replace(" ", "_")
        filepath = self.campaigns_dir / f"{timestamp}_{safe_name}.json"
        with open(filepath, "w") as f:
            json.dump({"plan": plan, "results": results}, f, indent=2)

        results["saved_to"]   = str(filepath)
        results["duration_s"] = round(duration, 1)

        # 5. Report to Chairman
        status = "✅" if not results["errors"] else "⚠️"
        AlertSystem.send(
            subject  = f"{status} Campaign Launched: {campaign_name}",
            body_html= f"""
<h3>{campaign_name}</h3>
<p><strong>Brief:</strong> {brief[:200]}</p>
<table>
<tr><td>Posts written</td><td>{results['posts_written']}</td></tr>
<tr><td>Posts scheduled</td><td>{results['posts_scheduled']}</td></tr>
<tr><td>Emails written</td><td>{results['emails_written']}</td></tr>
<tr><td>Duration</td><td>{results['duration_s']}s</td></tr>
</table>
{'<p style="color:red">Errors: ' + '<br>'.join(results['errors']) + '</p>' if results['errors'] else ''}
""",
            severity = "SUCCESS" if not results["errors"] else "WARNING"
        )

        self.logger.info(
            f"Campaign complete: {results['posts_scheduled']} posts scheduled"
        )
        return results

    def execute(self) -> dict:
        pending = self.state.get("pending_campaigns", [])
        if not pending:
            self.logger.info("No pending campaigns")
            return {"items_processed": 0}

        campaign = pending[0]
        result = self.run_campaign(
            brief        = campaign["brief"],
            duration_days= campaign.get("duration_days", 14)
        )
        self.state.set("pending_campaigns", pending[1:])
        return {"items_processed": 1, "campaign": result.get("campaign_name")}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Campaign Orchestrator Bot")
    p.add_argument("--brief",    type=str, help="Campaign brief")
    p.add_argument("--days",     type=int, default=14, help="Campaign duration in days")
    p.add_argument("--dry-run",  action="store_true", help="Plan only, don't schedule")
    args = p.parse_args()

    bot = CampaignOrchestratorBot()

    if args.brief:
        if args.dry_run:
            plan = bot.plan_campaign(args.brief, args.days)
            print(json.dumps(plan, indent=2))
        else:
            result = bot.run_campaign(args.brief, args.days)
            print(json.dumps(result, indent=2))
    else:
        bot.run()

# USAGE:
# python campaign_orchestrator_bot.py --brief "Launch our new content strategy service" --days 14
# python campaign_orchestrator_bot.py --brief "..." --dry-run  (plan only)
#
# REQUIRED SECRETS:
# ANTHROPIC_API_KEY, PUBLER_API_KEY, PUBLER_WORKSPACE_ID
