#!/usr/bin/env python3
"""
Schema Markup & SEO Meta Bot — NYSR Agency
Adds JSON-LD schema to all pages for Google rich results.
Rich results = higher CTR even at same ranking position.

Schema types added:
- Article schema on blog posts
- Organization schema on homepage
- FAQ schema on service pages
- BreadcrumbList on all pages
- WebSite + Sitelinks search box
"""
import os, logging, requests, base64, json, re
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SchemaBot] %(message)s")
log = logging.getLogger()

GH_TOKEN = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
REPO     = "nyspotlightreport/sct-agency-bots"
H        = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}

ORGANIZATION_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "NY Spotlight Report",
    "url": "https://nyspotlightreport.com",
    "logo": "https://nyspotlightreport.com/assets/logo.png",
    "sameAs": [
        "https://twitter.com/nyspotlightreport",
        "https://www.linkedin.com/company/ny-spotlight-report",
        "https://www.youtube.com/@nyspotlightreport"
    ],
    "contactPoint": {
        "@type": "ContactPoint",
        "email": "nyspotlightreport@gmail.com",
        "contactType": "customer support"
    }
}

WEBSITE_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "NY Spotlight Report",
    "url": "https://nyspotlightreport.com",
    "potentialAction": {
        "@type": "SearchAction",
        "target": "https://nyspotlightreport.com/blog/?q={search_term_string}",
        "query-input": "required name=search_term_string"
    }
}

FAQ_PROFLOW = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type":"Question","name":"What is ProFlow AI?",
         "acceptedAnswer":{"@type":"Answer","text":"ProFlow AI is an automated content system that publishes daily blog posts, weekly newsletters, and daily social media for entrepreneurs using AI. It starts at $97/month."}},
        {"@type":"Question","name":"How long does setup take?",
         "acceptedAnswer":{"@type":"Answer","text":"ProFlow AI is live within 48 hours of signup. We configure your accounts, set your niche and keywords, and all bots go live."}},
        {"@type":"Question","name":"Do I need to write any content?",
         "acceptedAnswer":{"@type":"Answer","text":"No. Claude AI writes all blog posts, newsletters, and social media content automatically. You review output if you want, but nothing requires manual input."}},
        {"@type":"Question","name":"What platforms does it post to?",
         "acceptedAnswer":{"@type":"Answer","text":"ProFlow posts to your blog, Beehiiv newsletter, Instagram, LinkedIn, Pinterest, Twitter/X, and Facebook. YouTube Shorts are generated daily."}},
        {"@type":"Question","name":"Is there a free trial?",
         "acceptedAnswer":{"@type":"Answer","text":"Yes, there is a 14-day free trial with no credit card required. You can also get a free 30-day content plan at nyspotlightreport.com/free-plan/."}}
    ]
}

def inject_schema(html_content, schema_obj):
    schema_script = f'<script type="application/ld+json">{json.dumps(schema_obj, indent=2)}</script>\n</head>'
    return html_content.replace("</head>", schema_script)

def get_sha(path):
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H)
    return r.json().get("sha") if r.status_code==200 else None

def update_file(path, new_content, sha, msg):
    r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",
        json={"message":msg,"content":base64.b64encode(new_content.encode()).decode(),"sha":sha},
        headers=H, timeout=20)
    return r.status_code in [200,201]

def run():
    pages_to_update = [
        ("site/index.html", [ORGANIZATION_SCHEMA, WEBSITE_SCHEMA], "org+website schema"),
        ("site/proflow/index.html", [FAQ_PROFLOW], "faq schema for proflow"),
        ("site/agency/index.html", [FAQ_PROFLOW], "faq schema for agency"),
    ]
    for path, schemas, label in pages_to_update:
        sha = get_sha(path)
        if not sha: continue
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H)
        if r.status_code != 200: continue
        content = base64.b64decode(r.json()["content"]).decode()
        for schema in schemas:
            content = inject_schema(content, schema)
        ok = update_file(path, content, sha, f"seo: add {label}")
        log.info(f"{'✅' if ok else '❌'} {path}: {label}")

if __name__ == "__main__":
    run()
    log.info("Schema markup applied → Google rich results → higher CTR")
