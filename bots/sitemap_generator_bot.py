"""
Sitemap Generator Bot — Enhanced
Pulls all pages from sitemap_pages table + SEO pages + wiki pages.
Builds sitemap.xml and deploys to Netlify. Pings Google + Bing.
Every new wiki/store page gets indexed within 24 hours.
"""
import os, json, logging, datetime, urllib.request, urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SITEMAP] %(message)s")
log = logging.getLogger("sitemap")

SUPABASE_URL   = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY   = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
NETLIFY_TOKEN  = os.environ.get("NETLIFY_AUTH_TOKEN","")
NETLIFY_SITE   = os.environ.get("NETLIFY_SITE_ID","8ef722e1-4110-42af-8ddb-ff6c2ce1745e")
PUSHOVER_API   = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER  = os.environ.get("PUSHOVER_USER_KEY","")

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

def push(title, msg):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req,timeout=10)
    except Exception:  # noqa: bare-except

        pass
def build_sitemap():
    today = datetime.date.today().isoformat()
    urls = []

    # Core pages from sitemap_pages table
    pages = supa("GET","sitemap_pages","?active=eq.true&order=priority.desc") or []
    for p in pages:
        urls.append({
            "loc": p["url"], "priority": p.get("priority",0.5),
            "changefreq": p.get("changefreq","weekly"),
            "lastmod": p.get("last_mod", today)
        })

    # Wiki pages
    wiki = supa("GET","wiki_pages","?status=eq.published&select=slug,updated_at") or []
    for w in wiki:
        slug = w.get("slug","")
        lastmod = (w.get("updated_at","") or today)[:10]
        url = f"https://nyspotlightreport.com/wiki/{slug}/"
        if not any(u["loc"] == url for u in urls):
            urls.append({"loc":url,"priority":0.7,"changefreq":"weekly","lastmod":lastmod})

    # SEO opportunity pages (published content URLs)
    seo = supa("GET","seo_opportunities","?status=eq.published&content_url=not.is.null&select=content_url,created_at") or []
    for s in seo:
        content_url = s.get("content_url","")
        if content_url and not any(u["loc"] == content_url for u in urls):
            urls.append({"loc":content_url,"priority":0.6,"changefreq":"monthly",
                         "lastmod":(s.get("created_at","") or today)[:10]})

    # Build XML
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_lines.extend([
            "  <url>",
            f"    <loc>{u['loc']}</loc>",
            f"    <lastmod>{u['lastmod']}</lastmod>",
            f"    <changefreq>{u['changefreq']}</changefreq>",
            f"    <priority>{u['priority']}</priority>",
            "  </url>"
        ])
    xml_lines.append("</urlset>")
    return "\n".join(xml_lines), len(urls)

def deploy_to_netlify(sitemap_xml):
    """Deploy sitemap.xml to Netlify via Files API."""
    if not NETLIFY_TOKEN: return False
    import hashlib
    sha1 = hashlib.sha1(sitemap_xml.encode()).hexdigest()
    # Create deploy with sitemap
    deploy_data = json.dumps({
        "files": {"/sitemap.xml": sha1},
        "async": False
    }).encode()
    req = urllib.request.Request(
        f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE}/deploys",
        data=deploy_data, method="POST",
        headers={"Authorization":f"Bearer {NETLIFY_TOKEN}","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            d = json.loads(r.read())
            deploy_id = d.get("id","")
            if not deploy_id: return False
        # Upload the file
        content = sitemap_xml.encode()
        req2 = urllib.request.Request(
            f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/sitemap.xml",
            data=content, method="PUT",
            headers={"Authorization":f"Bearer {NETLIFY_TOKEN}","Content-Type":"application/octet-stream"})
        with urllib.request.urlopen(req2,timeout=20) as r:
            log.info(f"Sitemap deployed: {len(content)} bytes")
            return True
    except Exception as e:
        log.warning(f"Netlify deploy failed: {e}")
        return False

def ping_search_engines(url_count):
    """Ping Google and Bing to re-crawl sitemap."""
    sitemap_url = "https://nyspotlightreport.com/sitemap.xml"
    engines = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}"
    ]
    for eng in engines:
        try:
            req = urllib.request.Request(eng, headers={"User-Agent":"NYSR-Bot/1.0"})
            with urllib.request.urlopen(req,timeout=10) as r:
                log.info(f"Pinged: {eng[:50]} → {r.status}")
        except Exception as e:
            log.warning(f"Ping failed {eng[:40]}: {e}")

def run():
    log.info("=== Sitemap Generator ===")
    sitemap_xml, url_count = build_sitemap()
    log.info(f"Built sitemap: {url_count} URLs")

    # Write to repo via GitHub API
    import base64
    GH_TOKEN = os.environ.get("GH_PAT","")
    if GH_TOKEN:
        import json as _json
        REPO = "nyspotlightreport/sct-agency-bots"
        content_b64 = base64.b64encode(sitemap_xml.encode()).decode()
        # Get current SHA
        h = {"Authorization":f"token {GH_TOKEN}","Content-Type":"application/json"}
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/contents/site/sitemap.xml", headers=h)
            with urllib.request.urlopen(req,timeout=10) as r:
                sha = _json.load(r).get("sha","")
        except: sha = ""
        payload = {"message":f"chore: update sitemap ({url_count} URLs)","content":content_b64}
        if sha: payload["sha"] = sha
        req2 = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/contents/site/sitemap.xml",
            data=_json.dumps(payload).encode(), method="PUT", headers=h)
        try:
            with urllib.request.urlopen(req2,timeout=15) as r:
                log.info(f"Sitemap pushed to GitHub: {r.status}")
        except Exception as e:
            log.warning(f"GitHub push failed: {e}")

    ping_search_engines(url_count)
    push("🗺️ Sitemap Updated", f"{url_count} URLs indexed. Google + Bing pinged.")
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
