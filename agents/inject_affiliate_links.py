#!/usr/bin/env python3
"""
TRACK 4 - Affiliate Link Injection Bot
Reads blog articles, detects categories, and injects contextual
affiliate link blocks before the CTA or footer.
"""

import os, re, json, glob
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BLOG_DIR = os.getenv("BLOG_DIR", os.path.join(os.path.dirname(__file__), "..", "NY-Spotlight-Report-good", "blog"))
AFFILIATES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "affiliates", "affiliate_programs.json")
MAX_LINKS_PER_ARTICLE = 2
BLOCK_CLASS = "nysr-affiliate-block"

# ---------------------------------------------------------------------------
# Category detection keywords
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "broadway": ["broadway", "theater", "theatre", "musical", "play", "show", "stage", "curtain", "tony award"],
    "nightlife": ["nightlife", "bar", "club", "lounge", "rooftop", "cocktail", "dj", "dance floor", "nightclub"],
    "fashion": ["fashion", "designer", "runway", "style", "outfit", "boutique", "couture", "vogue"],
    "culture": ["culture", "museum", "gallery", "art", "exhibit", "history", "heritage", "landmark"],
    "tourism": ["tourist", "tourism", "visit", "sightseeing", "attraction", "tour", "explore nyc", "guide to"],
    "food": ["food", "restaurant", "dining", "chef", "cuisine", "brunch", "dinner", "eat", "foodie", "recipe"],
    "lgbtq": ["lgbtq", "pride", "queer", "drag", "stonewall", "gay", "lesbian", "trans", "nonbinary"],
    "music": ["music", "concert", "live music", "jazz", "hip-hop", "rapper", "singer", "festival", "album"],
}

# Category to preferred affiliate program mapping
CATEGORY_AFFILIATES = {
    "broadway":  ["seatgeek", "stubhub"],
    "nightlife": ["hotels_com", "viator"],
    "tourism":   ["viator", "hotels_com"],
    "food":      ["opentable", "amazon_associates"],
    "culture":   ["getyourguide", "viator"],
    "music":     ["seatgeek", "stubhub"],
    "lgbtq":     ["getyourguide", "viator"],
    "fashion":   ["amazon_associates", "viator"],
}


def load_affiliate_programs():
    """Load affiliate programs from JSON config."""
    if not os.path.exists(AFFILIATES_FILE):
        print("[affiliate_injector] Affiliates file not found: {}".format(AFFILIATES_FILE))
        return {}
    with open(AFFILIATES_FILE, "r") as f:
        programs = json.load(f)
    return {p["id"]: p for p in programs}


def detect_categories(html_content):
    """Detect article categories from content keywords."""
    text = re.sub(r"<[^>]+>", " ", html_content).lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(text.count(kw) for kw in keywords)
        if score >= 2:
            scores[cat] = score
    return sorted(scores, key=scores.get, reverse=True)


def select_affiliate_links(categories, programs):
    """Select up to MAX_LINKS_PER_ARTICLE affiliate links based on categories."""
    selected = []
    seen_ids = set()
    for cat in categories:
        if len(selected) >= MAX_LINKS_PER_ARTICLE:
            break
        preferred = CATEGORY_AFFILIATES.get(cat, [])
        for prog_id in preferred:
            if prog_id in seen_ids or prog_id not in programs:
                continue
            if len(selected) >= MAX_LINKS_PER_ARTICLE:
                break
            prog = programs[prog_id]
            templates = prog.get("link_templates", {})
            link_key = cat if cat in templates else list(templates.keys())[0] if templates else None
            if not link_key:
                continue
            link_url = templates[link_key]
            selected.append({
                "program": prog["name"],
                "url": link_url,
                "cta": prog.get("cta_text", "Visit {}".format(prog["name"])),
                "commission": prog.get("commission", ""),
            })
            seen_ids.add(prog_id)
    return selected


def build_affiliate_block(links):
    """Build styled HTML affiliate block."""
    items_html = ""
    for link in links:
        items_html += (
            '\n      <div style="margin-bottom:10px;">'
            '\n        <a href="{}" target="_blank" rel="nofollow sponsored"'
            '\n           style="color:#1a73e8;text-decoration:none;font-weight:600;font-size:15px;">'
            '\n          {} &rarr;'
            '\n        </a>'
            '\n        <span style="color:#666;font-size:13px;margin-left:8px;">{}</span>'
            '\n      </div>'
        ).format(link["url"], link["cta"], link["program"])

    return (
        '\n<!-- NYSR Affiliate Block -->'
        '\n<div class="{}" style="border-left:4px solid #d4a017;background:#fdf9ee;'
        'padding:16px 20px;margin:24px 0;border-radius:4px;font-family:sans-serif;">'
        '\n  <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;'
        'color:#999;margin-bottom:10px;">Sponsored Resources</div>'
        '\n  {}'
        '\n</div>'
        '\n<!-- /NYSR Affiliate Block -->\n'
    ).format(BLOCK_CLASS, items_html)


def inject_into_article(html_content, affiliate_block):
    """Inject affiliate block before nysr-cta or footer element."""
    cta_pattern = re.compile(r'(<div[^>]*class="[^"]*nysr-cta[^"]*")', re.IGNORECASE)
    match = cta_pattern.search(html_content)
    if match:
        pos = match.start()
        return html_content[:pos] + affiliate_block + "\n" + html_content[pos:]
    footer_pattern = re.compile(r"(<footer[\s>])", re.IGNORECASE)
    match = footer_pattern.search(html_content)
    if match:
        pos = match.start()
        return html_content[:pos] + affiliate_block + "\n" + html_content[pos:]
    body_pattern = re.compile(r"(</body>)", re.IGNORECASE)
    match = body_pattern.search(html_content)
    if match:
        pos = match.start()
        return html_content[:pos] + affiliate_block + "\n" + html_content[pos:]
    return html_content + "\n" + affiliate_block


def process_all_articles(dry_run=False):
    """Main: process all blog articles and inject affiliate blocks."""
    programs = load_affiliate_programs()
    if not programs:
        return {"error": "no_affiliate_programs", "processed": 0}
    blog_dir = os.path.abspath(BLOG_DIR)
    if not os.path.isdir(blog_dir):
        print("[affiliate_injector] Blog directory not found: {}".format(blog_dir))
        return {"error": "blog_dir_not_found", "processed": 0}
    html_files = glob.glob(os.path.join(blog_dir, "*.html"))
    stats = {"total": len(html_files), "injected": 0, "skipped_existing": 0, "skipped_no_match": 0}
    for html_path in html_files:
        filename = os.path.basename(html_path)
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if BLOCK_CLASS in content:
            stats["skipped_existing"] += 1
            continue
        categories = detect_categories(content)
        if not categories:
            stats["skipped_no_match"] += 1
            continue
        links = select_affiliate_links(categories, programs)
        if not links:
            stats["skipped_no_match"] += 1
            continue
        block = build_affiliate_block(links)
        new_content = inject_into_article(content, block)
        if dry_run:
            print("[affiliate_injector] DRY RUN | {} | cats={} | links={}".format(
                filename, categories[:3], [l["program"] for l in links]))
        else:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("[affiliate_injector] Injected | {} | {}".format(
                filename, [l["program"] for l in links]))
        stats["injected"] += 1
    print("\n[affiliate_injector] Stats: {}".format(json.dumps(stats, indent=2)))
    return stats


if __name__ == "__main__":
    import sys
    print("=" * 60)
    print("TRACK 4 - Affiliate Link Injection Bot")
    print("=" * 60)
    dry = "--dry-run" in sys.argv
    process_all_articles(dry_run=dry)
