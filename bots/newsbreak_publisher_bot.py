#!/usr/bin/env python3
"""
NewsBreak Publisher Bot — NYSR Agency
Repurposes WordPress blog posts to NewsBreak.com
NewsBreak pays $1-5 per 1000 views + ad revenue share.
Account: nyspotlightreport@gmail.com
"""
import os, requests, json, logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("NewsBreakBot")

NB_TOKEN  = os.environ.get("NEWSBREAK_TOKEN", "")
WP_TOKEN  = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE   = os.environ.get("WORDPRESS_SITE_ID", "")

def get_latest_posts(n=5):
    r = requests.get(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts?number={n}&fields=ID,title,content,excerpt,date",
        headers={"Authorization": f"Bearer {WP_TOKEN}"}, timeout=15)
    return r.json().get("posts", []) if r.status_code == 200 else []

def post_to_newsbreak(title, body, summary):
    if not NB_TOKEN:
        log.info(f"[DRAFT] Would post: {title[:60]}")
        return True
    r = requests.post("https://www.newsbreak.com/api/v1/articles",
        headers={"Authorization": f"Bearer {NB_TOKEN}", "Content-Type": "application/json"},
        json={"title": title, "content": body, "summary": summary[:300], "category": "business"},
        timeout=15)
    return r.status_code in [200, 201]

if __name__ == "__main__":
    posts = get_latest_posts(3)
    log.info(f"Syncing {len(posts)} posts to NewsBreak")
    for p in posts:
        ok = post_to_newsbreak(p["title"], p.get("content",""), p.get("excerpt",""))
        log.info(f"{'✅' if ok else '❌'} {p['title'][:60]}")
        time.sleep(2)
    log.info("Setup: newsbreak.com/creator → register → add NEWSBREAK_TOKEN secret")
