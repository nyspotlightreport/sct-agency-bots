#!/usr/bin/env python3
"""
WordPress Daily Blogger — Repurposes affiliate content to WordPress.com
Drives additional organic traffic from WordPress.com search
Runs daily via GitHub Actions
"""
import os, requests, json, random, datetime

WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE  = "nyspotlightreport.wordpress.com"
CLAUDE   = os.environ.get("ANTHROPIC_API_KEY","")
AFFILIATE_TAG = "nysr"

ARTICLE_TOPICS = [
    ("How to Build a $500/Month Passive Income in 90 Days", "passive income", "make money online"),
    ("Best AI Tools for Entrepreneurs 2026", "ai tools entrepreneurs", "jasper beehiiv hubspot"),
    ("Bandwidth Sharing: The Truly Passive Income Nobody Talks About", "bandwidth sharing", "earnapp honeygain"),
    ("Amazon KDP: How to Publish Low-Content Books for Royalties", "amazon kdp", "publish books royalties"),
    ("The Print-on-Demand Income Guide 2026", "print on demand", "redbubble teepublic society6"),
    ("Why Your Email List Is Worth More Than Your Social Following", "email list", "beehiiv convertkit"),
    ("Affiliate Marketing: Programs That Pay $100-$1000 Per Sale", "affiliate marketing", "hubspot ahrefs"),
    ("How to Create Digital Products That Sell While You Sleep", "digital products", "gumroad etsy"),
    ("The SEO Strategy That Actually Works for Small Sites in 2026", "seo strategy", "ahrefs semrush"),
    ("Side Hustles That Scale: From $0 to $500/Month", "side hustles", "passive income online"),
]

def generate_post(topic, keyword, related):
    if not CLAUDE:
        return f"""<p>Looking to build passive income in 2026? {topic} is one of the most searched topics right now — and for good reason.</p>
<p>Whether you're using bandwidth sharing apps like <a href="https://earnapp.com/i/NYSR">EarnApp</a> and <a href="https://r.honeygain.me/NYSPOTLIGHT">Honeygain</a>, building a newsletter on <a href="https://beehiiv.com/?via=nysr">Beehiiv</a>, or selling digital products, the key is building multiple income streams that compound over time.</p>
<p>For SEO tools, <a href="https://ahrefs.com/?ref=nysr">Ahrefs</a> and <a href="https://semrush.com/?ref=nysr">SEMrush</a> provide the data you need to rank content that generates passive affiliate income. For CRM and business growth, <a href="https://hubspot.com/?via=nysr">HubSpot</a> remains the top free option.</p>
<p>The formula: create once, promote intelligently, let the systems work. Read our full guide at nyspotlightreport.com for the complete framework.</p>"""

    resp = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": CLAUDE, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model":"claude-haiku-4-5-20251001","max_tokens":800,"messages":[{
            "role":"user",
            "content": f"""Write a 400-word blog post about: {topic}
Keywords: {keyword}, {related}
Include: 2-3 affiliate links naturally (HubSpot, Ahrefs, Beehiiv, EarnApp, Kinsta, ConvertKit, Jasper)
Format: HTML paragraphs. No markdown. No headers. Just <p> tags.
Tone: Expert, helpful, direct. Not salesy.
End with a call to action to visit nyspotlightreport.com"""
        }]}, timeout=25)
    
    if resp.ok:
        return resp.json()["content"][0]["text"]
    return f"<p>{topic} — full guide at nyspotlightreport.com</p>"

def post_to_wordpress(title, content, tags):
    if not WP_TOKEN:
        print("No WP token"); return False
    
    token = WP_TOKEN.replace("%","").replace("n","%n").replace("$","%24") if "%" not in WP_TOKEN else WP_TOKEN
    resp = requests.post(
        f"https://public-api.wordpress.com/wp/v2/sites/{WP_SITE}/posts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"title": title, "content": content, "status": "publish",
              "tags": [], "excerpt": f"Expert guide: {title[:100]}"},
        timeout=20)
    
    print(f"WordPress post: {resp.status_code}")
    if resp.ok:
        post_url = resp.json().get("link","")
        print(f"Live at: {post_url}")
    else:
        print(f"Error: {resp.text[:200]}")
    return resp.ok

def run():
    today = datetime.date.today()
    # Rotate topics based on day of year
    topic_data = ARTICLE_TOPICS[today.timetuple().tm_yday % len(ARTICLE_TOPICS)]
    title, keyword, related = topic_data
    
    print(f"Generating WordPress post: {title}")
    content = generate_post(title, keyword, related)
    
    success = post_to_wordpress(title, content, [keyword])
    if success:
        print(f"✅ WordPress post published: {title}")
    else:
        print(f"❌ Failed to publish")

if __name__ == "__main__":
    run()
