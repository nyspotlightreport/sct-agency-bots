#!/usr/bin/env python3
"""
Article Image Generator -- DALL-E 3 editorial images for all blog articles.

Scans BLOG_DIR for HTML articles, categorises each by slug/content keywords,
generates a category-appropriate DALL-E 3 image, saves to IMG_DIR, and
injects an <img> tag into the article HTML.

Env vars:
    OPENAI_API_KEY  -- required
    BLOG_DIR        -- default ../NY-Spotlight-Report-good/blog
    IMG_DIR         -- default ../NY-Spotlight-Report-good/images/articles
"""
import os, sys, re, json, time, glob, logging, urllib.request, argparse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log = logging.getLogger("article_images")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [IMG-GEN] %(message)s")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
BLOG_DIR = os.environ.get(
    "BLOG_DIR",
    os.path.join(os.path.dirname(__file__), "..", "NY-Spotlight-Report-good", "blog"),
)
IMG_DIR = os.environ.get(
    "IMG_DIR",
    os.path.join(
        os.path.dirname(__file__), "..", "NY-Spotlight-Report-good", "images", "articles"
    ),
)

DALLE_ENDPOINT = "https://api.openai.com/v1/images/generations"
RATE_LIMIT_SLEEP = 3  # seconds between DALL-E calls

# ---------------------------------------------------------------------------
# Category prompt map -- order matters, first match wins
# ---------------------------------------------------------------------------
CATEGORY_PROMPTS = [
    (
        ["broadway", "theater", "theatre", "tony", "musical", "stage"],
        "Professional editorial photograph, Broadway theater marquee lights at night, "
        "NYC Theater District, cinematic photography, no text",
    ),
    (
        ["nightlife", "bar", "club", "cocktail", "lounge"],
        "Professional editorial photograph, sophisticated NYC bar interior, "
        "warm ambient lighting, urban nightlife, no text",
    ),
    (
        ["fashion", "nyfw", "style", "runway", "designer"],
        "Professional editorial photograph, New York Fashion Week street style, "
        "editorial magazine quality, no text",
    ),
    (
        ["lgbtq", "pride", "drag", "queer", "stonewall"],
        "Professional editorial photograph, NYC Pride celebration, "
        "vibrant community atmosphere, rainbow colors, no text",
    ),
    (
        ["culture", "art", "gallery", "museum", "exhibition"],
        "Professional editorial photograph, NYC art gallery, "
        "contemporary art, sophisticated interior, no text",
    ),
    (
        ["awards", "oscar", "grammy", "emmy", "golden-globe"],
        "Professional editorial photograph, awards ceremony atmosphere, "
        "elegant theater, cinematic lighting, no text",
    ),
    (
        ["music", "concert", "jazz", "hip-hop", "rapper"],
        "Professional editorial photograph, NYC live music venue, "
        "concert atmosphere, stage lighting, no text",
    ),
    (
        ["film", "cinema", "sundance", "movie", "premiere"],
        "Professional editorial photograph, NYC film premiere, "
        "cinema marquee, red carpet, no text",
    ),
]

DEFAULT_PROMPT = (
    "Professional editorial photograph, New York City urban scene, "
    "iconic NYC atmosphere, golden hour, no text"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def slug_from_path(path):
    """Return the filename without extension as the slug."""
    return os.path.splitext(os.path.basename(path))[0]


def extract_title(html):
    """Pull the <h1> text or <title> text from article HTML."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "New York Spotlight Report"


def extract_headings(html):
    """Return list of H2 text content."""
    return [
        re.sub(r"<[^>]+>", "", m).strip()
        for m in re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL | re.IGNORECASE)
    ]


def classify_article(slug, title, headings, html):
    """Return the best DALL-E prompt for an article based on keyword matching."""
    searchable = " ".join([slug, title] + headings).lower()
    body_sample = re.sub(r"<[^>]+>", " ", html[:2000]).lower()
    searchable += " " + body_sample

    for keywords, prompt in CATEGORY_PROMPTS:
        if any(kw in searchable for kw in keywords):
            return prompt
    return DEFAULT_PROMPT


def already_has_image(html):
    """Check if the article already references an article image."""
    return "images/articles/" in html


def generate_image(prompt):
    """Call DALL-E 3 API and return the image URL."""
    payload = json.dumps({
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1792x1024",
        "quality": "standard",
        "response_format": "url",
    }).encode()

    req = urllib.request.Request(
        DALLE_ENDPOINT,
        data=payload,
        headers={
            "Authorization": "Bearer %s" % OPENAI_KEY,
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return data["data"][0]["url"]


def download_image(url, dest):
    """Download an image from url to dest path."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ArticleImageBot/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(dest, "wb") as f:
            f.write(resp.read())
    log.info("  Saved %s (%d KB)", dest, os.path.getsize(dest) // 1024)


def inject_image_tag(html, slug, title):
    """Insert an <img> tag into the article HTML.

    Strategy:
      1. If a gradient hero div exists, replace it.
      2. Otherwise insert after the closing </h1> tag.
      3. Fallback: insert after <body>.
    """
    img_tag = (
        '<img src="/images/articles/{slug}.jpg" alt="{title}" '
        'style="width:100%;height:420px;object-fit:cover;display:block" '
        'loading="lazy">'
    ).format(slug=slug, title=title)

    # Strategy 1: replace gradient placeholder div
    gradient_re = (
        r'<div[^>]*style="[^"]*(?:linear-gradient|background:\s*#)[^"]*"'
        r'[^>]*>.*?</div>'
    )
    m = re.search(gradient_re, html, re.DOTALL | re.IGNORECASE)
    if m:
        return html[: m.start()] + img_tag + html[m.end():]

    # Strategy 2: after </h1>
    m = re.search(r"</h1>", html, re.IGNORECASE)
    if m:
        pos = m.end()
        return html[:pos] + "\n" + img_tag + html[pos:]

    # Strategy 3: after <body>
    m = re.search(r"<body[^>]*>", html, re.IGNORECASE)
    if m:
        pos = m.end()
        return html[:pos] + "\n" + img_tag + html[pos:]

    # Last resort: prepend
    return img_tag + "\n" + html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate DALL-E 3 images for blog articles"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without calling API or writing files",
    )
    args = parser.parse_args()

    if not OPENAI_KEY and not args.dry_run:
        log.error("OPENAI_API_KEY not set -- aborting")
        sys.exit(1)

    blog_dir = os.path.abspath(BLOG_DIR)
    img_dir = os.path.abspath(IMG_DIR)

    log.info("Blog dir : %s", blog_dir)
    log.info("Image dir: %s", img_dir)
    log.info("Dry run  : %s", args.dry_run)

    if not os.path.isdir(blog_dir):
        log.error("Blog directory not found: %s", blog_dir)
        sys.exit(1)

    articles = sorted(glob.glob(os.path.join(blog_dir, "*.html")))
    log.info("Found %d article(s)", len(articles))

    generated = 0
    skipped = 0
    errors = 0

    for article_path in articles:
        slug = slug_from_path(article_path)

        with open(article_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        if already_has_image(html):
            log.info("  SKIP (already has image): %s", slug)
            skipped += 1
            continue

        title = extract_title(html)
        headings = extract_headings(html)
        prompt = classify_article(slug, title, headings, html)

        log.info("  PROCESS: %s", slug)
        log.info("    Title   : %s", title)
        log.info("    Category: %s", prompt[:60] + "...")

        if args.dry_run:
            log.info("    DRY-RUN -- would generate image and inject tag")
            generated += 1
            continue

        try:
            image_url = generate_image(prompt)
            dest_path = os.path.join(img_dir, "%s.jpg" % slug)
            download_image(image_url, dest_path)

            updated_html = inject_image_tag(html, slug, title)
            with open(article_path, "w", encoding="utf-8") as f:
                f.write(updated_html)

            log.info("    Injected <img> into %s", article_path)
            generated += 1

        except Exception as exc:
            log.error("    ERROR generating image for %s: %s", slug, exc)
            errors += 1

        # DALL-E rate limit: ~5 images/min for standard
        time.sleep(RATE_LIMIT_SLEEP)

    log.info("=" * 60)
    log.info("Done. Generated: %d | Skipped: %d | Errors: %d", generated, skipped, errors)
    log.info("=" * 60)

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
