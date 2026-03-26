#!/usr/bin/env python3
"""Generate DALL-E 3 images for all NY Spotlight Report articles."""

import requests
import os
import sys
import time
import json

API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY not set in environment")
    sys.exit(1)

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "site", "images", "articles")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Article slug -> DALL-E prompt mapping
ARTICLE_PROMPTS = {
    "10-years-behind-the-scenes-entertainment": "Professional editorial photograph of a backstage scene at a major entertainment venue, stage crew working behind curtains with dramatic stage lighting visible, photojournalistic style, cinematic, 16:9 aspect ratio",
    "100-million-broadway-season-2024": "Professional editorial photograph of Broadway theater marquees lit up at night on 42nd Street Times Square, New York City, golden hour glow mixed with neon, dramatic lighting, photojournalistic style, 16:9",
    "bushwick-open-studios-2026": "Professional editorial photograph of an artist open studio event in a Bushwick Brooklyn warehouse loft, colorful paintings on brick walls, visitors exploring art, natural light streaming through industrial windows, photojournalistic style, 16:9",
    "chelsea-gallery-district-2024": "Professional editorial photograph of a modern art gallery opening in Chelsea NYC, people viewing large contemporary art pieces in a minimalist white-walled space, warm gallery lighting, photojournalistic style, 16:9",
    "emerging-designers-nyc-2026": "Professional editorial photograph of an emerging fashion designer's studio in NYC with fabric swatches, dress forms, and a young designer sketching, creative workspace, natural light, photojournalistic style, 16:9",
    "evolution-of-drag-culture": "Professional editorial photograph of a glamorous drag queen performing on a brightly lit NYC nightclub stage, spectacular sequined costume, dramatic stage lighting with purple and gold, audience visible, photojournalistic style, 16:9",
    "fashion-nightlife-nyc": "Professional editorial photograph of fashionable New Yorkers arriving at an exclusive nightclub in the Meatpacking District, velvet rope line, neon signage, stylish outfits, nighttime urban setting, photojournalistic style, 16:9",
    "gallery-weekend-art-parties": "Professional editorial photograph of a crowded gallery opening night party in NYC, people mingling with wine glasses amid contemporary sculptures and paintings, warm ambient lighting, photojournalistic style, 16:9",
    "grammy-highlights-nyc-artists": "Professional editorial photograph of a live music performance at a prestigious NYC venue, singer at microphone with band under golden spotlight, Grammy-worthy energy, audience silhouettes, photojournalistic style, 16:9",
    "hells-kitchen-gay-nightlife-capital": "Professional editorial photograph of the vibrant Hell's Kitchen neighborhood at night with rainbow flags, glowing bar fronts along Ninth Avenue, diverse groups of people socializing outside bars, warm street lighting, photojournalistic style, 16:9",
    "immersive-theater-nyc-2026": "Professional editorial photograph of an immersive theater experience with actors performing among the audience in a transformed warehouse space, dramatic atmospheric lighting, fog effects, photojournalistic style, 16:9",
    "late-night-nyc-after-midnight": "Professional editorial photograph of a late-night NYC scene, neon-lit streets of Lower Manhattan after midnight, a jazz club entrance glowing warmly, yellow taxi passing, moody cinematic atmosphere, photojournalistic style, 16:9",
    "lgbtq-bars-clubs-nyc-guide": "Professional editorial photograph of a stylish queer-friendly bar interior in NYC, warm Edison bulb lighting, rainbow accents, diverse patrons having fun at the bar, welcoming atmosphere, photojournalistic style, 16:9",
    "lgbtq-film-festivals-2026": "Professional editorial photograph of an indie film screening at a NYC art house cinema, audience watching a film with projector light visible, LGBTQ film festival banner, intimate venue setting, photojournalistic style, 16:9",
    "long-island-fashion-scene": "Professional editorial photograph of a fashion boutique on a charming Long Island main street, mannequins in the window display with autumn styling, tree-lined sidewalk, golden hour light, photojournalistic style, 16:9",
    "long-island-north-shore-culture": "Professional editorial photograph of the Long Island North Shore Gold Coast, historic mansion estate with manicured gardens, Long Island Sound visible in background, golden afternoon light, photojournalistic style, 16:9",
    "long-island-wine-country-nightlife": "Professional editorial photograph of a Long Island vineyard at sunset with string lights illuminating an outdoor wine tasting event, guests socializing among grapevines, warm golden hour atmosphere, photojournalistic style, 16:9",
    "nyc-comedy-scene-guide": "Professional editorial photograph of a stand-up comedian performing at a classic brick-wall comedy club in Greenwich Village NYC, single spotlight on performer, audience laughing, intimate venue, photojournalistic style, 16:9",
    "nyc-jazz-renaissance-2024": "Professional editorial photograph of a live jazz performance in an intimate NYC club, saxophone player in spotlight with upright bass and piano visible, blue and amber mood lighting, smoke effect, photojournalistic style, 16:9",
    "nyc-street-style-report-2026": "Professional editorial photograph of stylish New Yorkers walking on a SoHo cobblestone street, diverse street style fashion, cast iron buildings in background, natural daylight, fashion editorial feel, photojournalistic style, 16:9",
    "nyfw-2026-recap": "Professional editorial photograph of models walking a New York Fashion Week runway at Spring Studios, dramatic overhead lighting, front row photographers with flash, high fashion atmosphere, photojournalistic style, 16:9",
    "oscars-2026-predictions": "Professional editorial photograph of a golden Academy Award Oscar statuette with dramatic gold and amber lighting, red carpet bokeh in background, cinematic atmosphere, photojournalistic style, 16:9",
    "pride-2026-nyc-events": "Professional editorial photograph of a vibrant NYC Pride parade on Fifth Avenue with rainbow flags waving, diverse joyful crowd celebrating, confetti in the air, bright summer sunlight, photojournalistic style, 16:9",
    "rooftop-bars-manhattan-2024": "Professional editorial photograph of an upscale Manhattan rooftop bar at twilight with the Empire State Building illuminated in the background, cocktail glasses on railing, string lights, photojournalistic style, 16:9",
    "street-art-murals-nyc-2026": "Professional editorial photograph of a massive colorful street art mural on a Bushwick Brooklyn building wall, artist on scaffolding painting, urban setting with pedestrians, vibrant daylight, photojournalistic style, 16:9",
    "sundance-to-screen-nyc-2026": "Professional editorial photograph of an independent film premiere at a NYC cinema, red carpet with filmmakers and a projection screen showing opening credits, intimate festival atmosphere, photojournalistic style, 16:9",
    "sustainable-fashion-nyc-guide": "Professional editorial photograph of a sustainable fashion pop-up shop in a bright NYC loft space, eco-friendly clothing on wooden racks, plants and natural materials, warm natural light, photojournalistic style, 16:9",
    "tony-awards-2026-preview": "Professional editorial photograph of the Tony Awards ceremony stage at Radio City Music Hall, golden trophy on podium, dramatic theatrical lighting with red curtains, photojournalistic style, 16:9",
    "trans-visibility-entertainment": "Professional editorial photograph of a diverse group of performers taking a curtain call on a Broadway stage, standing ovation from audience, warm spotlight, pride and celebration, inclusive and uplifting, photojournalistic style, 16:9",
    "ultimate-nyc-nightlife-guide": "Professional editorial photograph of an iconic NYC nightclub dance floor at peak hour, DJ booth with LED lights, energetic diverse crowd dancing, purple and blue laser lighting, photojournalistic style, 16:9",
    "vinyl-record-bars-nyc": "Professional editorial photograph of a vinyl record bar in East Village NYC, turntable spinning a record in foreground, shelves of vinyl records behind bar, warm amber lighting, cocktails on counter, photojournalistic style, 16:9",
}


def generate_image(slug, prompt, retries=3):
    """Generate a DALL-E 3 image and save it."""
    filepath = os.path.join(IMAGES_DIR, f"{slug}.jpg")

    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        print(f"  SKIP (exists): {slug}")
        return filepath

    for attempt in range(retries):
        try:
            print(f"  Generating: {slug} (attempt {attempt + 1})...")
            resp = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1792x1024",
                    "quality": "hd",
                },
                timeout=120,
            )

            if resp.status_code == 429:
                wait = 65
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code == 402:
                print(f"  ERROR: Insufficient funds / billing issue")
                return None

            if resp.status_code != 200:
                print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
                if attempt < retries - 1:
                    time.sleep(10)
                continue

            data = resp.json()
            url = data["data"][0]["url"]

            img_resp = requests.get(url, timeout=60)
            if img_resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(img_resp.content)
                print(f"  OK: {slug} ({len(img_resp.content)} bytes)")
                return filepath
            else:
                print(f"  ERROR downloading image: {img_resp.status_code}")

        except Exception as e:
            print(f"  Exception: {e}")
            if attempt < retries - 1:
                time.sleep(10)

    return None


def main():
    print(f"=== DALL-E 3 Article Image Generator ===")
    print(f"Articles to process: {len(ARTICLE_PROMPTS)}")
    print(f"Output directory: {IMAGES_DIR}")
    print()

    results = {"success": [], "failed": [], "skipped": []}

    for i, (slug, prompt) in enumerate(ARTICLE_PROMPTS.items(), 1):
        print(f"[{i}/{len(ARTICLE_PROMPTS)}] {slug}")
        filepath = generate_image(slug, prompt)

        if filepath and os.path.exists(filepath):
            if "SKIP" not in str(filepath):
                results["success"].append(slug)
            else:
                results["skipped"].append(slug)
        else:
            results["failed"].append(slug)

        # Small delay between requests to avoid rate limits
        if filepath and i < len(ARTICLE_PROMPTS):
            time.sleep(2)

    print()
    print(f"=== RESULTS ===")
    print(f"Generated: {len(results['success'])}")
    print(f"Skipped (already existed): {len(results['skipped'])}")
    print(f"Failed: {len(results['failed'])}")
    if results["failed"]:
        print(f"Failed articles: {', '.join(results['failed'])}")

    # Write results to JSON for the HTML updater
    with open(os.path.join(os.path.dirname(__file__), "image_gen_results.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
