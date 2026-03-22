#!/usr/bin/env python3
"""
Trend Intelligence Agent — NYSR Agency
Powered by Claude. Monitors news, Reddit, Twitter trends daily.
Creates viral, timely content that rides trending topics.
Timely content gets 10-100x more organic traffic.
"""
import os, sys, json, logging, requests, feedparser
sys.path.insert(0,".")
from agents.claude_core import claude, claude_json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [TrendAgent] %(message)s")
log = logging.getLogger()

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY","")
WP_TOKEN    = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE     = os.environ.get("WORDPRESS_SITE_ID","")
BH_KEY      = os.environ.get("BEEHIIV_API_KEY","")
BH_PUB      = os.environ.get("BEEHIIV_PUB_ID","")

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.entrepreneur.com/latest.rss",
    "https://feeds.feedburner.com/entrepreneur/latest",
    "https://www.indiehackers.com/feed.rss",
]

def get_news_headlines() -> list:
    if not NEWSAPI_KEY: return []
    topics = ["passive income","AI tools entrepreneurs","content marketing automation",
              "side hustle 2026","digital products trending"]
    headlines = []
    for topic in topics[:2]:
        r = requests.get(
            f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=5&apiKey={NEWSAPI_KEY}",
            timeout=10)
        if r.status_code == 200:
            for a in r.json().get("articles",[]):
                headlines.append({"title": a["title"], "source": a["source"]["name"],
                                  "topic": topic, "url": a["url"]})
    return headlines[:10]

def get_rss_trends() -> list:
    items = []
    for feed_url in RSS_FEEDS[:2]:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                items.append({"title": entry.title, "source": feed.feed.title,
                               "summary": getattr(entry,"summary","")[:200]})
        except: pass
    return items

def identify_opportunities(headlines: list, rss: list) -> list:
    """Use Claude to identify which trends to write about."""
    all_content = headlines + rss
    if not all_content: return []
    
    content_str = json.dumps([{"title":i.get("title"),"source":i.get("source")} 
                               for i in all_content[:15]])
    
    return claude_json(
        "You are a content strategist for a passive income and AI automation brand.",
        f"""Review these trending headlines and identify the top 3 content opportunities.

Headlines: {content_str}

For each opportunity, the angle must:
1. Be relevant to entrepreneurs, passive income, or AI tools
2. Have a contrarian or unique take (not just summarizing the news)
3. Connect naturally to our products (ProFlow AI or digital downloads)

Return JSON array of objects with:
- opportunity: the trend/news item
- our_angle: our unique take that provides 10x more value than the original
- title: the blog post H1 title
- keyword: SEO keyword to target
- urgency: why write this TODAY specifically""",
        max_tokens=800
    )

def write_trend_post(opportunity: dict) -> str:
    """Write a reactive blog post riding the trend."""
    return claude(
        """You write for NY Spotlight Report. Brand voice: Direct, authoritative, helpful.
Audience: Entrepreneurs who want passive income and to use AI/automation.""",
        f"""Write a trend-reactive blog post.

Trending topic: {opportunity.get('opportunity','')}
Our angle: {opportunity.get('our_angle','')}
Title: {opportunity.get('title','')}
SEO keyword: {opportunity.get('keyword','')}
Why today: {opportunity.get('urgency','')}

Structure:
1. Quick take on the trend (2-3 paragraphs) — our POV, not a summary
2. What this means for entrepreneurs specifically
3. The practical implication (what they should DO about this)
4. How automated systems make this easier (tie to ProFlow AI naturally)
5. Key takeaway

Length: 800-1200 words. Move fast. This is timely content, not evergreen.
Include a CTA at the end for nyspotlightreport.com/proflow/""",
        max_tokens=2000
    )

def write_trending_social(opportunity: dict) -> dict:
    """Write platform-native viral posts for the trend."""
    return claude_json(
        "You write viral social content for entrepreneurs. Sharp, real, no fluff.",
        f"""Write viral social posts riding this trend: {opportunity.get('title','')}
Our angle: {opportunity.get('our_angle','')}

Return JSON with:
- twitter_thread: 5-tweet thread (each under 280 chars, numbered, ends with CTA)
- linkedin: 150-word LinkedIn post with data/insight + engagement question
- instagram_caption: Hook + insight + 15 hashtags
- reddit_post: Title + first paragraph for r/entrepreneur or r/passive_income""",
        max_tokens=1000
    )

def publish_to_wordpress(title, content, keyword):
    if not WP_TOKEN: return False
    r = requests.post(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts/new",
        headers={"Authorization": f"Bearer {WP_TOKEN}"},
        json={"title": title, "content": content, "status": "publish", "tags": keyword},
        timeout=30)
    return r.status_code == 200

def run():
    log.info("Trend Intelligence Agent starting...")
    headlines = get_news_headlines()
    rss_items = get_rss_trends()
    log.info(f"Headlines: {len(headlines)} | RSS items: {len(rss_items)}")
    
    opportunities = identify_opportunities(headlines, rss_items)
    log.info(f"Opportunities identified: {len(opportunities)}")
    
    for opp in opportunities[:2]:
        log.info(f"Writing trend post: {opp.get('title','')}")
        post = write_trend_post(opp)
        if post:
            publish_to_wordpress(opp.get("title",""), post, opp.get("keyword",""))
        
        social = write_trending_social(opp)
        if social:
            import json as j
            with open(f"/tmp/trend_social_{opp.get('keyword','post').replace(' ','_')}.json","w") as f:
                j.dump(social, f, indent=2)
    
    log.info("✅ Trend Agent complete")

if __name__ == "__main__":
    run()
