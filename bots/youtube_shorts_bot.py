"""
youtube_shorts_bot.py — Daily YouTube Shorts Script Generator
Takes top news → generates short video scripts → creates Publer draft posts
Full pipeline: Script + Hook + Hashtags + Thumbnail concept + SEO title
Runs: Daily 6am ET (before social_poster_bot)
Revenue: YouTube AdSense ($100-5k+/mo with consistent output)
"""
import os, json, urllib.request, datetime, time

class YouTubeShortsBot:
    def __init__(self):
        self.anthropic_key  = os.environ.get("ANTHROPIC_API_KEY","")
        self.newsapi_key    = os.environ.get("NEWSAPI_KEY","")
        self.publer_key     = os.environ.get("PUBLER_API_KEY","")
        self.publer_ws_id   = os.environ.get("PUBLER_WORKSPACE_ID","69bc5c22ef1de019931daeae")

    def get_trending_story(self):
        """Get today's top NYC entertainment story"""
        if not self.newsapi_key:
            return {"title":"NYC Broadway season opens to record crowds","url":"#","description":"Broadway is booming"}

        queries = [
            "Broadway New York premiere 2026",
            "NYC entertainment celebrity",
            "New York film festival",
        ]
        for q in queries:
            try:
                url = f"https://newsapi.org/v2/everything?q={urllib.request.quote(q)}&language=en&sortBy=publishedAt&pageSize=3&apiKey={self.newsapi_key}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read())
                articles = [a for a in data.get("articles",[]) if a.get("title") and a["title"] != "[Removed]"]
                if articles:
                    return articles[0]
            except Exception as e:
                print(f"NewsAPI error: {e}")
        return {"title":"NYC Entertainment News", "description":"New York entertainment roundup"}

    def generate_shorts_package(self, story):
        """Generate complete Shorts content package via Claude"""
        if not self.anthropic_key:
            return self._fallback_script(story)

        today = datetime.date.today().strftime("%B %d, %Y")
        prompt = f"""You are a viral YouTube Shorts creator for NY Spotlight Report.
Create a complete Shorts package for this story:
STORY: {story.get('title','')}
DETAILS: {story.get('description','')[:200]}
DATE: {today}

Return ONLY valid JSON (no markdown):
{{
  "hook": "First 3 seconds spoken text to grab attention",
  "script": "Full 30-45 second script (spoken text only, no stage directions)",
  "title": "SEO YouTube title (max 60 chars)",
  "description": "YouTube description (150 chars) with keywords",
  "hashtags": ["#Broadway","#NYC","#Entertainment","#NYCNews","#Viral"],
  "thumbnail_concept": "Visual description for thumbnail (text overlay + background)",
  "call_to_action": "End screen CTA (5 words max)",
  "estimated_views": "Viral potential: low/medium/high"
}}"""

        try:
            req_data = json.dumps({
                "model":"claude-haiku-4-5-20251001","max_tokens":600,
                "messages":[{"role":"user","content":prompt}]
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=req_data,
                headers={"x-api-key":self.anthropic_key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read())
                raw = resp.get("content",[{}])[0].get("text","")
                import re
                match = re.search(r'\{[\s\S]*\}', raw)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            print(f"Claude error: {e}")
        return self._fallback_script(story)

    def _fallback_script(self, story):
        title = story.get("title","NYC Entertainment")
        return {
            "hook": f"NYC just made headlines and you NEED to know this...",
            "script": f"Here's what's happening in New York entertainment right now. {story.get('description','')[:150]} This is why New York City stays the entertainment capital of the world. Follow NY Spotlight Report for daily NYC coverage!",
            "title": f"NYC Entertainment News {datetime.date.today().strftime('%b %d')}",
            "description": "NYC entertainment news daily | Broadway | Film | Music | Fashion #NYC #Entertainment",
            "hashtags": ["#NYC","#Broadway","#Entertainment","#NewYork","#Viral","#News","#NYSpotlight"],
            "thumbnail_concept": "Bold red/black design with NYC skyline + white text overlay of headline",
            "call_to_action": "Follow for daily NYC news!",
            "estimated_views": "medium"
        }

    def post_script_to_publer(self, package, story_url):
        """Post the script as a Publer draft (text post with full script)"""
        if not self.publer_key:
            print("⚠️ No Publer key — script saved to file")
            with open("/tmp/shorts_script.json","w") as f:
                json.dump(package, f, indent=2)
            return False

        # Format as social post caption (the script itself)
        caption = f"""🎬 SCRIPT: {package.get('title','')}

HOOK: {package.get('hook','')}

📜 FULL SCRIPT:
{package.get('script','')}

🎯 THUMBNAIL: {package.get('thumbnail_concept','')}

📣 CTA: {package.get('call_to_action','')}

{' '.join(package.get('hashtags',[])[:10])}

Source: {story_url}"""

        payload = json.dumps({
            "post": {
                "workspace_id": self.publer_ws_id,
                "type": "feed",
                "status": "draft",
                "content": caption[:2000],
                "account_ids": []
            }
        }).encode()

        req = urllib.request.Request(
            "https://api.publer.io/v1/posts",
            data=payload,
            headers={"Authorization":f"Bearer {self.publer_key}","Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                result = json.loads(r.read())
                print(f"✅ Publer draft created")
                return True
        except Exception as e:
            print(f"Publer error: {e}")
            return False

    def generate_weekly_batch(self):
        """Generate 7 scripts at once for the week"""
        scripts = []
        topics = [
            "Broadway show opening New York",
            "NYC film premiere celebrity",
            "New York fashion week 2026",
            "Manhattan music concert event",
            "NYC entertainment celebrity news",
            "New York award show 2026",
            "Brooklyn arts scene viral",
        ]

        print("Generating week of YouTube Shorts scripts...")
        for i, topic in enumerate(topics):
            print(f"  Script {i+1}/7: {topic[:40]}...")
            story = {"title": topic, "description": f"Latest news about {topic} in New York City"}
            package = self.generate_shorts_package(story)
            scripts.append({"topic": topic, "package": package})
            time.sleep(1)

        # Save batch
        with open("/tmp/shorts_weekly_batch.json","w") as f:
            json.dump(scripts, f, indent=2)
        print(f"✅ Saved {len(scripts)} scripts to /tmp/shorts_weekly_batch.json")
        return scripts

    def run(self):
        print("=== YOUTUBE SHORTS BOT STARTING ===")
        print("1. Getting trending story...")
        story = self.get_trending_story()
        print(f"   Story: {story.get('title','?')[:60]}")

        print("2. Generating Shorts package via Claude...")
        package = self.generate_shorts_package(story)
        print(f"   Hook: {package.get('hook','?')[:50]}...")
        print(f"   Viral potential: {package.get('estimated_views','?')}")

        print("3. Saving script + posting to Publer draft...")
        story_url = story.get("url","https://nyspotlightreport.com")
        posted = self.post_script_to_publer(package, story_url)

        # Always save locally
        today = datetime.date.today().isoformat()
        with open(f"/tmp/shorts_{today}.json","w") as f:
            json.dump({"story":story,"package":package,"posted":posted}, f, indent=2)

        print(f"\n✅ SHORTS BOT COMPLETE: Script generated, posted={posted}")
        print(f"   Title: {package.get('title','?')}")
        print(f"   CTA: {package.get('call_to_action','?')}")
        return package

if __name__ == "__main__":
    bot = YouTubeShortsBot()
    bot.run()
