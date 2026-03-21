#!/usr/bin/env python3
"""Sitemap Generator Bot — auto-rebuilds sitemap with all blog posts."""
import os, requests, base64
from datetime import date

GH_TOKEN = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
REPO = "nyspotlightreport/sct-agency-bots"
H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}

def run():
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/site/blog", headers=H)
    posts = [f["name"] for f in r.json() if isinstance(r.json(), list) and f.get("type") == "dir"]
    
    blog_urls = "".join([
        f"  <url><loc>https://nyspotlightreport.com/blog/{p}/</loc>"
        f"<changefreq>monthly</changefreq><priority>0.8</priority>"
        f"<lastmod>{date.today()}</lastmod></url>\n"
        for p in posts
    ])
    
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url><loc>https://nyspotlightreport.com/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
        '  <url><loc>https://nyspotlightreport.com/blog/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>\n'
        '  <url><loc>https://nyspotlightreport.com/proflow/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>\n'
        '  <url><loc>https://nyspotlightreport.com/agency/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>\n'
        '  <url><loc>https://nyspotlightreport.com/free-plan/</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'
        '  <url><loc>https://nyspotlightreport.com/studio/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
        + blog_urls +
        '</urlset>'
    )
    
    r2 = requests.get(f"https://api.github.com/repos/{REPO}/contents/site/sitemap.xml", headers=H)
    sha = r2.json().get("sha") if r2.status_code == 200 else None
    body = {"message": f"feat: sitemap updated {date.today()} ({len(posts)} posts)",
            "content": base64.b64encode(sitemap.encode()).decode()}
    if sha: body["sha"] = sha
    r3 = requests.put(f"https://api.github.com/repos/{REPO}/contents/site/sitemap.xml", json=body, headers=H)
    ok = r3.status_code in [200, 201]
    print(f"{"✅" if ok else "❌"} Sitemap: {len(posts)} blog posts indexed")

if __name__ == "__main__":
    run()
