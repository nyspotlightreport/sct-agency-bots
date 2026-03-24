#!/usr/bin/env python3
"""
Amazon Associates Deep Link Injector — NYSR Agency
Finds product mentions in all blog posts and converts to
Amazon affiliate links. Commission: 1-10% per sale.
Associate Tag: nysr-20 (register at affiliate-program.amazon.com)
"""
import os, requests, re, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("AmazonAssocBot")

WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE  = os.environ.get("WORDPRESS_SITE_ID", "")
AMZN_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG", "nysr-20")

# High-converting product categories to auto-link
PRODUCT_KEYWORDS = {
    "planner":      f"https://amzn.to/planners?tag={AMZN_TAG}",
    "notebook":     f"https://www.amazon.com/s?k=notebook&tag={AMZN_TAG}",
    "journal":      f"https://www.amazon.com/s?k=journal&tag={AMZN_TAG}",
    "budget planner":f"https://www.amazon.com/s?k=budget+planner&tag={AMZN_TAG}",
    "chatgpt":      f"https://www.amazon.com/s?k=ai+productivity+book&tag={AMZN_TAG}",
    "passive income":f"https://www.amazon.com/s?k=passive+income+book&tag={AMZN_TAG}",
    "side hustle":  f"https://www.amazon.com/s?k=side+hustle&tag={AMZN_TAG}",
    "sudoku":       f"https://www.amazon.com/s?k=sudoku+book&tag={AMZN_TAG}",
    "word search":  f"https://www.amazon.com/s?k=word+search+book&tag={AMZN_TAG}",
    "habit tracker":f"https://www.amazon.com/s?k=habit+tracker&tag={AMZN_TAG}",
    "meal prep":    f"https://www.amazon.com/s?k=meal+prep+containers&tag={AMZN_TAG}",
    "workout":      f"https://www.amazon.com/s?k=home+gym&tag={AMZN_TAG}",
}

def get_posts(n=20):
    r = requests.get(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts?number={n}",
        headers={"Authorization": f"Bearer {WP_TOKEN}"}, timeout=15)
    return r.json().get("posts", []) if r.status_code == 200 else []

def inject_amazon_links(content):
    modified = content
    count = 0
    for kw, url in PRODUCT_KEYWORDS.items():
        pattern = r'(?<!["\x27>])(' + re.escape(kw) + r')(?!["\x27<])'
        new, n = re.subn(
            pattern,
            f'<a href="{url}" rel="sponsored nofollow" target="_blank">\\1</a>',
            modified, count=1, flags=re.IGNORECASE)
        if n:
            modified = new
            count += 1
    return modified, count

if __name__ == "__main__":
    posts = get_posts(20)
    total = 0
    for p in posts:
        new_content, n = inject_amazon_links(p.get("content",""))
        if n > 0:
            requests.post(
                f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts/{p['ID']}",
                headers={"Authorization": f"Bearer {WP_TOKEN}"},
                json={"content": new_content}, timeout=15)
            log.info(f"+{n} Amazon links: {p['title'][:50]}")
            total += n
    log.info(f"Total Amazon links injected: {total}")
    log.info("Register: affiliate-program.amazon.com -> tag: nysr-20")
