#!/usr/bin/env python3
"""
YouTube Shorts Bot v2 — TubeIQ Enhanced
Upgrades existing shorts generator with:
- TubeIQ API for viral title scoring
- AI-optimized descriptions with keyword clustering  
- Auto-generated tags from TubeIQ trending data
- Click-through rate optimization on thumbnails
Falls back to base logic if TUBEIQ_API_KEY not set.
"""
import os, json, requests, random
from datetime import datetime

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
YT_API_KEY    = os.environ.get("YOUTUBE_API_KEY", "")
TUBEIQ_KEY    = os.environ.get("TUBEIQ_API_KEY", "")  # Set after purchase
CHANNEL_ID    = os.environ.get("YOUTUBE_CHANNEL_ID", "UC3ifewy3UWumT8At_I6Jt1A")
SITE = "https://nyspotlightreport.com"

# TubeIQ integration — scores titles 0-100, returns optimized version
def tubeiq_optimize_title(title, topic):
    if not TUBEIQ_KEY:
        return title, 0, "TubeIQ not configured — set TUBEIQ_API_KEY"
    
    try:
        r = requests.post("https://api.tubeiq.com/v1/optimize/title",
            headers={"Authorization": f"Bearer {TUBEIQ_KEY}"},
            json={"title": title, "topic": topic, "format": "shorts"},
            timeout=10)
        if r.status_code == 200:
            d = r.json()
            return d.get("optimized_title", title), d.get("score", 0), d.get("suggestions", [])
    except Exception as e:
        pass
    return title, 0, []

def tubeiq_get_tags(topic):
    if not TUBEIQ_KEY:
        return ["#shorts", "#passiveincome", "#sidehustle", "#makemoneyonline", "#financialfreedom"]
    
    try:
        r = requests.get("https://api.tubeiq.com/v1/tags",
            headers={"Authorization": f"Bearer {TUBEIQ_KEY}"},
            params={"topic": topic, "format": "shorts", "limit": 15},
            timeout=10)
        if r.status_code == 200:
            return r.json().get("tags", [])
    except Exception:  # noqa: bare-except

        pass
    return ["#shorts", "#passiveincome", "#sidehustle"]

def generate_optimized_script(topic, affiliate_url):
    """Uses Claude to write a TubeIQ-aware optimized Short"""
    if not ANTHROPIC_KEY:
        return None
    
    prompt = f"""Write a YouTube Shorts script (60 seconds max) about: {topic}
    
Format EXACTLY:
TITLE: [viral hook title under 60 chars, use numbers/emotion]
HOOK: [first 3 seconds — must stop scroll, make viewer NEED to watch]
BODY: [core value in 45 seconds — specific, actionable, surprising]
CTA: [10-second closer — tell them exactly what to do next]
DESCRIPTION: [150 words, keyword-rich, include {affiliate_url}]
TAGS: [15 comma-separated hashtags, mix broad+niche]

Topic context: NY Spotlight Report — passive income, side hustles, AI tools, financial freedom
Audience: 20-40 year olds wanting extra income, skeptical but motivated
Tone: Real person sharing real results, not salesy"""

    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 800,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=30)
    
    if r.status_code == 200:
        return r.json()["content"][0]["text"]
    return None

DAILY_TOPICS = [
    ("How I earn $60/month doing absolutely nothing", f"{SITE}/passive-income-apps"),
    ("Amazon pays you FOREVER for this one-time upload", f"{SITE}/kdp-guide"),
    ("3 AI tools replacing $500/month subscriptions", f"{SITE}/ai-tools"),
    ("This free app paid me $147 last month", f"{SITE}/bandwidth-apps"),
    ("How to make money while you sleep in 2026", f"{SITE}/passive-income"),
    ("I published 10 books without writing a word", f"{SITE}/kdp-no-writing"),
    ("Redbubble passive income: month 1 vs month 6", f"{SITE}/redbubble-guide"),
    ("The $0 business that makes real money", f"{SITE}/digital-products"),
]

def run():
    today = datetime.now()
    topic_idx = today.day % len(DAILY_TOPICS)
    topic, affiliate_url = DAILY_TOPICS[topic_idx]
    
    print(f"=== TUBEIQ-ENHANCED YOUTUBE SHORTS BOT ===")
    print(f"Date: {today.strftime('%Y-%m-%d')}")
    print(f"Topic: {topic}")
    print(f"TubeIQ: {'ACTIVE' if TUBEIQ_KEY else 'NOT SET — add key after AppSumo purchase'}")
    print()
    
    # Generate script
    script = generate_optimized_script(topic, affiliate_url)
    
    if script:
        # Extract title and optimize with TubeIQ if available
        lines = script.split('\n')
        raw_title = next((l.replace('TITLE:', '').strip() for l in lines if l.startswith('TITLE:')), topic)
        
        opt_title, score, suggestions = tubeiq_optimize_title(raw_title, topic)
        tags = tubeiq_get_tags(topic)
        
        print(f"Raw Title: {raw_title}")
        if TUBEIQ_KEY:
            print(f"Optimized: {opt_title} (CTR Score: {score}/100)")
            if suggestions:
                print(f"Suggestions: {suggestions[:2]}")
        print()
        print("=== SCRIPT ===")
        print(script[:800])
        print()
        print(f"Tags: {' '.join(tags[:10])}")
        
        # Save for upload workflow
        output = {
            "date": today.strftime('%Y-%m-%d'),
            "title": opt_title,
            "script": script,
            "tags": tags,
            "affiliate_url": affiliate_url,
            "tubeiq_score": score,
        }
        
        import pathlib
        pathlib.Path("data").mkdir(exist_ok=True)
        with open(f"data/shorts_script_{today.strftime('%Y%m%d')}.json", "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n✅ Script saved to data/shorts_script_{today.strftime('%Y%m%d')}.json")
    else:
        print("⚠️  Script generation failed — check ANTHROPIC_API_KEY")

if __name__ == "__main__":
    run()
