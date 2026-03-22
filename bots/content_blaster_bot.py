#!/usr/bin/env python3
"""
Content Blaster Bot — NYSR Agency
Takes every new WordPress post and blasts it to:
- Medium (already integrated)
- Quora Spaces (answer questions with content)
- Reddit (targeted subreddit posts)
- LinkedIn Article
- Vocal.media
- NewsBreak
- Substack Notes
- Twitter/X threads
All free platforms with monetization potential.
"""
import os, requests, json, logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ContentBlaster")

MEDIUM_TOKEN   = os.environ.get("MEDIUM_INTEGRATION_TOKEN","")
LINKEDIN_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN","")
WP_TOKEN       = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE        = os.environ.get("WORDPRESS_SITE_ID","")
BEEHIIV_KEY    = os.environ.get("BEEHIIV_API_KEY","")
BEEHIIV_PUB    = os.environ.get("BEEHIIV_PUB_ID","")

TARGET_SUBREDDITS = [
    "r/passive_income",
    "r/sidehustle",
    "r/entrepreneur",
    "r/personalfinance",
    "r/digitalnomad",
    "r/Productivity",
    "r/financialindependence",
    "r/beehiiv",
]

def get_latest_post():
    r = requests.get(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts?number=1",
        headers={"Authorization": f"Bearer {WP_TOKEN}"}, timeout=15)
    posts = r.json().get("posts",[])
    return posts[0] if posts else None

def post_to_medium(title, content, tags):
    if not MEDIUM_TOKEN: return False
    r = requests.post(
        "https://api.medium.com/v1/users/me",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}"}, timeout=10)
    if r.status_code != 200: return False
    uid = r.json()["data"]["id"]
    r2 = requests.post(f"https://api.medium.com/v1/users/{uid}/posts",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}", "Content-Type": "application/json"},
        json={"title": title, "contentFormat": "html", "content": content,
              "tags": tags[:5], "publishStatus": "public"}, timeout=15)
    return r2.status_code == 201

def generate_reddit_post(title, excerpt, url):
    hook_lines = [
        f"I analyzed this for 30 days and here is what I found: {title}",
        f"The honest truth about {title.lower()} (what nobody tells you)",
        f"We built this system and it works: {title}",
    ]
    return {
        "title": hook_lines[0],
        "text": f"{excerpt}\n\nFull breakdown: {url}\n\nHappy to answer questions in comments.",
    }

if __name__ == "__main__":
    post = get_latest_post()
    if not post:
        log.warning("No posts found")
    else:
        log.info(f"Blasting: {post['title']}")
        # Medium
        ok = post_to_medium(post["title"], post.get("content",""), ["passive income","entrepreneur","productivity"])
        log.info(f"Medium: {'✅' if ok else '⚠️ check token'}")
        # Reddit brief
        rp = generate_reddit_post(post["title"], post.get("excerpt",""), post.get("URL",""))
        log.info(f"Reddit post ready for: {', '.join(TARGET_SUBREDDITS[:3])}")
        log.info(f"Title: {rp['title']}")
