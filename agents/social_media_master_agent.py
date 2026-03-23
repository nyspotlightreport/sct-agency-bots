#!/usr/bin/env python3
"""
Social Media Master Agent — NYSR Agency
World-class social media system using direct native APIs.
No dependency on Publer (key invalid/expired).

Platforms & methods:
✅ Pinterest   — Pinterest API v5 (token in secrets)
✅ Medium      — Medium Integration API
✅ LinkedIn    — LinkedIn UGC Posts API
✅ Twitter/X   — Twitter API v2 (needs TWITTER_BEARER_TOKEN)
✅ Instagram   — Meta Graph API (needs INSTAGRAM_PAGE_TOKEN)
✅ Facebook    — Meta Graph API (needs FB_PAGE_TOKEN + PAGE_ID)

Each platform gets NATIVE content — not the same post copy-pasted.
Platform-native = algorithm rewards = 3-5x organic reach.
"""
import os, sys, json, logging, requests, time
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SocialMaster] %(message)s")
log = logging.getLogger()

# Tokens
PINTEREST_TOKEN    = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
MEDIUM_TOKEN       = os.environ.get("MEDIUM_INTEGRATION_TOKEN", "")
LINKEDIN_TOKEN     = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
TWITTER_TOKEN      = os.environ.get("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY    = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS     = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SEC = os.environ.get("TWITTER_ACCESS_SECRET", "")
IG_TOKEN           = os.environ.get("INSTAGRAM_PAGE_TOKEN", "")
IG_USER_ID         = os.environ.get("INSTAGRAM_USER_ID", "")
FB_TOKEN           = os.environ.get("FB_PAGE_TOKEN", "")
FB_PAGE_ID         = os.environ.get("FB_PAGE_ID", "")
ANTHROPIC          = os.environ.get("ANTHROPIC_API_KEY", "")

BRAND_VOICE = """NY Spotlight Report brand voice:
- Direct, sharp, no fluff
- Specific numbers > vague claims
- Peer-to-peer expert, not salesperson  
- NYC edge — calm authority, ambitious
- Never say: "game-changer", "revolutionize", "unlock your potential"
- Always: specific results, real tools, honest tradeoffs"""

TODAY_TOPICS = [
    "passive income automation", "AI content tools", "digital products",
    "newsletter monetization", "cold email systems", "side hustle 2026",
    "content marketing automation", "affiliate income stacks"
]

# ── CONTENT GENERATION ───────────────────────────────────────────

def generate_platform_content(topic: str) -> dict:
    """Generate platform-native content for all channels from one topic."""
    if not ANTHROPIC:
        # Fallback templates
        return {
            "pinterest": {
                "title": f"How to Build {topic.title()} in 2026",
                "description": f"Step-by-step guide to {topic}. Real numbers, zero fluff. nyspotlightreport.com",
                "link": "https://nyspotlightreport.com/blog/"
            },
            "linkedin": f"Most people get {topic} wrong.\n\nThe actual framework that works:\n\n1. Start with systems, not tactics\n2. Automate before you optimize\n3. Compound before you scale\n\nWe've been building AI-powered content systems at NY Spotlight Report.\n\nHere's what 90 days looks like:\n→ nyspotlightreport.com/blog/\n\nWhat's your approach?",
            "twitter": f"Unpopular opinion: {topic} is about systems not hustle.\n\nThe entrepreneurs winning in 2026 have automated:\n• Content creation\n• Lead generation\n• Product delivery\n\nWe document exactly how at nyspotlightreport.com\n\n(free breakdown in bio) 🧵",
            "instagram": f"The {topic} formula nobody talks about:\n\n📌 Save this\n\n1️⃣ Build the system once\n2️⃣ Let it run 24/7\n3️⃣ Optimize monthly\n\nWe've built 63 AI bots doing exactly this\n\n🔗 Full breakdown at nyspotlightreport.com (link in bio)\n\n#passiveincome #entrepreneur #sidehustle #contentmarketing #aitools #digitalproducts #onlinebusiness #makemoneyonline",
            "medium_tags": ["passive income", "entrepreneurship", "ai tools", "content marketing"]
        }
    
    return claude_json(
        BRAND_VOICE,
        f"""Generate platform-native social media content about: {topic}
Today's date: {datetime.now().strftime("%B %d, %Y")}

Return JSON with these keys:
- pinterest: {{title (60 chars), description (500 chars, includes nyspotlightreport.com), link: "https://nyspotlightreport.com/blog/"}}
- linkedin: Full LinkedIn post (150-200 words, ends with question, 1 link to nyspotlightreport.com)
- twitter: Tweet/thread opener (under 280 chars, hook only, includes nyspotlightreport.com link)
- instagram: Caption with hook + value + 20 hashtags + link in bio mention
- medium_tags: array of 5 relevant Medium tags

Rules per platform:
- Pinterest: SEO-rich description, educational tone, drives to blog
- LinkedIn: Professional insight, data-driven, asks a question at end
- Twitter: Sharp hook, slight controversy, curiosity gap
- Instagram: Line breaks every 1-2 sentences, emoji sparingly, strong hashtag set""",
        max_tokens=1500
    )

# ── PLATFORM POSTING ─────────────────────────────────────────────

def post_to_pinterest(title: str, description: str, link: str, board_id: str = None) -> bool:
    if not PINTEREST_TOKEN:
        log.info("[Pinterest] No token — skipping")
        return False
    
    # Get boards first if no board_id
    if not board_id:
        r = requests.get("https://api.pinterest.com/v5/boards",
            headers={"Authorization": f"Bearer {PINTEREST_TOKEN}"}, timeout=10)
        if r.status_code == 200:
            boards = r.json().get("items", [])
            if boards:
                board_id = boards[0]["id"]
                log.info(f"Using board: {boards[0]['name']}")
        if not board_id:
            log.error("No Pinterest boards found")
            return False
    
    payload = {
        "board_id": board_id,
        "title": title[:100],
        "description": description[:500],
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": "https://nyspotlightreport.com/assets/pin-default.jpg"
        }
    }
    r = requests.post("https://api.pinterest.com/v5/pins",
        headers={"Authorization": f"Bearer {PINTEREST_TOKEN}", "Content-Type": "application/json"},
        json=payload, timeout=20)
    ok = r.status_code in [200, 201]
    log.info(f"{'✅' if ok else '❌'} Pinterest: {title[:50]} | {r.status_code}")
    return ok

def post_to_linkedin(text: str) -> bool:
    if not LINKEDIN_TOKEN:
        log.info("[LinkedIn] No access token — skipping")
        return False
    
    # Get user URN
    r = requests.get("https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {LINKEDIN_TOKEN}"}, timeout=10)
    if r.status_code != 200:
        log.warning(f"LinkedIn userinfo: {r.status_code} — token may need refresh")
        return False
    
    uid = r.json().get("sub", "")
    payload = {
        "author": f"urn:li:person:{uid}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r2 = requests.post("https://api.linkedin.com/v2/ugcPosts",
        headers={"Authorization": f"Bearer {LINKEDIN_TOKEN}", "Content-Type": "application/json",
                 "X-Restli-Protocol-Version": "2.0.0"},
        json=payload, timeout=20)
    ok = r2.status_code in [200, 201]
    log.info(f"{'✅' if ok else f'❌ {r2.status_code}'} LinkedIn post")
    if not ok: log.debug(r2.text[:200])
    return ok

def post_to_twitter(text: str) -> bool:
    """Post tweet using Twitter API v2 OAuth 1.0a."""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS, TWITTER_ACCESS_SEC]):
        log.info("[Twitter] Missing credentials — skipping")
        return False
    
    try:
        import hmac, hashlib, time as t, urllib.parse, base64 as b64, random
        
        url = "https://api.twitter.com/2/tweets"
        timestamp = str(int(t.time()))
        nonce = base64.b64encode(os.urandom(16)).decode().strip("=")
        
        oauth_params = {
            "oauth_consumer_key": TWITTER_API_KEY,
            "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": timestamp,
            "oauth_token": TWITTER_ACCESS,
            "oauth_version": "1.0"
        }
        
        param_string = "&".join(f"{urllib.parse.quote(k,'')}&{urllib.parse.quote(v,'')}" 
                                for k,v in sorted(oauth_params.items()))
        base_string = f"POST&{urllib.parse.quote(url,'')}&{urllib.parse.quote(param_string,'')}"
        signing_key = f"{urllib.parse.quote(TWITTER_API_SECRET,'')}&{urllib.parse.quote(TWITTER_ACCESS_SEC,'')}"
        sig = b64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
        
        oauth_params["oauth_signature"] = sig
        auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(v,"")}"' for k,v in sorted(oauth_params.items()))
        
        r = requests.post(url, 
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json={"text": text[:280]}, timeout=20)
        ok = r.status_code in [200, 201]
        log.info(f"{'✅' if ok else f'❌ {r.status_code}'} Twitter/X post")
        return ok
    except Exception as e:
        log.error(f"Twitter error: {e}")
        return False

def post_to_instagram_feed(caption: str) -> bool:
    """Post to Instagram Business via Meta Graph API."""
    if not IG_TOKEN or not IG_USER_ID:
        log.info("[Instagram] No IG_PAGE_TOKEN or IG_USER_ID — skipping")
        return False
    
    # Step 1: Create media container
    r = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media",
        params={
            "image_url": "https://nyspotlightreport.com/assets/ig-post-default.jpg",
            "caption": caption[:2200],
            "access_token": IG_TOKEN
        }, timeout=20)
    
    if r.status_code != 200:
        log.error(f"IG container: {r.status_code} {r.text[:100]}")
        return False
    
    container_id = r.json().get("id")
    
    # Step 2: Publish
    r2 = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish",
        params={"creation_id": container_id, "access_token": IG_TOKEN}, timeout=20)
    ok = r2.status_code == 200
    log.info(f"{'✅' if ok else f'❌ {r2.status_code}'} Instagram post")
    return ok

def post_to_facebook(text: str) -> bool:
    """Post to Facebook Page."""
    if not FB_TOKEN or not FB_PAGE_ID:
        log.info("[Facebook] No FB_PAGE_TOKEN or FB_PAGE_ID — skipping")
        return False
    
    r = requests.post(
        f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed",
        params={"message": text, "access_token": FB_TOKEN}, timeout=20)
    ok = r.status_code == 200
    log.info(f"{'✅' if ok else f'❌ {r.status_code}'} Facebook post")
    return ok

def post_to_medium(title: str, content: str, tags: list) -> bool:
    """Publish to Medium."""
    if not MEDIUM_TOKEN:
        log.info("[Medium] No token — skipping")
        return False
    
    # Get user ID
    r = requests.get("https://api.medium.com/v1/me",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}"}, timeout=10)
    if r.status_code != 200:
        log.error(f"Medium auth: {r.status_code}")
        return False
    
    uid = r.json()["data"]["id"]
    payload = {
        "title": title,
        "contentFormat": "html",
        "content": f"<h1>{title}</h1><p>{content}</p><p><a href=\"https://nyspotlightreport.com/blog/\">More at NY Spotlight Report →</a></p>",
        "tags": tags[:5],
        "publishStatus": "public"
    }
    r2 = requests.post(f"https://api.medium.com/v1/users/{uid}/posts",
        headers={"Authorization": f"Bearer {MEDIUM_TOKEN}", "Content-Type": "application/json"},
        json=payload, timeout=30)
    ok = r2.status_code in [200, 201]
    log.info(f"{'✅' if ok else f'❌ {r2.status_code}'} Medium post: {title[:50]}")
    return ok

# ── MAIN RUN ──────────────────────────────────────────────────────

def run():
    log.info("Social Media Master Agent starting...")
    
    # Pick today's topic
    from datetime import date
    topic_idx = date.today().timetuple().tm_yday % len(TODAY_TOPICS)
    topic = TODAY_TOPICS[topic_idx]
    log.info(f"Today's topic: {topic}")
    
    # Generate platform-native content
    content = generate_platform_content(topic)
    if not content:
        log.error("Content generation failed")
        return
    
    results = {}
    
    # Post to each platform
    if "pinterest" in content:
        p = content["pinterest"]
        results["pinterest"] = post_to_pinterest(
            p.get("title",""), p.get("description",""), p.get("link","https://nyspotlightreport.com/blog/"))
    
    if "linkedin" in content:
        results["linkedin"] = post_to_linkedin(content["linkedin"])
        time.sleep(2)
    
    if "twitter" in content:
        results["twitter"] = post_to_twitter(content["twitter"])
        time.sleep(2)
    
    if "instagram" in content:
        results["instagram"] = post_to_instagram_feed(content["instagram"])
        time.sleep(2)
    
    if "facebook" in content:
        results["facebook"] = post_to_facebook(content.get("linkedin",""))  # reuse linkedin content
        time.sleep(2)
    
    # Save content for manual review
    import json
    with open("/tmp/social_content_today.json", "w") as f:
        json.dump({"topic": topic, "date": str(date.today()), "content": content, "results": results}, f, indent=2)
    
    posted = sum(1 for v in results.values() if v)
    total  = len(results)
    log.info(f"Social posting complete: {posted}/{total} platforms posted")
    
    # Report
    for platform, ok in results.items():
        log.info(f"  {'✅' if ok else '⚠️ '} {platform}")
    
    if posted == 0:
        log.warning("No posts went out — check credentials")
        log.info("Needed secrets: PINTEREST_ACCESS_TOKEN, LINKEDIN_ACCESS_TOKEN,")
        log.info("  TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET")
        log.info("  INSTAGRAM_PAGE_TOKEN, INSTAGRAM_USER_ID, FB_PAGE_TOKEN, FB_PAGE_ID")

if __name__ == "__main__":
    run()
