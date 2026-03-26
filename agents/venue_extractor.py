#!/usr/bin/env python3
"""
TRACK 2 - Venue Extractor: Articles to Warm Prospects
Scans NY Spotlight Report blog articles for venue/business mentions,
builds prospect records, and generates warm outreach email drafts.
"""

import os, re, json, glob, hashlib
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BLOG_DIR = os.getenv("BLOG_DIR", os.path.join(os.path.dirname(__file__), "..", "NY-Spotlight-Report-good", "blog"))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sales")
PROSPECTS_FILE = os.path.join(DATA_DIR, "venue_prospects.json")
DRAFTS_DIR = os.path.join(DATA_DIR, "warm_outreach_drafts")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "partnerships@myproflow.org")
SITE_URL = os.getenv("SITE_URL", "https://nyspotlightreport.com")

# ---------------------------------------------------------------------------
# Industry detection keywords
# ---------------------------------------------------------------------------
INDUSTRY_KEYWORDS = {
    "nightlife": ["bar", "club", "lounge", "nightclub", "speakeasy", "rooftop", "cocktail", "pub", "dive bar"],
    "restaurant": ["restaurant", "bistro", "eatery", "diner", "cafe", "pizzeria", "trattoria", "brasserie", "steakhouse", "grill"],
    "salon": ["salon", "barbershop", "spa", "beauty", "nail", "hair"],
    "hotel": ["hotel", "inn", "hostel", "resort", "boutique hotel", "suites"],
    "theater": ["theater", "theatre", "playhouse", "comedy club", "improv"],
    "gallery": ["gallery", "museum", "exhibit", "art space", "studio"],
    "fitness": ["gym", "fitness", "yoga", "pilates", "crossfit", "boxing"],
    "retail": ["boutique", "shop", "store", "market", "emporium"],
    "music": ["music venue", "jazz club", "concert hall", "live music"],
    "event_space": ["event space", "venue", "hall", "ballroom", "loft"],
}

# ---------------------------------------------------------------------------
# Regex patterns for venue extraction
# ---------------------------------------------------------------------------
VENUE_PATTERNS = [
    re.compile(
        r"\b(The\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\s+"
        r"(Bar|Club|Lounge|Restaurant|Bistro|Cafe|Salon|Hotel|Gallery|Theater|Theatre|Gym|Spa|Boutique|Shop|Studio|Museum)\b"
    ),
    re.compile(
        r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\s+"
        r"(Bar|Club|Lounge|Restaurant|Bistro|Cafe|Salon|Hotel|Gallery|Theater|Theatre|Gym|Spa|Boutique|Shop|Studio|Museum)\b"
    ),
    re.compile(
        r"\bat\s+((?:The\s+)?[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})\b"
    ),
    re.compile(
        r'["\u201c]((?:The\s+)?[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})["\u201d]'
    ),
]

SKIP_WORDS = {
    "The New", "The City", "The Best", "The Most", "The First", "The Last",
    "The Big", "New York", "The Ultimate", "The Top", "The Next", "The Real",
    "In The", "At The", "For The", "And The", "With The", "From The",
    "The Great", "This Is", "That Is", "There Are", "They Are",
}


def detect_industry(venue_name):
    """Detect industry from venue name keywords."""
    name_lower = venue_name.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return industry
    return "general"


def extract_venues_from_html(html_content, filename):
    """Extract venue/business names from HTML article content."""
    text = re.sub(r"<[^>]+>", " ", html_content)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE)
    if not title_match:
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE)
    article_title = title_match.group(1).strip() if title_match else filename

    venues = {}
    for pattern in VENUE_PATTERNS:
        for match in pattern.finditer(text):
            raw_name = match.group(1).strip() if match.lastindex else match.group(0).strip()
            raw_name = re.sub(r"\s+", " ", raw_name).strip(" .,;:!?")
            if len(raw_name) < 4 or len(raw_name) > 60:
                continue
            if raw_name in SKIP_WORDS or any(raw_name.startswith(sw) for sw in SKIP_WORDS):
                continue
            venue_id = hashlib.md5(raw_name.lower().encode()).hexdigest()[:12]
            if venue_id not in venues:
                venues[venue_id] = {
                    "id": venue_id,
                    "business_name": raw_name,
                    "industry": detect_industry(raw_name),
                    "source_article": article_title,
                    "source_file": filename,
                    "source_url": "{}/blog/{}".format(SITE_URL, filename),
                    "warm_signal": "Featured in NY Spotlight Report article: {}".format(article_title),
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "outreach_status": "pending",
                }
    return list(venues.values())


def generate_warm_email(prospect):
    """Generate a warm outreach email draft for a prospect."""
    biz = prospect["business_name"]
    industry = prospect["industry"]
    article = prospect["source_article"]
    url = prospect["source_url"]
    subject = "Your venue was featured in NY Spotlight Report - partnership opportunity"
    body = (
        "Hi {} Team,\n\n"
        "I am reaching out because your venue was recently featured in our "
        'article "{}" on NY Spotlight Report ({}).\n\n'
        "Our readers loved the mention, and we would like to explore how we "
        "can help drive even more customers your way.\n\n"
        "NY Spotlight Report reaches thousands of NYC locals and visitors each "
        "month who are actively looking for the best {} experiences in the city. "
        "We offer:\n\n"
        "- Dedicated feature articles with professional photography\n"
        "- Social media promotion across our Instagram, TikTok, and YouTube channels\n"
        "- Inclusion in our curated NYC guides and newsletters\n\n"
        "Would you be open to a quick 10-minute call this week to discuss how "
        "we can work together?\n\n"
        "Best regards,\n"
        "S.C. Thomas\n"
        "Founder & Editor-in-Chief\n"
        "NY Spotlight Report\n"
        "partnerships@myproflow.org\n"
    ).format(biz, article, url, industry)
    return {
        "to": "info@{}.com".format(biz.lower().replace(" ", "")),
        "from": FROM_EMAIL,
        "subject": subject,
        "body": body,
        "prospect_id": prospect["id"],
        "business_name": biz,
        "industry": industry,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sent": False,
    }


def process_articles():
    """Main function: scan blog articles and extract venue prospects."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    blog_dir = os.path.abspath(BLOG_DIR)
    if not os.path.isdir(blog_dir):
        print("[venue_extractor] Blog directory not found: {}".format(blog_dir))
        print("[venue_extractor] Creating sample structure for CI...")
        os.makedirs(blog_dir, exist_ok=True)
        return {"prospects": [], "drafts": [], "error": "blog_dir_not_found"}
    html_files = glob.glob(os.path.join(blog_dir, "*.html"))
    if not html_files:
        print("[venue_extractor] No HTML files found in {}".format(blog_dir))
        return {"prospects": [], "drafts": []}

    existing = {}
    if os.path.exists(PROSPECTS_FILE):
        with open(PROSPECTS_FILE, "r") as f:
            for p in json.load(f):
                existing[p["id"]] = p

    all_prospects = []
    all_drafts = []
    for html_path in html_files:
        filename = os.path.basename(html_path)
        print("[venue_extractor] Processing: {}".format(filename))
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        venues = extract_venues_from_html(content, filename)
        for venue in venues:
            if venue["id"] not in existing:
                all_prospects.append(venue)
                existing[venue["id"]] = venue
                draft = generate_warm_email(venue)
                all_drafts.append(draft)
                safe_name = venue["business_name"][:30].replace(" ", "_").replace("/", "_")
                draft_file = os.path.join(DRAFTS_DIR, "{}_{}.json".format(venue["id"], safe_name))
                with open(draft_file, "w") as df:
                    json.dump(draft, df, indent=2)

    with open(PROSPECTS_FILE, "w") as f:
        json.dump(list(existing.values()), f, indent=2)

    summary = {
        "total_articles_scanned": len(html_files),
        "new_prospects_found": len(all_prospects),
        "total_prospects": len(existing),
        "drafts_generated": len(all_drafts),
        "run_at": datetime.now(timezone.utc).isoformat(),
    }
    print("[venue_extractor] Summary: {}".format(json.dumps(summary, indent=2)))
    return summary


def send_warm_outreach(dry_run=True):
    """Send warm outreach emails for pending prospects via Resend API."""
    if not os.path.isdir(DRAFTS_DIR):
        return {"sent": 0, "error": "no_drafts_dir"}
    draft_files = glob.glob(os.path.join(DRAFTS_DIR, "*.json"))
    sent_count = 0
    errors = []
    for draft_path in draft_files:
        with open(draft_path, "r") as f:
            draft = json.load(f)
        if draft.get("sent"):
            continue
        if dry_run:
            print("[venue_extractor] DRY RUN - would send to: {} | Subject: {}".format(
                draft["to"], draft["subject"]))
            continue
        if not RESEND_API_KEY:
            errors.append({"draft": draft_path, "error": "RESEND_API_KEY not set"})
            continue
        try:
            import requests
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": "Bearer {}".format(RESEND_API_KEY)},
                json={
                    "from": draft["from"],
                    "to": [draft["to"]],
                    "subject": draft["subject"],
                    "text": draft["body"],
                },
                timeout=15,
            )
            if resp.status_code in (200, 201):
                draft["sent"] = True
                draft["sent_at"] = datetime.now(timezone.utc).isoformat()
                with open(draft_path, "w") as f:
                    json.dump(draft, f, indent=2)
                sent_count += 1
                print("[venue_extractor] Sent outreach to: {}".format(draft["to"]))
            else:
                errors.append({"draft": draft_path, "error": resp.text})
        except Exception as e:
            errors.append({"draft": draft_path, "error": str(e)})
    return {"sent": sent_count, "errors": errors, "dry_run": dry_run}


if __name__ == "__main__":
    print("=" * 60)
    print("TRACK 2 - Venue Extractor")
    print("=" * 60)
    result = process_articles()
    print("\nProspects file: {}".format(PROSPECTS_FILE))
    print("Drafts directory: {}".format(DRAFTS_DIR))
    outreach = send_warm_outreach(dry_run=True)
    print("\nOutreach result: {}".format(json.dumps(outreach, indent=2)))
