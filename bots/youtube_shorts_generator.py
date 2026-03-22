#!/usr/bin/env python3
"""
YouTube Shorts Auto-Generator
Creates Shorts scripts from affiliate content daily
Uploads to YouTube via Data API
Revenue: Ad revenue + affiliate links in description
"""
import os, requests, json, datetime, random, subprocess, tempfile
from pathlib import Path

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
YT_API_KEY    = os.environ.get("YOUTUBE_API_KEY","")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY","")
SITE = "https://nyspotlightreport.com"

SHORTS_SCRIPTS = [
    {
        "title": "I made $60/month doing absolutely nothing #passiveincome",
        "hook": "I installed 2 apps and now make $60 a month doing nothing.",
        "body": "EarnApp and Honeygain pay you to share your unused internet bandwidth. You literally just install them and forget about them. I got my first payment in week 3. No referrals needed, no tasks, no surveys. Just existing internet you already have.",
        "cta": "Link in bio for the full guide. Free to install.",
        "tags": "#passiveincome #sidehustle #makemoney #earnapp #honeygain",
        "affiliate_link": f"{SITE}/best-passive-income-apps-2026"
    },
    {
        "title": "Amazon will pay you royalties FOREVER for this #kdp",
        "hook": "Amazon KDP lets you publish books with zero upfront cost and earn royalties forever.",
        "body": "Low content books — journals, planners, puzzle books — cost nothing to make with AI tools. Upload to KDP, set your price, and Amazon handles printing, shipping, and customer service. One book can earn $20 to $200 a month. I have 10 books running on autopilot right now.",
        "cta": "Full guide linked in bio.",
        "tags": "#amazonkdp #passiveincome #selfpublishing #sidehustle",
        "affiliate_link": f"{SITE}/amazon-kdp-guide-2026"
    },
    {
        "title": "The newsletter platform that PAYS YOU from day 1 #beehiiv",
        "hook": "Most newsletter platforms cost money. This one pays you.",
        "body": "Beehiiv has a built-in ad network that monetizes your subscribers automatically. Even with 100 subscribers, their ad placements put money in your account. Free to start, no minimum subscriber count, and they pay you 25% recurring on every referral you make. Your newsletter earns, your referrals earn.",
        "cta": "Start free at link in bio.",
        "tags": "#beehiiv #newsletter #passiveincome #emailmarketing",
        "affiliate_link": f"{SITE}/how-to-start-newsletter-make-money"
    },
    {
        "title": "Upload a design once. Earn royalties FOREVER. #redbubble",
        "hook": "I uploaded 20 designs to Redbubble and now earn royalties every month on autopilot.",
        "body": "Print on demand means zero inventory, zero shipping, zero customer service. Redbubble handles everything. You just upload the design once and collect royalties when it sells. T-shirts, phone cases, mugs, posters, stickers — all from one upload. I also list on Teepublic and Society6 for double and triple the income from the same design.",
        "cta": "Guide at link in bio.",
        "tags": "#redbubble #printondemand #passiveincome #sidehustle",
        "affiliate_link": f"{SITE}/best-print-on-demand-sites-2026"
    },
    {
        "title": "This affiliate program pays $1000 per referral #affiliatemarketing",
        "hook": "HubSpot pays up to $1,000 for every person you refer. Every. Single. One.",
        "body": "HubSpot has one of the highest-paying affiliate programs available. Their product is genuinely the best free CRM on the market, so recommending it honestly is easy. One referral per month at their average payout beats most part-time jobs. Ahrefs pays $200 per sale, WP Engine pays $200-plus, Kinsta pays 10 percent recurring forever.",
        "cta": "Full affiliate program list at link in bio.",
        "tags": "#affiliatemarketing #passiveincome #makemoney #sidehustle",
        "affiliate_link": f"{SITE}/best-ai-tools-entrepreneurs-2026"
    },
]

def generate_video_script(script_data):
    if not ANTHROPIC_KEY:
        return script_data
    resp = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 400,
              "messages": [{"role": "user", "content": f"""
Rewrite this YouTube Shorts script to be more engaging and conversational. Keep it under 55 seconds spoken.
Hook: {script_data["hook"]}
Body: {script_data["body"]}
CTA: {script_data["cta"]}
Output only the spoken script text, no labels."""}]},
        timeout=20)
    if resp.ok:
        script_data["spoken_script"] = resp.json()["content"][0]["text"]
    return script_data

def create_text_video(script_text, output_path):
    """Create simple text-on-black video using FFMPEG"""
    try:
        # Escape special chars for ffmpeg drawtext
        safe_text = script_text[:200].replace("'", "").replace(":", "").replace("\n", " ")
        lines = [safe_text[i:i+40] for i in range(0, min(len(safe_text), 160), 40)]
        text_block = "\n".join(lines)

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:size=1080x1920:duration=30:rate=30",
            "-vf", f"drawtext=text='{text_block[:100]}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"FFMPEG error: {e}")
        return False

def run():
    today = datetime.date.today().timetuple().tm_yday
    script_data = SHORTS_SCRIPTS[today % len(SHORTS_SCRIPTS)]

    print(f"Generating Short: {script_data['title']}")

    # Generate enhanced script
    script_data = generate_video_script(script_data)
    spoken = script_data.get("spoken_script", f"{script_data['hook']} {script_data['body']} {script_data['cta']}")

    # Save script for manual review / upload
    output_dir = Path("data/youtube_shorts")
    output_dir.mkdir(exist_ok=True)

    date_str = datetime.date.today().isoformat()
    script_file = output_dir / f"short_{date_str}.json"
    with open(script_file, "w") as f:
        json.dump({
            "date": date_str,
            "title": script_data["title"],
            "script": spoken,
            "description": f"{spoken[:300]}\n\nFull guide: {script_data['affiliate_link']}\n\n{script_data['tags']}",
            "tags": script_data["tags"].split(),
            "affiliate_link": script_data["affiliate_link"]
        }, f, indent=2)

    print(f"Script saved: {script_file}")
    print(f"Title: {script_data['title']}")
    print(f"Script: {spoken[:200]}...")
    print("\n📹 To create actual video:")
    print(f"  1. Use ElevenLabs TTS on script text")
    print(f"  2. Add to simple background using CapCut/Adobe (or ffmpeg)")
    print(f"  3. Upload to YouTube as Short")
    print(f"  4. Description: {script_data['affiliate_link']}")

if __name__ == "__main__":
    run()
