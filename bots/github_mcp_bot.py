#!/usr/bin/env python3
"""
GITHUB MCP BOT v1.0 — S.C. Thomas Internal Agency
Connects to GitHub MCP server to manage the sct-agency-bots repo.
- Monitor workflow runs and alert on failures
- Auto-create issues for bot errors
- Track repo health and deployment status
- Push new bot code automatically
Schedule: Every 30 minutes + on-demand
"""
import os, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, AlertSystem, with_retry

class GitHubMCPBot(BaseBot):
    VERSION = "1.0.0"
    API = "https://api.github.com"
    REPO = "nyspotlightreport/sct-agency-bots"

    def __init__(self):
        super().__init__("github-mcp")
        self.token = os.getenv("GITHUB_TOKEN", "")

    @property
    def headers(self):
        h = {"Accept": "application/vnd.github.v3+json",
             "User-Agent": "SCT-Agency-Bot/1.0"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    @with_retry(max_retries=2, delay=2.0)
    def get_workflow_runs(self, limit: int = 20) -> list:
        url = f"{self.API}/repos/{self.REPO}/actions/runs?per_page={limit}"
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("workflow_runs", [])

    @with_retry(max_retries=2, delay=2.0)
    def get_repo_info(self) -> dict:
        req = urllib.request.Request(
            f"{self.API}/repos/{self.REPO}", headers=self.headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    @with_retry(max_retries=2, delay=2.0)
    def create_issue(self, title: str, body: str) -> dict:
        payload = json.dumps({"title": title, "body": body}).encode()
        req = urllib.request.Request(
            f"{self.API}/repos/{self.REPO}/issues",
            data=payload, headers=self.headers, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    @with_retry(max_retries=2, delay=2.0)
    def get_secrets_list(self) -> list:
        """List secret names (values are never exposed)"""
        req = urllib.request.Request(
            f"{self.API}/repos/{self.REPO}/actions/secrets",
            headers=self.headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("secrets", [])

    def analyze_runs(self, runs: list) -> dict:
        """Analyze recent workflow runs for failures"""
        total     = len(runs)
        successes = sum(1 for r in runs if r.get("conclusion") == "success")
        failures  = [r for r in runs if r.get("conclusion") == "failure"]
        pending   = [r for r in runs if r.get("status") in ("in_progress","queued")]

        return {
            "total":     total,
            "successes": successes,
            "failures":  len(failures),
            "pending":   len(pending),
            "failed_names": [r["name"] for r in failures[:5]],
            "health_pct": round(successes / total * 100) if total else 0,
        }

    def execute(self) -> dict:
        runs      = self.get_workflow_runs(20)
        analysis  = self.analyze_runs(runs)
        repo_info = self.get_repo_info()

        # Alert on failures
        if analysis["failures"] > 0:
            failed = ", ".join(analysis["failed_names"])
            AlertSystem.send(
                subject  = f"⚠️ Bot Failures: {analysis['failures']} workflow(s) failed",
                body_html= f"""
<h3>GitHub Workflow Failures Detected</h3>
<p><strong>Failed:</strong> {failed}</p>
<p><strong>Health:</strong> {analysis['health_pct']}% ({analysis['successes']}/{analysis['total']} runs succeeded)</p>
<p><a href="https://github.com/{self.REPO}/actions">View on GitHub</a></p>""",
                severity = "WARNING"
            )

        self.log_summary(
            runs_checked=analysis["total"],
            failures=analysis["failures"],
            health_pct=analysis["health_pct"]
        )
        return analysis

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--status",  action="store_true", help="Show repo status")
    p.add_argument("--runs",    action="store_true", help="Show recent runs")
    p.add_argument("--secrets", action="store_true", help="List secrets")
    args = p.parse_args()

    bot = GitHubMCPBot()
    if args.runs:
        runs     = bot.get_workflow_runs(10)
        analysis = bot.analyze_runs(runs)
        print(f"Health: {analysis['health_pct']}% | "
              f"Successes: {analysis['successes']} | "
              f"Failures: {analysis['failures']}")
        for r in runs[:5]:
            icon = "✅" if r.get("conclusion")=="success" else "❌" if r.get("conclusion")=="failure" else "⏳"
            print(f"  {icon} {r['name']}: {r.get('conclusion') or r.get('status')} ({r['created_at'][:10]})")
    elif args.secrets:
        secrets = bot.get_secrets_list()
        print(f"Secrets ({len(secrets)}):")
        for s in secrets:
            print(f"  ✅ {s['name']}")
    else:
        result = bot.run()
        print(json.dumps(result, indent=2))

# OPTIONAL SECRET: GITHUB_TOKEN (fine-grained PAT with repo+actions scope)
# Without it: reads public data. With it: can create issues + manage repo.
# Get at: github.com/settings/tokens/new
