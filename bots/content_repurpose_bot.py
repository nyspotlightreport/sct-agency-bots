#!/usr/bin/env python3
"""
CONTENT REPURPOSE BOT — S.C. Thomas Internal Agency
Input: 1 article/post/idea
Output: Twitter thread, LinkedIn post, email, short tweet, Instagram caption
Uses Claude API to generate all variants. Saves to output folder.
Usage: python content_repurpose_bot.py --input "your content here"
       python content_repurpose_bot.py --file article.txt
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./repurposed_content"))
OUTPUT_DIR.mkdir(exist_ok=True)

BRAND_VOICE = """
You are writing as S.C. Thomas — Editor in Chief, authority figure, operator.
Voice rules:
- Short sentences. Strong verbs. Outcome-first.
- Authoritative but not arrogant
- No corporate buzzwords, no AI tells ("certainly", "dive deep", etc.)
- No hashtag spam
- Specific > vague always
- Never start with "I" on social posts
"""

PLATFORM_PROMPTS = {
    "twitter_thread": """
Convert this content into a Twitter/X thread (8-12 tweets).
- Tweet 1: Hook — bold claim or surprising fact
- Tweets 2-10: One insight per tweet, builds on previous
- Final tweet: CTA or memorable close
- Each tweet under 280 chars
- No hashtags
- Number each tweet (1/, 2/, etc.)
""",
    "twitter_single": """
Write ONE high-impact Twitter/X post about the core idea.
- Under 240 chars
- Hook first word or phrase
- No hashtags
- Sharp, memorable, shareable
""",
    "linkedin_post": """
Write a LinkedIn post (150-250 words).
- First line must stop the scroll — bold claim or story opener
- NO "I'm excited to announce"
- Story or insight → lesson → takeaway
- End with a question or subtle CTA
- Professional but human
- Line breaks between paragraphs
""",
    "email_newsletter": """
Write an email newsletter section (200-300 words).
- Subject line: 5 options (punchy, benefit-driven)
- Preview text: 1 option (under 90 chars)
- Body: conversational, one clear insight, one CTA
- Sign off: casual
""",
    "instagram_caption": """
Write an Instagram caption (100-150 words).
- Hook first line (shows before the fold)
- Story or insight in 3-4 short paragraphs
- CTA at end ("Link in bio" or question)
- 5-8 relevant hashtags at very end (separated by line break)
"""
}

# ─── CLAUDE API CALLER ────────────────────────────────────────────────────────

def call_claude(system_prompt, user_content):
    if not ANTHROPIC_API_KEY:
        return f"[NO API KEY] Would generate: {user_content[:100]}..."
    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_content}]
    }
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["content"][0]["text"]

# ─── REPURPOSE ENGINE ─────────────────────────────────────────────────────────

def repurpose(content, title="content"):
    print(f"\n[repurpose-bot] Processing: {title[:50]}")
    results = {}

    for platform, platform_prompt in PLATFORM_PROMPTS.items():
        print(f"  → Generating {platform}...")
        system = BRAND_VOICE + "\n\n" + platform_prompt
        prompt = f"SOURCE CONTENT:\n\n{content}\n\nGenerate the {platform.replace('_', ' ')} now."
        try:
            output = call_claude(system, prompt)
            results[platform] = output
            print(f"  ✅ {platform} done ({len(output)} chars)")
        except Exception as e:
            results[platform] = f"ERROR: {e}"
            print(f"  ❌ {platform} failed: {e}")

    return results

def save_results(results, title="content"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title[:30] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    filename = OUTPUT_DIR / f"{timestamp}_{safe_title}.md"

    with open(filename, "w") as f:
        f.write(f"# Repurposed Content: {title}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n")
        
        labels = {
            "twitter_thread": "🐦 TWITTER/X THREAD",
            "twitter_single": "🐦 TWITTER/X SINGLE POST",
            "linkedin_post": "💼 LINKEDIN POST",
            "email_newsletter": "📧 EMAIL NEWSLETTER",
            "instagram_caption": "📸 INSTAGRAM CAPTION"
        }
        
        for platform, output in results.items():
            f.write(f"## {labels.get(platform, platform.upper())}\n\n")
            f.write(output)
            f.write("\n\n---\n\n")

    print(f"\n[repurpose-bot] Saved to: {filename}")
    return filename

def print_results(results):
    labels = {
        "twitter_thread": "🐦 TWITTER/X THREAD",
        "twitter_single": "🐦 TWITTER/X SINGLE POST",
        "linkedin_post": "💼 LINKEDIN POST",
        "email_newsletter": "📧 EMAIL NEWSLETTER",
        "instagram_caption": "📸 INSTAGRAM CAPTION"
    }
    for platform, output in results.items():
        print(f"\n{'='*60}")
        print(f"{labels.get(platform, platform.upper())}")
        print('='*60)
        print(output)

# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Repurpose Bot")
    parser.add_argument("--input", type=str, help="Content to repurpose (text)")
    parser.add_argument("--file",  type=str, help="Path to .txt or .md file")
    parser.add_argument("--title", type=str, default="content", help="Title for output file")
    parser.add_argument("--platforms", nargs="+", 
                        choices=list(PLATFORM_PROMPTS.keys()),
                        help="Specific platforms only (default: all)")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            content = f.read()
        title = args.title or Path(args.file).stem
    elif args.input:
        content = args.input
        title = args.title
    else:
        # Demo mode
        content = "Short-form content beats long-form for discovery. Most people won't read 2,000 words from someone they don't know. But they'll read 5 sentences. Then 10. Then the whole thread. Attention is earned in increments."
        title = "content_strategy_demo"
        print("[repurpose-bot] No input provided — running demo")

    if args.platforms:
        filtered = {k: v for k, v in PLATFORM_PROMPTS.items() if k in args.platforms}
        PLATFORM_PROMPTS.clear()
        PLATFORM_PROMPTS.update(filtered)

    results = repurpose(content, title)
    print_results(results)
    save_results(results, title)

# ─── USAGE EXAMPLES ───────────────────────────────────────────────────────────
# python content_repurpose_bot.py --input "Your article text here" --title "my_post"
# python content_repurpose_bot.py --file my_article.txt
# python content_repurpose_bot.py --file my_article.txt --platforms twitter_thread linkedin_post
#
# SETUP:
# pip install requests
# export ANTHROPIC_API_KEY=your_key_here
