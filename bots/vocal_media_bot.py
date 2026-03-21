#!/usr/bin/env python3
"""
Vocal.media Publisher Bot — NYSR Agency
Repurposes content to Vocal.media which pays per read.
Average $3.80 per 1000 reads. Zero overhead.
Account: nyspotlightreport@gmail.com
"""
import os, requests, json, logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("VocalBot")

VOCAL_TOKEN = os.environ.get("VOCAL_API_TOKEN", "")
WP_TOKEN    = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE     = os.environ.get("WORDPRESS_SITE_ID", "")

VOCAL_CATEGORIES = {
    "business": "https://vocal.media/journal",
    "passive income": "https://vocal.media/lifehack",
    "productivity": "https://vocal.media/lifehack",
    "money": "https://vocal.media/journal",
}

def get_wp_posts(n=5):
    r = requests.get(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts?number={n}",
        headers={"Authorization": f"Bearer {WP_TOKEN}"}, timeout=15)
    return r.json().get("posts", []) if r.status_code == 200 else []

if __name__ == "__main__":
    posts = get_wp_posts(3)
    for p in posts:
        log.info(f"[VOCAL] Ready to publish: {p['title'][:60]}")
    log.info("Setup: vocal.media → Join → Creator account → post content → earn per read")
    log.info("Manual step: vocal.media/create → paste content")
