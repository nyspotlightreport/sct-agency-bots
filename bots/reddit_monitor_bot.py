#!/usr/bin/env python3
"""
REDDIT MONITOR BOT v1.0 — S.C. Thomas Internal Agency
Monitors Reddit for brand mentions, niche keywords, and lead opportunities.
Drafts helpful replies with soft CTAs. Tracks trending topics for content.
Schedule: Every 6 hours.
"""
import os, sys, json, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

class RedditMonitorBot(BaseBot):
    VERSION = "1.0.0"

    SUBREDDITS = os.getenv("REDDIT_SUBREDDITS",
        "nyc,NewYork,Journalism,media,entrepreneur,smallbusiness,marketing"
    ).split(",")

    KEYWORDS = os.getenv("REDDIT_KEYWORDS",
        "nyspotlightreport,ny spotlight,local media,nyc news,content strategy"
    ).split(",")

    def __init__(self):
        super().__init__("reddit-monitor")
        self.seen = set(self.state.get("seen_reddit_ids", []))

    @with_retry(max_retries=2, delay=3.0)
    def search_reddit(self, query: str, subreddit: str = None, limit: int = 10) -> list:
        """Search Reddit via public JSON API"""
        encoded = urllib.parse.quote(query)
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded}&sort=new&limit={limit}&restrict_sr=1"
        else:
            url = f"https://www.reddit.com/search.json?q={encoded}&sort=new&limit={limit}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "RedditMonitorBot/1.0 (agency automation; contact seanb041992@gmail.com)"
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            posts = data.get("data", {}).get("children", [])
            results = []
            for post in posts:
                pd = post.get("data", {})
                pid = pd.get("id", "")
                if pid and pid not in self.seen:
                    results.append({
                        "id":        pid,
                        "title":     pd.get("title", ""),
                        "text":      pd.get("selftext", "")[:300],
                        "subreddit": pd.get("subreddit", ""),
                        "url":       f"https://reddit.com{pd.get('permalink', '')}",
                        "score":     pd.get("score", 0),
                        "comments":  pd.get("num_comments", 0),
                    })
            return results
        except Exception as e:
            self.logger.warning(f"Reddit search failed for '{query}': {e}")
            return []

    def draft_reply(self, post: dict) -> str:
        """Draft a helpful reply using Claude"""
        system = ("You are a helpful Reddit user who happens to run a NY media outlet. "
                  "Write a genuinely helpful reply — no spam, no direct promotion. "
                  "Only mention nyspotlightreport.com if it's naturally relevant. "
                  "Be a real person. Max 3 sentences.")
        prompt = f"""Reddit post in r/{post['subreddit']}:
Title: {post['title']}
Content: {post['text'][:200]}

Write a helpful reply:"""
        return ClaudeClient.complete_safe(
            system=system, user=prompt, max_tokens=150,
            fallback=""
        )

    def execute(self) -> dict:
        all_posts = []
        for keyword in self.KEYWORDS[:3]:
            posts = self.search_reddit(keyword.strip())
            all_posts.extend(posts)
        for subreddit in self.SUBREDDITS[:3]:
            # Search for trending topics to repurpose as content
            posts = self.search_reddit("", subreddit.strip(), 5)
            all_posts.extend(posts)

        if not all_posts:
            return {"items_processed": 0}

        hot_posts = sorted(all_posts, key=lambda x: x["score"], reverse=True)[:5]
        reply_drafts = []
        for post in hot_posts[:3]:
            draft = self.draft_reply(post)
            if draft:
                reply_drafts.append({"post": post, "draft": draft})

        # Update seen IDs
        new_ids = [p["id"] for p in all_posts]
        self.seen.update(new_ids)
        self.state.set("seen_reddit_ids", list(self.seen)[-500:])

        if hot_posts or reply_drafts:
            drafts_html = "".join([f"""
<div style="border-left:3px solid #ff4500;padding:10px;margin-bottom:10px;background:#fff8f5;">
  <strong><a href="{d['post']['url']}">r/{d['post']['subreddit']}: {d['post']['title'][:60]}</a></strong><br>
  <em>Draft reply:</em> {d['draft']}
</div>""" for d in reply_drafts])

            AlertSystem.send(
                subject  = f"🤖 Reddit Monitor — {len(all_posts)} posts | {len(reply_drafts)} reply drafts",
                body_html= f"<h3>Reddit Opportunities</h3>{drafts_html}",
                severity = "INFO"
            )

        return {"items_processed": len(all_posts), "drafts": len(reply_drafts)}

if __name__ == "__main__":
    RedditMonitorBot().run()
# SECRETS: None needed (public Reddit API)
# ENV VARS: REDDIT_SUBREDDITS, REDDIT_KEYWORDS
