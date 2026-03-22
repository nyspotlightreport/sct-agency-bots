"""
Wiki Syndication Bot
Pulls published wiki pages → reformats as LinkedIn articles + Medium posts.
Every wiki page = organic SEO + brand authority + lead gen.
Closes the wiki→traffic→revenue loop.
"""
import os, json, logging, datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WIKISYN] %(message)s")
log = logging.getLogger("wiki_syn")

SUPABASE_URL  = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
MEDIUM_TOKEN  = os.environ.get("MEDIUM_INTEGRATION_TOKEN","")
LINKEDIN_TOKEN= os.environ.get("LINKEDIN_ACCESS_TOKEN","")
WP_TOKEN      = os.environ.get("WORDPRESS_ACCESS_TOKEN","")
WP_SITE       = os.environ.get("WORDPRESS_SITE_ID","135512")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.error

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}",
               "Content-Type":"application/json","Prefer":"return=representation"}
    req = urllib.request.Request(url,data=payload,method=method,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except: return None

def ai(prompt):
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":1200,
                        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,headers={
        "Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def push(title, msg):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req,timeout=10)
    except: pass

def publish_to_wordpress(title, content, tags):
    """Publish to WordPress.com via API."""
    if not WP_TOKEN: return False
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "tags": ",".join(tags or []),
        "categories": "AI Automation",
        "format": "standard"
    }
    data = json.dumps(post_data).encode()
    req = urllib.request.Request(
        f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts/new",
        data=data, method="POST",
        headers={"Authorization":f"Bearer {WP_TOKEN}","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            result = json.loads(r.read())
            log.info(f"WordPress post: {result.get('URL','?')}")
            return True
    except urllib.error.HTTPError as e:
        log.warning(f"WordPress failed: {e.code}")
        return False

def queue_linkedin_post(content):
    """Queue LinkedIn post via scheduled_posts table."""
    supa("POST","scheduled_posts",{
        "platform":"linkedin","content":content,"status":"queued",
        "scheduled_for":datetime.datetime.utcnow().isoformat()
    })

def syndicate_wiki_page(page):
    """Convert one wiki page into syndication-ready content."""
    title = page["title"]
    content = page.get("content","")
    tags = page.get("tags",[]) or []
    if not content or len(content) < 200: return False

    # Generate SEO-optimized WordPress article from wiki content
    wp_content = ai(
        f"Convert this internal wiki page into a public-facing SEO blog article for NY Spotlight Report. "
        f"Add an intro hook, improve readability for general audience, add a CTA at the end pointing to "
        f"nyspotlightreport.com/store/ for AI automation tools. Keep the core info, make it 600-900 words. "
        f"Return only the article HTML (use <h2>, <p>, <ul> tags).\n\n"
        f"Wiki title: {title}\nContent:\n{content[:2000]}"
    )

    # Generate LinkedIn post version
    linkedin_post = ai(
        f"Write a LinkedIn post based on this wiki article. "
        f"Professional tone, 3-4 paragraphs, insight-first, ends with: "
        f"'Full guide at nyspotlightreport.com/wiki/ — free access.' "
        f"Include 3 hashtags.\n\nTitle: {title}\nSummary: {content[:500]}"
    )

    published = False

    # WordPress
    if wp_content and WP_TOKEN:
        ok = publish_to_wordpress(
            f"{title} — NY Spotlight Report Guide",
            wp_content,
            tags + ["ai-automation","nysr","business-automation"]
        )
        if ok: published = True

    # LinkedIn queue
    if linkedin_post:
        queue_linkedin_post(linkedin_post.strip())
        published = True

    if published:
        # Mark page as syndicated
        now = datetime.datetime.utcnow().isoformat()
        meta = page.get("meta") or {}
        meta["syndicated_at"] = now
        supa("PATCH","wiki_pages",{"meta":meta},query=f"?id=eq.{page['id']}")
        log.info(f"Syndicated: {title}")
        push("📡 Wiki Syndicated", f"'{title}' → WordPress + LinkedIn")
    return published

def run():
    log.info("=== Wiki Syndication Bot ===")
    # Get published pages not yet syndicated, created in last 7 days
    week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
    pages = supa("GET","wiki_pages",
                 f"?status=eq.published&created_at=gte.{week_ago}&select=*") or []
    syndicated = 0
    for page in pages:
        meta = page.get("meta") or {}
        if not meta.get("syndicated_at"):
            if syndicate_wiki_page(page):
                syndicated += 1
    log.info(f"Syndicated {syndicated} wiki pages")
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
