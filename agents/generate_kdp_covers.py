#!/usr/bin/env python3
"""
KDP Cover Generator — Uses Marcus Kane's Media Production DALL-E 3 pipeline
Generates missing covers for 10 KDP books
"""
import os, json, urllib.request, base64, time, logging

log = logging.getLogger("kdp_covers")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [COVERS] %(message)s")

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
COVERS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "kdp_books", "covers")

MISSING_COVERS = {
    "social_media_content_planner_90_days_cover": {
        "title": "Social Media Content Planner",
        "prompt": "Professional ebook cover for a 90-day social media content planner, clean modern design, vibrant purple and teal gradient, social media icons subtly in background, bold white title text, premium digital product look, no text on image"
    },
    "business_plan_template_annual_cover": {
        "title": "Business Plan Template",
        "prompt": "Professional ebook cover for an annual business plan template, corporate navy blue and gold design, abstract geometric shapes, executive boardroom feel, clean minimal layout, premium digital product, no text on image"
    },
    "monthly_savings_challenge_tracker_cover": {
        "title": "Monthly Savings Challenge",
        "prompt": "Professional ebook cover for a monthly savings challenge tracker, fresh green and white color scheme, piggy bank or money jar illustration, clean modern design, motivational financial planning feel, no text on image"
    },
    "guided_meditation_journal_90_days_cover": {
        "title": "Guided Meditation Journal",
        "prompt": "Professional ebook cover for a 90-day guided meditation journal, serene lavender and soft gold colors, zen lotus flower, peaceful calming atmosphere, minimalist spiritual design, no text on image"
    },
    "sudoku_puzzles_easy_to_hard_200_puzzles_cover": {
        "title": "Sudoku Puzzles 200",
        "prompt": "Professional ebook cover for a sudoku puzzle book with 200 puzzles easy to hard, bold orange and dark blue design, sudoku grid pattern in background, brain teaser gaming feel, clean sharp design, no text on image"
    },
    "word_search_puzzles_for_adults_100_puzzles_cover": {
        "title": "Word Search Puzzles",
        "prompt": "Professional ebook cover for an adult word search puzzle book 100 puzzles, rich red and cream colors, scattered letters in background, elegant adult puzzle book design, premium quality feel, no text on image"
    },
    "daily_habit_tracker_30_day_reset_cover": {
        "title": "Daily Habit Tracker 30-Day Reset",
        "prompt": "Professional ebook cover for a 30-day daily habit tracker reset journal, energetic coral and white design, checkbox and calendar motifs, motivational self-improvement theme, clean modern layout, no text on image"
    },
    "reading_log_book_review_journal_cover": {
        "title": "Reading Log & Book Review Journal",
        "prompt": "Professional ebook cover for a reading log and book review journal, warm burgundy and cream colors, stack of books illustration, cozy literary atmosphere, bookworm aesthetic, elegant design, no text on image"
    },
    "business_plan_template_annual_planner_cover": {
        "title": "Business Plan Annual Planner",
        "prompt": "Professional ebook cover for a business plan annual planner, sleek charcoal and silver design, calendar and chart graphics, strategic planning corporate theme, premium executive look, no text on image"
    },
    "side_hustle_income_tracker_cover": {
        "title": "Side Hustle Income Tracker",
        "prompt": "Professional ebook cover for a side hustle income tracker, bold electric blue and neon green, money growth chart graphic, entrepreneurial energy, hustler motivation theme, modern clean design, no text on image"
    }
}

def generate_cover(name, prompt):
    """Generate a single cover using DALL-E 3 via OpenAI API."""
    if not OPENAI_KEY:
        log.error("OPENAI_API_KEY not set")
        return False

    log.info(f"Generating: {name}")
    data = json.dumps({
        "model": "gpt-image-1",
        "prompt": f"Book cover design, 6x9 inch portrait format, KDP paperback cover. {prompt}. High resolution, print quality, professional publishing standard.",
        "n": 1,
        "size": "1024x1536"
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        img_url = result["data"][0]["url"]

        # Download the image
        img_req = urllib.request.Request(img_url)
        img_resp = urllib.request.urlopen(img_req, timeout=30)
        img_data = img_resp.read()

        # Save to covers directory
        os.makedirs(COVERS_DIR, exist_ok=True)
        path = os.path.join(COVERS_DIR, f"{name}.jpg")
        with open(path, "wb") as f:
            f.write(img_data)

        size_kb = len(img_data) / 1024
        log.info(f"  Saved: {name}.jpg ({size_kb:.1f} KB)")
        return True

    except Exception as e:
        log.error(f"  FAILED {name}: {e}")
        return False


if __name__ == "__main__":
    log.info(f"=== KDP Cover Generator — {len(MISSING_COVERS)} covers ===")
    success = 0
    for name, info in MISSING_COVERS.items():
        if generate_cover(name, info["prompt"]):
            success += 1
        time.sleep(2)  # Rate limit
    log.info(f"=== Done: {success}/{len(MISSING_COVERS)} covers generated ===")
    if success < len(MISSING_COVERS):
        exit(1)
