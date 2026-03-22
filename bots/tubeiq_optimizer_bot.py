#!/usr/bin/env python3
"""
TubeIQ YouTube Optimizer Bot — NYSR Agency
Once TubeIQ is purchased, this bot:
1. Takes every Shorts script from the generator bot
2. Calls TubeIQ API for SEO-optimized title, description, tags
3. Injects them back into the YouTube upload payload
4. Result: every Short gets max-SEO metadata = more views = faster monetization
"""
import os, json, ssl, urllib.request, urllib.parse, time

TUBEIQ_KEY  = os.environ.get("TUBEIQ_API_KEY", "")
CHANNEL_ID  = os.environ.get("YOUTUBE_CHANNEL_ID", "UC3ifewy3UWumT8At_I6Jt1A")
BASE        = "https://api.tubeiq.co/v1"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def optimize_video_metadata(topic: str, script_excerpt: str) -> dict:
    """Call TubeIQ to generate SEO title, description, tags"""
    if not TUBEIQ_KEY:
        # Fallback: AI-generated without TubeIQ
        return {
            "title": f"{topic} #Shorts",
            "description": f"{script_excerpt[:100]}\n\n#shorts #NYSRReport #passiveincome",
            "tags": ["shorts", "passive income", "money", "entrepreneur", topic.lower()]
        }
    payload = json.dumps({
        "topic": topic,
        "script": script_excerpt,
        "content_type": "shorts",
        "channel_id": CHANNEL_ID
    }).encode()
    req = urllib.request.Request(f"{BASE}/optimize",
        data=payload, method="POST",
        headers={"Authorization": f"Bearer {TUBEIQ_KEY}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read())
            return {
                "title": data.get("title", f"{topic} #Shorts"),
                "description": data.get("description", ""),
                "tags": data.get("tags", [])
            }
    except Exception as e:
        print(f"TubeIQ API error: {e} — using fallback")
        return optimize_video_metadata(topic, script_excerpt)

def process_pending_shorts():
    """Read scripts from data dir, optimize all metadata"""
    scripts_dir = "data/shorts_scripts"
    optimized   = []
    
    if not os.path.exists(scripts_dir):
        print(f"No scripts dir at {scripts_dir}")
        return []

    for fname in os.listdir(scripts_dir):
        if not fname.endswith(".json"):
            continue
        with open(f"{scripts_dir}/{fname}") as f:
            script = json.load(f)

        topic   = script.get("topic", fname.replace(".json",""))
        excerpt = script.get("script", "")[:300]
        meta    = optimize_video_metadata(topic, excerpt)

        script["seo_title"]       = meta["title"]
        script["seo_description"] = meta["description"]
        script["seo_tags"]        = meta["tags"]

        out_path = f"data/shorts_optimized/{fname}"
        os.makedirs("data/shorts_optimized", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(script, f, indent=2)

        optimized.append({"file": fname, "title": meta["title"]})
        print(f"✅ {topic} → '{meta['title']}'")
        time.sleep(0.3)

    return optimized

if __name__ == "__main__":
    print("=== TubeIQ YouTube Optimizer ===")
    results = process_pending_shorts()
    print(f"\n✅ Optimized {len(results)} scripts for maximum YouTube SEO")
