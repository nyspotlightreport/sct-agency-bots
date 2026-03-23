#!/usr/bin/env python3
"""
SOCIAL POSTER BOT v3.0 — S.C. Thomas Internal Agency
Posts to ALL platforms via Publer API.
FIXED: uses urllib only (no requests), proper workspace injection, gzip handling
"""
import os, sys, json, urllib.request, urllib.error, urllib.parse, gzip
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

class SocialPosterBot(BaseBot):
    VERSION = "3.0.0"
    BASE    = "https://app.publer.com/api/v1"

    def __init__(self):
        super().__init__("social-poster")
        self.api_key   = os.getenv("PUBLER_API_KEY", "")
        self.workspace = os.getenv("PUBLER_WORKSPACE_ID", "")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer-API {self.api_key}",
            "Publer-Workspace-Id": self.workspace,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SCT-Agency/3.0",
        }

    def _get(self, path):
        req = urllib.request.Request(f"{self.BASE}{path}", headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                try: return json.loads(gzip.decompress(raw))
                except: return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read()
            try: body = gzip.decompress(raw).decode()
            except: body = raw.decode('utf-8','replace')
            self.logger.error(f"Publer {path}: HTTP {e.code} — {body[:100]}")
            return {}

    def _post(self, path, payload):
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(f"{self.BASE}{path}", data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                try: return json.loads(gzip.decompress(raw))
                except: return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read()
            try: body = gzip.decompress(raw).decode()
            except: body = raw.decode('utf-8','replace')
            self.logger.error(f"Publer POST {path}: HTTP {e.code} — {body[:200]}")
            return {}

    def get_accounts(self):
        data = self._get("/accounts")
        return data.get("accounts", data if isinstance(data, list) else [])

    def schedule_post(self, text, account_ids, scheduled_at=None):
        if not scheduled_at:
            dt = datetime.now(timezone.utc) + timedelta(minutes=30)
            scheduled_at = dt.strftime("%Y-%m-%dT%H:%M+00:00")
        payload = {"bulk": {"state": "scheduled", "posts": [{
            "networks": {"default": {"type": "status", "text": text}},
            "accounts": [{"id": aid, "scheduled_at": scheduled_at} for aid in account_ids]
        }]}}
        return self._post("/posts/schedule", payload)

    def generate_daily_content(self):
        system = "You are S.C. Thomas, Editor in Chief of NY Spotlight Report. Write punchy, direct social media content."
        prompt = f"""Write 1 engaging social post for today ({datetime.now().strftime('%B %d, %Y')}).
Topic: NY media/business news, entrepreneurship, or AI/automation for media companies.
Style: Short. Direct. No hashtag spam. Max 3 relevant hashtags. Under 280 chars.
Return ONLY the post text."""
        return ClaudeClient.complete_safe(system=system, user=prompt, max_tokens=150,
                                          fallback="Building the future of NY media. One story at a time. #NYSpotlight")

    def execute(self):
        accounts = self.get_accounts()
        if not accounts:
            self.logger.warning("No Publer accounts found. Check PUBLER_API_KEY and PUBLER_WORKSPACE_ID.")
            return {"error": "no_accounts"}

        self.logger.info(f"Found {len(accounts)} accounts")
        active = [a for a in accounts if a.get("status") == "active" or "id" in a]

        # Generate and post content
        content = self.generate_daily_content()
        if not content:
            return {"error": "no_content"}

        account_ids = [a["id"] for a in active[:6]]  # Max 6 platforms per post
        result = self.schedule_post(content, account_ids)

        job_id = result.get("job_id", "")
        self.logger.info(f"Posted to {len(account_ids)} platforms. Job: {job_id}")
        self.state.set("last_post", {"text": content[:100], "job_id": job_id,
                                      "timestamp": datetime.now().isoformat()})
        return {"posted": len(account_ids), "job_id": job_id, "content": content[:80]}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--accounts", action="store_true")
    p.add_argument("--post", type=str, help="Post specific text")
    args = p.parse_args()
    bot = SocialPosterBot()
    if args.accounts:
        accts = bot.get_accounts()
        print(f"Found {len(accts)} accounts:")
        for a in accts: print(f"  {a.get('id')} | {a.get('name','?')} | {a.get('provider','?')} | {a.get('status','?')}")
    elif args.post:
        accts = bot.get_accounts()
        ids = [a["id"] for a in accts[:3]]
        r = bot.schedule_post(args.post, ids)
        print(f"Result: {r}")
    else:
        bot.run()
