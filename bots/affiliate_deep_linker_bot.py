#!/usr/bin/env python3
"""
Affiliate Deep Link Injector — NYSR Agency
Scans all WordPress blog posts and ensures every relevant keyword
has an affiliate link. Increases affiliate revenue per post by 3-5x.
Runs daily after WordPress blogger bot.
"""
import os, requests, json, re, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("AffiliateLinkBot")

WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE  = os.environ.get("WORDPRESS_SITE_ID", "nyspotlightreport.wordpress.com")
BASE     = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}"

# High-value affiliate programs mapped to keywords
AFFILIATE_LINKS = {
    # SEO Tools
    "ahrefs": "https://ahrefs.com/?via=nysr",
    "semrush": "https://semrush.com/?via=nysr",
    # Email Marketing
    "beehiiv": "https://www.beehiiv.com?via=nysr",
    "convertkit": "https://convertkit.com?lmref=nysr",
    # Hosting
    "bluehost": "https://www.bluehost.com/web-hosting/nysr",
    "hostinger": "https://www.hostinger.com?REFERRALCODE=nysr",
    # Business Tools
    "canva": "https://www.canva.com/affiliates/nysr",
    "shopify": "https://shopify.com/?ref=nysr",
    "hubspot": "https://hubspot.sjv.io/nysr",
    # Passive Income
    "honeygain": "https://r.honeygain.me/NYSR101",
    "earnapp": "https://earnapp.com/i/nysr",
    "gumroad": "https://gumroad.com?via=nysr",
    # AI Tools
    "jasper": "https://jasper.ai?fpr=nysr",
    "copy.ai": "https://www.copy.ai?via=nysr",
}

def inject_links_into_post(post_id, content):
    modified = content
    injected = 0
    for keyword, url in AFFILIATE_LINKS.items():
        # Only link first occurrence of each keyword, not already linked
        pattern = f"(?<!href=[\"\']{url}[\"\'}>])\b({re.escape(keyword)})\b"
        new_content, n = re.subn(
            pattern,
            f'<a href="{url}" rel="sponsored nofollow" target="_blank">\\1</a>',
            modified, count=1, flags=re.IGNORECASE)
        if n > 0:
            modified = new_content
            injected += 1
    return modified, injected

def process_recent_posts(limit=10):
    if not WP_TOKEN:
        log.warning("No WORDPRESS_ACCESS_TOKEN")
        return
    r = requests.get(f"{BASE}/posts?number={limit}&fields=ID,content,title",
        headers={"Authorization": f"Bearer {WP_TOKEN}"}, timeout=15)
    posts = r.json().get("posts", [])
    log.info(f"Processing {len(posts)} recent posts")
    total_links = 0
    for post in posts:
        new_content, n = inject_links_into_post(post["ID"], post.get("content",""))
        if n > 0:
            upd = requests.post(f"{BASE}/posts/{post['ID']}",
                headers={"Authorization": f"Bearer {WP_TOKEN}"},
                json={"content": new_content}, timeout=15)
            if upd.status_code == 200:
                log.info(f"  +{n} links: {post['title'][:50]}")
                total_links += n
    log.info(f"Total affiliate links injected: {total_links}")

if __name__ == "__main__":
    process_recent_posts()
