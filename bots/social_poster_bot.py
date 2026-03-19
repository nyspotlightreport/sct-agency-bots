#!/usr/bin/env python3
"""
SOCIAL POSTER BOT v2.0 — S.C. Thomas Internal Agency
Posts to ALL platforms via Publer API: Twitter/X, LinkedIn, Instagram,
Facebook, TikTok, Pinterest, YouTube, Threads, Bluesky + more.
Runs on schedule OR triggered with content. Fully autonomous.
"""
import sys, os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, with_retry, get_logger

class SocialPosterBot(BaseBot):
    VERSION = "2.0.0"
    BASE_URL = "https://app.publer.com/api/v1"

    def __init__(self):
        super().__init__("social-poster", required_config=["PUBLER_API_KEY"])
        self.api_key    = os.getenv("PUBLER_API_KEY", "")
        self.workspace  = os.getenv("PUBLER_WORKSPACE_ID", "")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer-API {self.api_key}",
            "Publer-Workspace-Id": self.workspace,
            "Content-Type": "application/json",
        }

    @with_retry(max_retries=3, delay=2.0)
    def get_workspaces(self) -> list:
        r = self.http.get(f"{self.BASE_URL}/workspaces", headers=self.headers)
        return r.json().get("workspaces", [])

    @with_retry(max_retries=3, delay=2.0)
    def get_accounts(self) -> list:
        r = self.http.get(f"{self.BASE_URL}/accounts", headers=self.headers)
        return r.json().get("accounts", [])

    @with_retry(max_retries=3, delay=2.0)
    def schedule_post(self, text: str, account_ids: list,
                      scheduled_at: str = None, media_ids: list = None,
                      network_overrides: dict = None) -> dict:
        """Schedule a post to one or more accounts"""
        if not scheduled_at:
            # Default to 30 min from now
            dt = datetime.now(timezone.utc) + timedelta(minutes=30)
            scheduled_at = dt.strftime("%Y-%m-%dT%H:%M+00:00")

        accounts = []
        for aid in account_ids:
            acct = {"id": aid, "scheduled_at": scheduled_at}
            if media_ids:
                acct["media"] = [{"id": mid} for mid in media_ids]
            accounts.append(acct)

        payload = {
            "bulk": {
                "state": "scheduled",
                "posts": [{
                    "networks": network_overrides or {"default": {"type": "status", "text": text}},
                    "accounts": accounts
                }]
            }
        }

        r = self.http.post(f"{self.BASE_URL}/posts/schedule", headers=self.headers, json_data=payload)
        return r.json()

    @with_retry(max_retries=3, delay=2.0)
    def publish_now(self, text: str, account_ids: list, media_ids: list = None) -> dict:
        """Publish immediately to accounts"""
        accounts = [{"id": aid} for aid in account_ids]
        if media_ids:
            for a in accounts:
                a["media"] = [{"id": mid} for mid in media_ids]

        payload = {
            "bulk": {
                "state": "publish",
                "posts": [{
                    "networks": {"default": {"type": "status", "text": text}},
                    "accounts": accounts
                }]
            }
        }
        r = self.http.post(f"{self.BASE_URL}/posts/schedule/publish",
                           headers=self.headers, json_data=payload)
        return r.json()

    @with_retry(max_retries=3, delay=2.0)
    def upload_media_from_url(self, url: str) -> str:
        """Upload media from URL, return media ID"""
        payload = {"media": [{"url": url, "source": "upload"}],
                   "type": "single", "direct_upload": False}
        r = self.http.post(f"{self.BASE_URL}/media/from-url",
                           headers=self.headers, json_data=payload)
        data = r.json()
        # Poll for job completion
        job_id = data.get("job_id")
        if job_id:
            for _ in range(10):
                import time; time.sleep(2)
                jr = self.http.get(f"{self.BASE_URL}/job_status/{job_id}",
                                   headers=self.headers)
                jdata = jr.json()
                if jdata.get("data", {}).get("status") == "complete":
                    return jdata.get("data", {}).get("result", {}).get("media_id", "")
        return data.get("media_id", "")

    def get_all_account_ids_by_platform(self, platform: str = None) -> list:
        """Get account IDs, optionally filtered by platform"""
        accounts = self.get_accounts()
        if platform:
            return [a["id"] for a in accounts
                    if a.get("network", "").lower() == platform.lower()]
        return [a["id"] for a in accounts]

    def post_to_all_platforms(self, text: str, scheduled_at: str = None,
                               platforms: list = None) -> dict:
        """Post content to all or specified platforms"""
        accounts = self.get_accounts()
        if platforms:
            target = [a["id"] for a in accounts
                      if a.get("network", "").lower() in [p.lower() for p in platforms]]
        else:
            target = [a["id"] for a in accounts]

        if not target:
            return {"success": False, "error": "No accounts found"}

        return self.schedule_post(text, target, scheduled_at)

    def execute(self) -> dict:
        """
        Default execute: pull pending content from state and post it.
        Or override externally for custom flows.
        """
        pending = self.state.get("pending_posts", [])
        if not pending:
            self.logger.info("No pending posts in queue")
            return {"items_processed": 0}

        posted = 0
        failed = 0
        for post in pending[:5]:  # Max 5 per run
            try:
                result = self.post_to_all_platforms(
                    text        = post["text"],
                    scheduled_at= post.get("scheduled_at"),
                    platforms   = post.get("platforms")
                )
                if result.get("success") is not False:
                    posted += 1
                    self.logger.info(f"Posted: {post['text'][:50]}...")
                else:
                    failed += 1
                    self.logger.error(f"Failed: {result}")
            except Exception as e:
                failed += 1
                self.logger.error(f"Post error: {e}")

        # Remove processed posts
        self.state.set("pending_posts", pending[5:])
        self.log_summary(posted=posted, failed=failed)
        return {"items_processed": posted, "failed": failed}


def post_content(text: str, platforms: list = None, scheduled_at: str = None):
    """Convenience function: post content right now"""
    bot = SocialPosterBot()
    return bot.post_to_all_platforms(text, scheduled_at, platforms)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--text",      type=str, help="Content to post")
    p.add_argument("--platforms", nargs="+", help="Target platforms")
    p.add_argument("--schedule",  type=str, help="ISO datetime to schedule")
    p.add_argument("--accounts",  action="store_true", help="List connected accounts")
    args = p.parse_args()

    bot = SocialPosterBot()

    if args.accounts:
        accounts = bot.get_accounts()
        print(f"\nConnected accounts ({len(accounts)}):")
        for a in accounts:
            print(f"  [{a.get('network','?')}] {a.get('name','?')} — ID: {a.get('id','?')}")
    elif args.text:
        result = bot.post_to_all_platforms(args.text, args.schedule, args.platforms)
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        bot.run()
