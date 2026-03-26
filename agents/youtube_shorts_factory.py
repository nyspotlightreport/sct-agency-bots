#!/usr/bin/env python3
"""
YouTube Shorts Factory
Reads articles from NY-Spotlight-Report-good/blog/ subdirectories and produces:
  - 60-second video scripts (hook in first 3 words, 3 key facts, CTA)
  - Optional ElevenLabs voiceover audio (when ELEVENLABS_API_KEY is set)
  - Optional DALL-E 3 thumbnails (when OPENAI_API_KEY is set)
  - Script text files  -> data/youtube/scripts/{slug}.txt
  - Metadata JSON      -> data/youtube/metadata/{slug}.json

Batch size controlled by YOUTUBE_BATCH_SIZE env var (default 5).
"""
import os
import re
import json
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BLOG_DIR = os.path.join(os.path.expanduser("~"), "NY-Spotlight-Report-good", "blog")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, "..", "data", "youtube")
SCRIPT_DIR = os.path.join(DATA_ROOT, "scripts")
META_DIR = os.path.join(DATA_ROOT, "metadata")
AUDIO_DIR = os.path.join(DATA_ROOT, "audio")
THUMB_DIR = os.path.join(DATA_ROOT, "thumbnails")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
YOUTUBE_BATCH_SIZE = int(os.environ.get("YOUTUBE_BATCH_SIZE", "5"))


# ---------------------------------------------------------------------------
# Article parsing
# ---------------------------------------------------------------------------
def parse_article(html_path: str, slug: str) -> dict:
    """Extract title, excerpt, and category from an article's index.html."""
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    # Title: <title>...</title>, strip site suffix after em-dash
    m = re.search(r"<title>([^<]+)</title>", html)
    title = m.group(1).split("\u2014")[0].strip() if m else slug.replace("-", " ").title()

    # Excerpt: og:description or meta description
    m = (
        re.search(r'og:description[^>]*content="([^"]+)"', html)
        or re.search(r'name="description"[^>]*content="([^"]+)"', html)
    )
    excerpt = m.group(1).strip() if m else title

    # Category from markup (span with class="article-category")
    m = re.search(r'class="article-category"[^>]*>([^<]+)<', html)
    category = m.group(1).strip() if m and m.group(1).strip() else "Entertainment"

    # Pull first 3 paragraphs from article body for fact extraction
    body_m = re.search(r'class="article-body"[^>]*>(.*?)</article>', html, re.DOTALL)
    body_text = ""
    if body_m:
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", body_m.group(1), re.DOTALL)
        body_text = " ".join(
            re.sub(r"<[^>]+>", "", p).strip() for p in paragraphs[:5]
        )

    return {
        "slug": slug,
        "title": title,
        "excerpt": excerpt,
        "category": category,
        "body_preview": body_text[:600],
    }


def discover_articles() -> list:
    """Scan the blog directory and return a list of article dicts."""
    if not os.path.isdir(BLOG_DIR):
        print(f"ERROR: Blog directory not found at {BLOG_DIR}")
        return []

    articles = []
    for item in sorted(os.listdir(BLOG_DIR)):
        item_path = os.path.join(BLOG_DIR, item)
        if not os.path.isdir(item_path):
            continue
        html_path = os.path.join(item_path, "index.html")
        if not os.path.isfile(html_path):
            continue
        articles.append(parse_article(html_path, item))

    return articles


# ---------------------------------------------------------------------------
# Script generation (template-based, no API key required)
# ---------------------------------------------------------------------------
def _extract_facts(body_preview: str, excerpt: str) -> list:
    """Pull up to 3 sentence-like facts from the body text or excerpt."""
    source = body_preview if body_preview else excerpt
    sentences = re.split(r"(?<=[.!?])\s+", source)
    facts = []
    for s in sentences:
        s = s.strip()
        if len(s) > 30 and len(s) < 200:
            facts.append(s)
        if len(facts) == 3:
            break
    # Pad with excerpt if needed
    while len(facts) < 3 and excerpt:
        facts.append(excerpt[:150])
        break
    return facts


def generate_script(article: dict) -> str:
    """
    Generate a 60-second YouTube Shorts script.
    Structure: hook (first 3 words grab attention) -> 3 key facts -> CTA.
    """
    title = article["title"]
    excerpt = article["excerpt"]
    body = article.get("body_preview", "")
    facts = _extract_facts(body, excerpt)

    hook_word = title.split()[0].upper() if title.split() else "BREAKING"

    lines = [
        f"{hook_word} NEWS ALERT!",
        "",
        f"{title}.",
        "",
        "Here are three things you need to know.",
        "",
    ]

    for i, fact in enumerate(facts, 1):
        lines.append(f"Number {i}: {fact}")
        lines.append("")

    lines.extend([
        "That's the story from the streets of New York.",
        "",
        "If you want daily coverage of NYC culture, entertainment, and the stories that matter,",
        "follow NY Spotlight Report right now.",
        "",
        "Hit that follow button and turn on notifications so you never miss a story.",
        "Link in bio for the full article.",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ElevenLabs audio generation
# ---------------------------------------------------------------------------
def generate_audio(script_text: str, slug: str) -> str | None:
    """Generate voiceover via ElevenLabs TTS. Returns file path or None."""
    if not ELEVENLABS_API_KEY:
        return None

    import requests

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script_text[:2500],
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            os.makedirs(AUDIO_DIR, exist_ok=True)
            path = os.path.join(AUDIO_DIR, f"{slug}.mp3")
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"    [audio] Saved {path}")
            return path
        else:
            print(f"    [audio] ElevenLabs API error {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"    [audio] ElevenLabs request failed: {e}")

    return None


# ---------------------------------------------------------------------------
# DALL-E 3 thumbnail generation
# ---------------------------------------------------------------------------
def generate_thumbnail(article: dict) -> str | None:
    """Generate a YouTube Shorts thumbnail via DALL-E 3. Returns file path or None."""
    if not OPENAI_API_KEY:
        return None

    import requests

    prompt = (
        f"A bold, eye-catching YouTube Shorts thumbnail about: {article['title']}. "
        "Style: vibrant colors, cinematic New York City vibe, bold text overlay area, "
        "9:16 vertical aspect ratio, dramatic lighting. No text in the image."
    )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt[:1000],
        "n": 1,
        "size": "1024x1792",
        "quality": "standard",
    }

    try:
        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=90,
        )
        if r.status_code == 200:
            image_url = r.json()["data"][0]["url"]
            # Download the image
            img_resp = requests.get(image_url, timeout=60)
            if img_resp.status_code == 200:
                os.makedirs(THUMB_DIR, exist_ok=True)
                path = os.path.join(THUMB_DIR, f"{article['slug']}.png")
                with open(path, "wb") as f:
                    f.write(img_resp.content)
                print(f"    [thumb] Saved {path}")
                return path
        else:
            print(f"    [thumb] DALL-E API error {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"    [thumb] DALL-E request failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("YouTube Shorts Factory - NY Spotlight Report")
    print("=" * 60)

    # Ensure output directories exist
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)

    articles = discover_articles()
    if not articles:
        print("No articles found. Exiting.")
        return

    batch = min(YOUTUBE_BATCH_SIZE, len(articles))
    print(f"Found {len(articles)} articles, processing first {batch}")
    print(f"  ElevenLabs API key: {'SET' if ELEVENLABS_API_KEY else 'NOT SET'}")
    print(f"  OpenAI API key:     {'SET' if OPENAI_API_KEY else 'NOT SET'}")
    print()

    for i, article in enumerate(articles[:batch], 1):
        print(f"[{i}/{batch}] {article['title'][:60]}")

        # 1. Generate script
        script_text = generate_script(article)
        script_path = os.path.join(SCRIPT_DIR, f"{article['slug']}.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_text)
        print(f"    [script] {len(script_text)} chars -> {script_path}")

        # 2. Generate audio (if ElevenLabs key available)
        audio_path = generate_audio(script_text, article["slug"])

        # 3. Generate thumbnail (if OpenAI key available)
        thumb_path = generate_thumbnail(article)

        # 4. Save metadata JSON
        metadata = {
            "title": f"{article['title'][:95]} | NY Spotlight Report",
            "description": (
                f"{article['excerpt'][:200]}\n\n"
                f"Full story: https://nyspotlightreport.com/blog/{article['slug']}/\n\n"
                "#NYC #NewYork #Entertainment #NYSpotlightReport"
            ),
            "tags": ["NYC", "New York", "Entertainment", "NYSpotlightReport", article["category"]],
            "category": article["category"],
            "script_file": script_path,
            "audio_file": audio_path,
            "thumbnail_file": thumb_path,
            "source_url": f"https://nyspotlightreport.com/blog/{article['slug']}/",
            "generated_at": datetime.now().isoformat(),
        }
        meta_path = os.path.join(META_DIR, f"{article['slug']}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"    [meta]   {meta_path}")
        print()

        # Brief pause between articles to be respectful to APIs
        if i < batch:
            time.sleep(0.5)

    print("=" * 60)
    print(f"Done. {batch} YouTube Shorts packages created.")
    print(f"  Scripts:    {SCRIPT_DIR}")
    print(f"  Metadata:   {META_DIR}")
    if ELEVENLABS_API_KEY:
        print(f"  Audio:      {AUDIO_DIR}")
    if OPENAI_API_KEY:
        print(f"  Thumbnails: {THUMB_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
