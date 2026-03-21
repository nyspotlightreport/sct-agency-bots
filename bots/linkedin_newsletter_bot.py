#!/usr/bin/env python3
"""
LinkedIn Newsletter Bot — NYSR Agency
Publishes weekly newsletter to LinkedIn (350M+ professionals).
LinkedIn newsletters get 5-10x more reach than regular posts.
Monetizes via: Stripe consulting offers, Beehiiv cross-promo.
"""
import os, requests, json, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("LinkedInNewsletterBot")

LI_TOKEN  = os.environ.get("LINKEDIN_ACCESS_TOKEN","")
WP_TOKEN  = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE   = os.environ.get("WORDPRESS_SITE_ID","")

NEWSLETTER_TEMPLATE = """
{headline}

---

{intro}

This week I want to break down {topic}.

{main_content}

---

**The 3 takeaways:**

1. {takeaway_1}
2. {takeaway_2}  
3. {takeaway_3}

---

If this was useful, subscribe to the full NY Spotlight Report newsletter:
→ nyspotlightreport.com

Need help implementing any of this? Reply or book a call:
→ [Stripe consulting link]

— S.C. Thomas, Chairman · NY Spotlight Report
"""

def get_latest_wp_post():
    r = requests.get(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts?number=1",
        headers={"Authorization": f"Bearer {WP_TOKEN}"}, timeout=15)
    posts = r.json().get("posts",[])
    return posts[0] if posts else None

def post_article(title, content):
    if not LI_TOKEN:
        log.warning("No LINKEDIN_ACCESS_TOKEN")
        return False
    r = requests.get("https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {LI_TOKEN}"}, timeout=10)
    if r.status_code != 200: return False
    uid = r.json().get("sub","")
    body = {
        "author": f"urn:li:person:{uid}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content[:3000]},
                "shareMediaCategory": "ARTICLE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r2 = requests.post("https://api.linkedin.com/v2/ugcPosts",
        headers={"Authorization": f"Bearer {LI_TOKEN}", "Content-Type": "application/json"},
        json=body, timeout=15)
    return r2.status_code == 201

if __name__ == "__main__":
    post = get_latest_wp_post()
    if post:
        ok = post_article(post["title"], post.get("excerpt","") + "\n\nRead more: nyspotlightreport.com")
        log.info(f"LinkedIn: {'✅' if ok else '⚠️ token may need refresh'}")
    log.info("LinkedIn newsletter drives 5-10x more organic reach than posts")
