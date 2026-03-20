"""
beehiiv_newsletter_bot.py — NY Spotlight Report Newsletter Pipeline
Auto-curate content → publish to Beehiiv → grow subscribers → earn sponsorships
Runs: Daily 9am ET
"""
import os, json, urllib.request, urllib.error, datetime

class BeehiivBot:
    def __init__(self):
        self.api_key       = os.environ.get("BEEHIIV_API_KEY","")
        self.pub_id        = os.environ.get("BEEHIIV_PUB_ID","")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY","")
        self.newsapi_key   = os.environ.get("NEWSAPI_KEY","")
        self.guardian_key  = os.environ.get("GUARDIAN_API_KEY","test")
        self.chairman_email= os.environ.get("CHAIRMAN_EMAIL","seanb041992@gmail.com")

    def fetch_top_stories(self):
        """Pull today's top NYC entertainment stories"""
        stories = []
        # Guardian
        tags = ["stage/theatre","film/film","music/music","fashion/fashion","us-news/new-york"]
        for tag in tags[:3]:
            try:
                url = f"https://content.guardianapis.com/search?tag={tag}&order-by=newest&page-size=3&show-fields=headline,trailText,thumbnail&api-key={self.guardian_key}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read())
                for art in (data.get("response",{}).get("results",[]))[:2]:
                    stories.append({
                        "title": art.get("fields",{}).get("headline","") or art.get("webTitle",""),
                        "summary": art.get("fields",{}).get("trailText",""),
                        "url": art.get("webUrl",""),
                        "source": "The Guardian",
                        "section": tag.split("/")[0]
                    })
            except Exception as e:
                print(f"Guardian error {tag}: {e}")
        return stories[:8]

    def generate_newsletter_html(self, stories):
        """Use Claude to write newsletter HTML"""
        if not self.anthropic_key:
            return self._fallback_newsletter(stories)

        story_text = "\n".join([f"{i+1}. {s['title']} - {s.get('summary','')[:100]}" for i,s in enumerate(stories)])
        today = datetime.date.today().strftime("%B %d, %Y")

        prompt = f"""You are the editor of NY Spotlight Report, New York's premier entertainment newsletter.
Write a professional, engaging daily newsletter for {today}.

Stories to cover:
{story_text}

Format as clean HTML email with:
- Punchy subject-line style opening headline
- 3-4 story summaries (2-3 sentences each) with NYC/entertainment angle
- Brief editor's note at end (1 sentence, confident, authoritative tone)
- Professional closing

Return ONLY the HTML body content (no <html><head> tags). Use inline styles."""

        try:
            req_data = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1500,
                "messages": [{"role":"user","content": prompt}]
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=req_data,
                headers={"x-api-key":self.anthropic_key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                resp = json.loads(r.read())
                return resp.get("content",[{}])[0].get("text","")
        except Exception as e:
            print(f"Claude error: {e}")
            return self._fallback_newsletter(stories)

    def _fallback_newsletter(self, stories):
        today = datetime.date.today().strftime("%B %d, %Y")
        items = "".join([f"<li style='margin:12px 0;'><strong>{s['title']}</strong><br><span style='color:#555;font-size:14px;'>{s.get('summary','')[:150]}</span> <a href='{s['url']}' style='color:#b5191b;'>Read →</a></li>" for s in stories[:5]])
        return f"""<div style='font-family:Georgia,serif;max-width:600px;margin:0 auto;'>
<h1 style='color:#b5191b;border-bottom:2px solid #b5191b;padding-bottom:10px;'>NY Spotlight Report</h1>
<p style='color:#666;font-size:12px;'>Today's Top Entertainment News — {today}</p>
<ul style='padding-left:20px;'>{items}</ul>
<p style='font-size:13px;color:#777;border-top:1px solid #eee;padding-top:10px;'>NY Spotlight Report — New York's Entertainment Authority</p>
</div>"""

    def create_beehiiv_draft(self, html_content, subject):
        """Create draft post in Beehiiv"""
        if not self.api_key or not self.pub_id:
            print("⚠️ No Beehiiv credentials — saving newsletter locally only")
            with open("/tmp/newsletter_draft.html","w") as f:
                f.write(html_content)
            print("Saved to /tmp/newsletter_draft.html")
            return {"status":"saved_locally"}

        today = datetime.date.today().strftime("%B %d, %Y")
        payload = json.dumps({
            "subject": subject or f"🎭 NYC Entertainment Daily — {today}",
            "status": "draft",
            "content_json": {"type":"doc","content":[]},
            "content_text": "See HTML version",
            "thumbnail_url": "",
            "meta_title": f"NY Spotlight Report — {today}",
            "meta_description": "New York's top entertainment news delivered daily.",
        }).encode()

        req = urllib.request.Request(
            f"https://api.beehiiv.com/v2/publications/{self.pub_id}/posts",
            data=payload,
            headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.loads(r.read())
                print(f"✅ Beehiiv draft created: {result.get('data',{}).get('id','?')}")
                return result
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"Beehiiv error HTTP {e.code}: {body[:200]}")
            return {"error": body}

    def get_subscriber_count(self):
        """Get current subscriber count from Beehiiv"""
        if not self.api_key or not self.pub_id:
            return {"subscribers": "N/A — no API key"}
        try:
            req = urllib.request.Request(
                f"https://api.beehiiv.com/v2/publications/{self.pub_id}/subscriptions?limit=1",
                headers={"Authorization":f"Bearer {self.api_key}"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
                return {"subscribers": data.get("total_results", 0)}
        except Exception as e:
            return {"subscribers": f"Error: {e}"}

    def send_growth_report_to_gmail(self, stats):
        """Email daily stats"""
        pass  # handled by weekly_report_bot

    def run(self):
        print("=== BEEHIIV NEWSLETTER BOT STARTING ===")
        today = datetime.date.today().strftime("%B %d, %Y")

        print("1. Fetching top stories...")
        stories = self.fetch_top_stories()
        print(f"   Got {len(stories)} stories")

        print("2. Generating newsletter content...")
        html = self.generate_newsletter_html(stories)
        subject = f"🎭 NYC Entertainment Daily — {today}"
        print(f"   Generated {len(html)} chars of HTML")

        print("3. Creating Beehiiv draft...")
        result = self.create_beehiiv_draft(html, subject)

        print("4. Checking subscriber count...")
        sub_stats = self.get_subscriber_count()
        print(f"   Subscribers: {sub_stats.get('subscribers','?')}")

        print("=== BEEHIIV BOT COMPLETE ===")
        return {"status":"complete","stories":len(stories),"subscribers":sub_stats.get("subscribers","?")}

if __name__ == "__main__":
    bot = BeehiivBot()
    bot.run()
