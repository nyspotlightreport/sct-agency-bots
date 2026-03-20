#!/usr/bin/env python3
"""
NEWS DIGEST BOT v1.0 — S.C. Thomas Internal Agency
Pulls breaking news from NewsAPI + Guardian + RSS feeds.
Claude summarizes + writes social content angles.
Posts daily digest to all platforms via Publer.
Schedule: Daily 7:00 AM ET.
"""

import os, sys, json, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

class NewsDigestBot(BaseBot):
    VERSION = "1.0.0"

    # Customize these topics for NY Spotlight Report
    TOPICS = os.getenv("NEWS_TOPICS",
        "New York,NYC business,media industry,local government,real estate NYC"
    ).split(",")

    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

    def __init__(self):
        super().__init__("news-digest")

    @with_retry(max_retries=2, delay=2.0)
    def fetch_newsapi(self, query: str, page_size: int = 5) -> list:
        """Fetch from NewsAPI"""
        if not self.NEWSAPI_KEY:
            return []
        encoded = urllib.parse.quote(query)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        url = (f"https://newsapi.org/v2/everything?q={encoded}"
               f"&from={yesterday}&sortBy=publishedAt&pageSize={page_size}"
               f"&language=en&apiKey={self.NEWSAPI_KEY}")
        req = urllib.request.Request(url,
            headers={"User-Agent": "NewsDigestBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data.get("articles", [])

    @with_retry(max_retries=2, delay=2.0)
    def fetch_guardian(self, query: str) -> list:
        """Fetch from Guardian API (free, no key needed for basic)"""
        encoded = urllib.parse.quote(query)
        url = f"https://content.guardianapis.com/search?q={encoded}&order-by=newest&page-size=3&api-key=test"
        try:
            req = urllib.request.Request(url,
                headers={"User-Agent": "NewsDigestBot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            results = data.get("response", {}).get("results", [])
            return [{"title": r["webTitle"], "url": r["webUrl"],
                     "source": {"name": "The Guardian"}} for r in results]
        except Exception:
            return []

    def collect_news(self) -> list:
        """Collect news from all sources"""
        all_articles = []
        seen_titles = set()

        for topic in self.TOPICS[:3]:  # Limit to 3 topics
            topic = topic.strip()
            # NewsAPI
            articles = self.fetch_newsapi(topic, 3)
            for a in articles:
                title = a.get("title", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_articles.append({
                        "title":   title,
                        "url":     a.get("url", ""),
                        "source":  a.get("source", {}).get("name", ""),
                        "desc":    a.get("description", "")[:200],
                        "topic":   topic,
                    })
            # Guardian
            for a in self.fetch_guardian(topic):
                title = a.get("title", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_articles.append({
                        "title":   title,
                        "url":     a.get("url", ""),
                        "source":  "The Guardian",
                        "desc":    "",
                        "topic":   topic,
                    })

        return all_articles[:15]  # Max 15 articles per run

    def write_digest_content(self, articles: list) -> dict:
        """Use Claude to write social content from news"""
        if not articles:
            return {}

        articles_text = "\n".join([
            f"{i+1}. [{a['source']}] {a['title']}\n   {a['desc']}"
            for i, a in enumerate(articles[:10])
        ])

        system = """You are the content director for NY Spotlight Report.
Given today's news headlines, write engaging social media content.
Return ONLY valid JSON."""

        prompt = f"""Today's headlines:
{articles_text}

Write social content for each platform. Return JSON:
{{
  "linkedin": "professional 150-word post about the most significant story with insight",
  "twitter": "sharp 240-char take on the top story",
  "newsletter_hook": "1 sentence email subject line for today's digest",
  "top_story": "title of the most newsworthy story",
  "top_story_url": "url of top story",
  "key_themes": ["theme1", "theme2", "theme3"]
}}"""

        try:
            return ClaudeClient.complete(system, prompt, max_tokens=800, json_mode=True)
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return {}

    def execute(self) -> dict:
        self.logger.info(f"Collecting news for topics: {self.TOPICS}")

        articles = self.collect_news()
        if not articles:
            self.logger.warning("No articles found")
            return {"items_processed": 0}

        self.logger.info(f"Collected {len(articles)} articles")
        content = self.write_digest_content(articles)

        if content:
            # Queue posts for social poster bot
            pending = self.state.get("pending_posts", [])
            date_str = datetime.now().strftime("%b %d")

            if content.get("twitter"):
                pending.append({
                    "text":      content["twitter"],
                    "platforms": ["twitter"],
                    "source":    "news_digest"
                })
            if content.get("linkedin"):
                pending.append({
                    "text":      content["linkedin"],
                    "platforms": ["linkedin"],
                    "source":    "news_digest"
                })

            self.state.set("pending_posts", pending)
            self.state.set("last_digest", {
                "date":       date_str,
                "articles":   len(articles),
                "top_story":  content.get("top_story", ""),
                "themes":     content.get("key_themes", []),
            })

        # Alert with digest summary
        AlertSystem.send(
            subject  = f"📰 News Digest — {len(articles)} stories | {datetime.now().strftime('%b %d')}",
            body_html= f"""
<h3>Today's News Digest</h3>
<p><strong>Top story:</strong> {content.get('top_story', 'N/A')}</p>
<p><strong>Themes:</strong> {', '.join(content.get('key_themes', []))}</p>
<p><strong>Articles collected:</strong> {len(articles)}</p>
<p><strong>Social posts queued:</strong> {2 if content else 0}</p>
<hr>
<p><strong>LinkedIn post:</strong><br>{content.get('linkedin', '')[:300]}...</p>
""",
            severity = "INFO"
        )

        self.log_summary(articles=len(articles), posts_queued=2 if content else 0)
        return {"items_processed": len(articles)}


if __name__ == "__main__":
    bot = NewsDigestBot()
    bot.run()

# SETUP:
# export NEWSAPI_KEY=your_key_from_newsapi.org
# export NEWS_TOPICS="New York,NYC business,media industry"
# GitHub secret: NEWSAPI_KEY
# Free: 100 requests/day on free plan
