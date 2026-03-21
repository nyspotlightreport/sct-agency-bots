#!/usr/bin/env python3
"""
Content Intelligence Agent — NYSR Agency
Powered by Claude. Writes every piece of content from scratch.
No templates. No repetition. Always fresh, always on-brand.

Outputs per run:
- 1 full SEO blog post (1,500-2,500 words)
- 1 newsletter issue
- 5 social media posts (platform-native)
- 1 YouTube Shorts script
- 3 Pinterest pin descriptions
"""
import os, sys, json, logging, requests, base64
sys.path.insert(0,".")
from agents.claude_core import claude, claude_json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ContentAgent] %(message)s")
log = logging.getLogger()

GH_TOKEN = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE  = os.environ.get("WORDPRESS_SITE_ID","nyspotlightreport.wordpress.com")
BH_KEY   = os.environ.get("BEEHIIV_API_KEY","")
BH_PUB   = os.environ.get("BEEHIIV_PUB_ID","")
PUBLER   = os.environ.get("PUBLER_API_KEY","")

BRAND_VOICE = """You are writing for NY Spotlight Report, a media brand by S.C. Thomas.
Brand voice: Direct. No fluff. Manhattan authority — calm, disciplined, sharp.
Audience: Entrepreneurs, side hustlers, and content creators aged 25-45.
Topics: Passive income, content automation, AI tools, entrepreneurship, financial independence.
Tone: Peer-to-peer expert. Like a sharp friend who's figured something out and is sharing it directly.
Never: Generic advice, clichés, "in conclusion", "in today's digital age", excessive disclaimers.
Always: Specific numbers, actionable steps, real examples."""

def research_trending_topics() -> list:
    """Use Claude to identify what to write about today."""
    return claude_json(
        "You are a content strategist for a passive income and AI automation brand.",
        """Generate 5 trending blog post ideas for today that would rank on Google and drive traffic.
        
Focus on: passive income, AI tools, content automation, side hustles, digital products.
Each idea should target a specific long-tail keyword with 500-5,000 monthly searches.

Return JSON array of objects with keys:
- title: compelling H1 title
- keyword: primary SEO keyword  
- angle: unique angle that makes this different from other content
- search_intent: what the reader wants to accomplish
- monetization: how this drives ProFlow AI or Gumroad sales""",
        max_tokens=1000
    )

def write_blog_post(topic: dict) -> str:
    """Write a full 2,000-word SEO blog post."""
    log.info(f"Writing blog post: {topic.get('title','')}")
    return claude(
        BRAND_VOICE,
        f"""Write a complete, publication-ready SEO blog post.

Title: {topic.get('title','')}
Primary Keyword: {topic.get('keyword','')}
Angle: {topic.get('angle','')}
Reader Intent: {topic.get('search_intent','')}

Requirements:
- 1,800-2,500 words
- H2 and H3 subheadings (use ## and ###)
- Include specific numbers, tools, and examples
- 3-5 internal links as [anchor text](/url) placeholders
- 1 CTA near the end pointing to https://nyspotlightreport.com/proflow/
- Naturally mention NY Spotlight Report 2-3 times
- End with a strong conclusion + 1 question to drive comments
- Include a "Quick Takeaways" box at the top (3-5 bullets)

Write the full post now. No preamble. Start with the title as an H1.""",
        max_tokens=4000
    )

def write_newsletter(blog_post: str, topic: dict) -> dict:
    """Write a newsletter issue based on the blog post."""
    log.info("Writing newsletter issue...")
    return claude_json(
        BRAND_VOICE + "\n\nYou write engaging email newsletters that get 40%+ open rates.",
        f"""Write a complete Beehiiv newsletter issue based on this blog post.

Blog title: {topic.get('title','')}
Blog excerpt: {blog_post[:500]}

Return JSON with:
- subject: email subject line (under 50 chars, creates curiosity)
- preview: preview text (under 90 chars)  
- body_html: complete HTML newsletter body with:
  * Hook opening (2-3 sentences, grabs attention)
  * Main insight (3-4 paragraphs, the meat)
  * Practical takeaway box (3 bullet points)
  * CTA section pointing to https://nyspotlightreport.com/proflow/
  * Sign-off from S.C. Thomas
  Use simple HTML: <p>, <strong>, <ul>, <li>, <h2>, <a href="">
- estimated_read_time: "X min read" """,
        max_tokens=2000
    )

def write_social_posts(topic: dict) -> dict:
    """Write platform-native social posts."""
    log.info("Writing social posts...")
    return claude_json(
        BRAND_VOICE,
        f"""Write platform-native social media posts for this topic: {topic.get('title','')}
Keyword context: {topic.get('keyword','')}

Return JSON with these keys, each containing the post text:
- twitter: Thread starter tweet (under 280 chars) + "🧵" — hook only, no hashtags yet
- instagram: Caption with hook, value, CTA, and 15-20 hashtags
- linkedin: Professional 150-word post with insight + engagement question
- pinterest: 3 different pin descriptions (SEO-optimized, 150 chars each) as array
- reddit_title: Post title for r/passive_income or r/sidehustle (no hype, sounds organic)""",
        max_tokens=1500
    )

def write_youtube_script(topic: dict) -> str:
    """Write a 60-second YouTube Shorts script."""
    return claude(
        BRAND_VOICE,
        f"""Write a 60-second YouTube Shorts script about: {topic.get('title','')}

Format:
HOOK (0-3 sec): [One sentence that stops the scroll — shocking stat or bold claim]
SETUP (3-10 sec): [Why this matters to them right now]
CONTENT (10-50 sec): [3 rapid-fire insights, each one sentence]
CTA (50-60 sec): [Tell them to follow for more + what the next video covers]

Keep each section tight. No filler. Total word count: 120-150 words max.
Write it conversational — like talking to a friend, not reading a script.""",
        max_tokens=400
    )

def publish_to_wordpress(title: str, content: str, keyword: str) -> bool:
    if not WP_TOKEN: return False
    r = requests.post(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts/new",
        headers={"Authorization": f"Bearer {WP_TOKEN}"},
        json={"title": title, "content": content, "status": "publish",
              "tags": keyword, "categories": "passive income,automation"},
        timeout=30)
    if r.status_code == 200:
        url = r.json().get("URL","")
        log.info(f"✅ Published to WordPress: {url}")
        return True
    log.error(f"WordPress publish failed: {r.status_code}")
    return False

def publish_newsletter(newsletter: dict) -> bool:
    if not BH_KEY or not newsletter.get("subject"): return False
    r = requests.post(
        f"https://api.beehiiv.com/v2/publications/{BH_PUB}/emails",
        headers={"Authorization": f"Bearer {BH_KEY}", "Content-Type": "application/json"},
        json={
            "subject": newsletter["subject"],
            "preview_text": newsletter.get("preview",""),
            "content": {"html": newsletter.get("body_html","")},
            "status": "draft"
        }, timeout=30)
    ok = r.status_code in [200,201]
    log.info(f"{'✅' if ok else '❌'} Beehiiv newsletter: {newsletter.get('subject','')}")
    return ok

def run():
    log.info("Content Intelligence Agent starting...")
    
    # 1. Research today's topics
    topics = research_trending_topics()
    if not topics:
        log.error("No topics generated — check API key")
        return
    
    log.info(f"Topics researched: {len(topics)}")
    topic = topics[0]  # Use best topic today
    log.info(f"Writing about: {topic.get('title','')}")
    
    # 2. Write blog post
    post = write_blog_post(topic)
    if post:
        title = topic.get("title","")
        publish_to_wordpress(title, post, topic.get("keyword",""))
    
    # 3. Write newsletter
    newsletter = write_newsletter(post, topic)
    if newsletter:
        publish_newsletter(newsletter)
    
    # 4. Write social posts
    social = write_social_posts(topic)
    if social:
        log.info(f"Social posts: {list(social.keys())}")
        # Save for Publer to pick up
        import json
        with open("/tmp/social_posts_today.json","w") as f:
            json.dump({"topic": topic["title"], "posts": social}, f, indent=2)
    
    # 5. YouTube script
    yt_script = write_youtube_script(topic)
    if yt_script:
        log.info(f"YouTube script: {len(yt_script)} chars")
    
    log.info("✅ Content Intelligence Agent complete")

if __name__ == "__main__":
    run()
