#!/usr/bin/env python3
"""
Social Scheduler Bot — Daily multi-platform content distribution.
Content → Revenue pipeline: post → traffic → leads → sales.

Platforms: LinkedIn, Twitter/X, WordPress blog
Strategy:
  - LinkedIn: thought leadership (Mon/Wed/Fri) → agency founders/marketers
  - Twitter: hot takes + engagement bait (daily) → developer/startup audience
  - WordPress: long-form SEO content (2x/week) → organic search traffic

Uses content from ContentBot + AI generation.
Posts directly via APIs when tokens available.
"""
import os, sys, json, logging, random
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None

import urllib.request, urllib.parse, base64
log = logging.getLogger(__name__)

TWITTER_BEARER = os.environ.get("TWITTER_BEARER_TOKEN","")
TWITTER_KEY    = os.environ.get("TWITTER_API_KEY","")
TWITTER_SECRET = os.environ.get("TWITTER_API_SECRET","")
TWITTER_ACCESS = os.environ.get("TWITTER_ACCESS_TOKEN","")
TWITTER_ASECRET= os.environ.get("TWITTER_ACCESS_TOKEN_SECRET","")
WP_TOKEN       = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE_ID     = os.environ.get("WORDPRESS_SITE_ID","")
PUSHOVER_API   = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER  = os.environ.get("PUSHOVER_USER_KEY","")
ANTHROPIC      = os.environ.get("ANTHROPIC_API_KEY","")

CONTENT_PILLARS = [
    {"pillar": "AI agency results",    "tone": "data-driven", "audience": "agency owners"},
    {"pillar": "Passive income tips",  "tone": "aspirational","audience": "solopreneurs"},
    {"pillar": "Automation how-to",    "tone": "educational", "audience": "marketers"},
    {"pillar": "NYSR system behind-the-scenes", "tone": "transparent", "audience": "founders"},
    {"pillar": "AI tool comparison",   "tone": "authoritative","audience": "tech decision-makers"},
]

CTA_ROTATION = [
    "→ Comment with your biggest automation challenge",
    "→ Link in bio to grab the free AI agency starter kit",
    "→ DM me "BOTS" and I'll send you the system map",
    "→ Save this for later — you'll need it",
    "→ Share with someone still doing this manually",
]

def generate_linkedin_post(pillar: dict) -> str:
    return claude(
        "You are a LinkedIn thought leader in AI agency automation. Write viral, value-dense posts.",
        f"""Write a LinkedIn post for this pillar: {pillar["pillar"]}
Tone: {pillar["tone"]} | Audience: {pillar["audience"]}
CTA to include: {random.choice(CTA_ROTATION)}

LinkedIn post format:
- Hook (first line must stop the scroll — question OR bold stat OR contrarian take)
- 3-5 short punchy paragraphs (no fluff, every line earns its place)
- Space between paragraphs
- End with CTA
- 3-5 relevant hashtags on the last line

Max 1300 characters. Sound like a real operator, not a content creator.""",
        max_tokens=400
    ) or f"The biggest mistake agencies make: doing manually what AI can do automatically.\n\nWe built 200 bots to run our entire operation.\n\nResult? More clients. Less grind.\n\n{random.choice(CTA_ROTATION)}\n\n#AIAgency #Automation #PassiveIncome"

def generate_tweet(pillar: dict) -> str:
    return claude(
        "You write high-engagement tweets for AI/automation audience. Short, punchy, retweet-worthy.",
        f"""Write a tweet about: {pillar["pillar"]}
Style: {pillar["tone"]} | Max 260 chars
Options: hot take, stat, listicle thread starter, behind-the-scenes, question
No hashtag spam. 0-2 relevant hashtags max. Sound human.""",
        max_tokens=100
    ) or "Built 200 AI bots that run my agency 24/7.\n\nPassive income while I sleep.\nLeads generated automatically.\nContent posted without me.\n\nThe system is the business now. ↓\n\n(thread)"

def generate_blog_post(pillar: dict) -> dict:
    return claude_json(
        "You write high-ranking SEO blog posts for AI agency owners.",
        f"""Write a complete SEO-optimized blog post for: {pillar["pillar"]}
Target audience: {pillar["audience"]}
Return JSON: {{
  "title": "H1 title (includes keyword, max 60 chars)",
  "slug": "url-slug",
  "meta_description": "155 char SEO description",
  "content": "Full post in HTML (800-1200 words, h2 headers, bullet points, 1 CTA at end linking to nyspotlightreport.com/pricing/)",
  "categories": ["AI", "Automation"],
  "tags": ["ai agency","automation","passive income","lead generation"]
}}""",
        max_tokens=1500
    ) or {
        "title": f"How to Use AI for {pillar['pillar']}",
        "slug":  pillar["pillar"].lower().replace(" ","-"),
        "content": f"<h1>AI and {pillar['pillar']}</h1><p>AI is transforming how agencies operate...</p>",
        "categories":["AI"],
        "tags":["ai","automation"]
    }

def post_to_twitter(text: str) -> bool:
    if not all([TWITTER_KEY,TWITTER_SECRET,TWITTER_ACCESS,TWITTER_ASECRET]):
        log.warning("Twitter credentials incomplete — saving draft")
        return False
    try:
        import hmac, hashlib, time
        timestamp   = str(int(time.time()))
        nonce       = base64.b64encode(os.urandom(16)).decode().rstrip("=")
        base_url    = "https://api.twitter.com/2/tweets"
        params      = {"oauth_consumer_key":TWITTER_KEY,"oauth_nonce":nonce,"oauth_signature_method":"HMAC-SHA1",
                       "oauth_timestamp":timestamp,"oauth_token":TWITTER_ACCESS,"oauth_version":"1.0"}
        base_str    = f"POST&{urllib.parse.quote(base_url,safe='')}&{urllib.parse.quote(urllib.parse.urlencode(sorted(params.items())),safe='')}"
        signing_key = f"{urllib.parse.quote(TWITTER_SECRET,safe='')}&{urllib.parse.quote(TWITTER_ASECRET,safe='')}"
        sig         = base64.b64encode(hmac.new(signing_key.encode(),base_str.encode(),hashlib.sha1).digest()).decode()
        params["oauth_signature"] = sig
        auth_header = "OAuth " + ", ".join([f'{urllib.parse.quote(k,safe="")}="{urllib.parse.quote(v,safe="")}"' for k,v in sorted(params.items())])
        req = urllib.request.Request(base_url,
            data=json.dumps({"text":text[:280]}).encode(),
            headers={"Content-Type":"application/json","Authorization":auth_header},
            method="POST"
        )
        with urllib.request.urlopen(req,timeout=10) as r:
            return r.status == 201
    except Exception as e:
        log.warning(f"Twitter post failed: {e}")
        return False

def post_to_wordpress(post: dict) -> bool:
    if not WP_TOKEN or not WP_SITE_ID: return False
    try:
        payload = {
            "title":      post.get("title",""),
            "content":    post.get("content",""),
            "status":     "publish",
            "categories": post.get("categories",[]),
            "tags":       post.get("tags",[]),
            "slug":       post.get("slug",""),
        }
        req = urllib.request.Request(
            f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE_ID}/posts/new",
            data=json.dumps(payload).encode(),
            headers={"Authorization":f"Bearer {WP_TOKEN}","Content-Type":"application/json"}
        )
        with urllib.request.urlopen(req,timeout=20) as r:
            return r.status == 200
    except Exception as e:
        log.warning(f"WP post failed: {e}")
        return False

def run():
    log.info("Social Scheduler running...")
    today        = datetime.utcnow()
    day_of_week  = today.weekday()  # 0=Mon, 6=Sun
    pillar       = CONTENT_PILLARS[today.day % len(CONTENT_PILLARS)]

    posted    = 0
    scheduled = []

    # Twitter — daily
    tweet = generate_tweet(pillar)
    if post_to_twitter(tweet):
        posted += 1
        log.info(f"  ✅ Tweeted: {tweet[:60]}...")
    else:
        scheduled.append({"platform":"twitter","content":tweet[:200]})
        log.info(f"  📋 Twitter draft: {tweet[:60]}...")

    # LinkedIn — Mon/Wed/Fri
    if day_of_week in [0,2,4]:
        li_post = generate_linkedin_post(pillar)
        scheduled.append({"platform":"linkedin","content":li_post[:300]})
        log.info(f"  📋 LinkedIn draft: {li_post[:60]}...")

    # WordPress — Tue/Thu (SEO content)
    if day_of_week in [1,3]:
        blog = generate_blog_post(pillar)
        if post_to_wordpress(blog):
            posted += 1
            log.info(f"  ✅ Blog published: {blog.get('title','')}")
        else:
            scheduled.append({"platform":"wordpress","content":blog.get("title","")})

    # Save all scheduled posts to Supabase for review
    for s in scheduled:
        supabase_request("POST","scheduled_posts",{
            "platform":   s["platform"],
            "content":    s["content"][:2000],
            "status":     "draft",
            "created_at": today.isoformat(),
        })

    if PUSHOVER_API and PUSHOVER_USER:
        msg = f"📱 Social: {posted} posted | {len(scheduled)} drafted\nPillar: {pillar['pillar']}"
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Social Scheduler","message":msg}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except: pass

    log.info(f"Social Scheduler: {posted} posted | {len(scheduled)} queued")
    return {"posted":posted,"scheduled":len(scheduled),"pillar":pillar["pillar"]}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Social] %(message)s")
    run()
