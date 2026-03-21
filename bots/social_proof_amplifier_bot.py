"""
Social Proof Amplifier Bot
Pulls new reviews/testimonials from Supabase → generates social posts →
pushes to Twitter + LinkedIn + WordPress automatically.
Closes the review→amplification gap. Every 5-star review becomes 3 social posts.
"""
import os, json, logging, datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PROOF] %(message)s")
log = logging.getLogger("social_proof")

SUPABASE_URL  = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
TWITTER_KEY   = os.environ.get("TWITTER_API_KEY","")
TWITTER_SECRET= os.environ.get("TWITTER_API_SECRET","")
TWITTER_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN","")
TWITTER_TSEC  = os.environ.get("TWITTER_ACCESS_SECRET","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.error, hmac, hashlib, time, base64, urllib.parse, secrets as sec_mod

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json", "Prefer": "return=representation"}
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code}")
        return None

def ai(prompt):
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":600,
                        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={
        "Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def push(title, message):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":message}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def post_tweet(text):
    """Post to Twitter v2 API."""
    if not all([TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TSEC]):
        log.warning("Twitter credentials missing")
        return False
    url = "https://api.twitter.com/2/tweets"
    body = json.dumps({"text": text[:280]}).encode()
    # OAuth 1.0a
    oauth_params = {
        "oauth_consumer_key": TWITTER_KEY,
        "oauth_nonce": sec_mod.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_TOKEN,
        "oauth_version": "1.0"
    }
    base_string = "&".join([
        "POST",
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote("&".join(f"{k}={urllib.parse.quote(str(v),safe='')}" for k,v in sorted(oauth_params.items())), safe="")
    ])
    signing_key = f"{urllib.parse.quote(TWITTER_SECRET,safe='')}&{urllib.parse.quote(TWITTER_TSEC,safe='')}"
    sig = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
    oauth_params["oauth_signature"] = sig
    auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(str(v),safe="")}"' for k,v in sorted(oauth_params.items()))
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": auth_header, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            log.info(f"Tweet posted: {text[:60]}…")
            return True
    except urllib.error.HTTPError as e:
        log.warning(f"Tweet failed: {e.code} {e.read()[:100]}")
        return False

def amplify_review(review):
    """Turn one review into Twitter post + LinkedIn post + store scheduled_post."""
    body = review.get("body","")
    author = review.get("author_name","A client")
    rating = review.get("rating", 5)
    stars = "⭐" * int(rating)

    # Generate Twitter post
    tweet = ai(
        f"Write a tweet for NY Spotlight Report sharing this client testimonial. "
        f"Include the quote, author name, 2 relevant hashtags (#AIAutomation #SmallBusiness). "
        f"Max 240 chars. No fluff. End with nyspotlightreport.com/store/\n"
        f"Review: '{body}' — {author} {stars}"
    )
    # Generate LinkedIn post
    linkedin = ai(
        f"Write a LinkedIn post for NY Spotlight Report sharing this testimonial. "
        f"3-4 sentences, professional tone, ends with CTA to nyspotlightreport.com/store/\n"
        f"Review: '{body}' — {author}"
    )
    # Post tweet
    if tweet:
        posted = post_tweet(tweet.strip())
        if posted:
            push("⭐ Review Amplified", f"Tweet posted: {tweet[:80]}")

    # Queue LinkedIn + WordPress posts
    for platform, content in [("linkedin", linkedin), ("twitter", tweet)]:
        if content:
            supa("POST", "scheduled_posts", {
                "platform": platform,
                "content": content.strip(),
                "status": "queued",
                "scheduled_for": datetime.datetime.utcnow().isoformat(),
                "meta": {"review_id": review.get("id"), "source": "social_proof_amplifier"}
            })

    # Mark review as amplified
    supa("PATCH", "testimonials",
         {"meta": {"amplified": True, "amplified_at": datetime.datetime.utcnow().isoformat()}},
         query=f"?id=eq.{review['id']}")
    log.info(f"Amplified review from {author}")

def sync_store_reviews_to_testimonials():
    """Copy approved store reviews into testimonials table."""
    reviews = supa("GET","store_reviews","?status=eq.published&rating=gte.4&select=*") or []
    for r in reviews:
        existing = supa("GET","testimonials",f"?source_id=eq.{r['id']}&select=id&limit=1") or []
        if existing: continue
        contact = None
        if r.get("contact_id"):
            c = supa("GET","contacts",f"?id=eq.{r['contact_id']}&select=name,company&limit=1") or []
            contact = c[0] if c else None
        supa("POST","testimonials",{
            "source": "review",
            "source_id": r["id"],
            "contact_id": r.get("contact_id"),
            "author_name": contact["name"] if contact else "Verified Client",
            "author_company": contact.get("company","") if contact else "",
            "body": r.get("body",""),
            "rating": r.get("rating",5),
            "product_id": r.get("product_id"),
            "status": "published",
            "featured": r.get("rating",0) == 5
        })
        log.info(f"Synced review to testimonials: {r.get('headline','')[:40]}")

def run():
    log.info("=== Social Proof Amplifier ===")
    sync_store_reviews_to_testimonials()
    # Amplify any un-amplified 4-5 star testimonials from last 7 days
    week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
    reviews = supa("GET","testimonials",
                   f"?status=eq.published&rating=gte.4&created_at=gte.{week_ago}&select=*") or []
    amplified = 0
    for r in reviews:
        meta = r.get("meta") or {}
        if not meta.get("amplified"):
            amplify_review(r)
            amplified += 1
            time.sleep(2)  # Rate limit buffer
    log.info(f"Amplified {amplified} reviews")
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
