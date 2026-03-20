#!/usr/bin/env python3
"""
KDP BOOK GENERATOR v1.0 — S.C. Thomas Internal Agency
Generates complete Kindle Direct Publishing ebooks.
AI-assisted, you edit and publish. $0 to publish. 35-70% royalties.
Niche: NYC guides, business tips, media industry, local journalism.
"""
import os, json, urllib.request
from datetime import datetime
from pathlib import Path

KDP_NICHES = [
    {"title": "NYC Neighborhood Guide 2026",           "pages": 60, "price": 4.99},
    {"title": "Local Journalism Survival Guide",       "pages": 80, "price": 6.99},
    {"title": "NYC Small Business Owner Handbook",     "pages": 100,"price": 7.99},
    {"title": "Content Creator NYC: Local Media 2026", "pages": 70, "price": 5.99},
    {"title": "Digital Media Strategy for Publishers", "pages": 90, "price": 8.99},
]

def generate_book_outline(title: str, pages: int, key: str) -> dict:
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514", "max_tokens": 3000,
        "messages": [{"role": "user", "content": f"""Create a complete book outline for:

Title: {title}
Target length: {pages} pages
Publisher: NY Spotlight Report

Return JSON:
{{
  "title": "{title}",
  "subtitle": "Compelling subtitle",
  "description": "200-word book description for Amazon",
  "keywords": ["keyword1", "keyword2", ...],
  "categories": ["Primary Category", "Secondary Category"],
  "chapters": [
    {{
      "number": 1,
      "title": "Chapter title",
      "summary": "What this chapter covers",
      "word_count": 1500,
      "key_points": ["point1", "point2", "point3"]
    }}
  ]
}}

Include 8-12 chapters. Make it genuinely valuable and specific."""}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"Content-Type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        text = json.loads(r.read()).get("content",[{}])[0].get("text","")
    try:
        return json.loads(text.replace("```json","").replace("```","").strip())
    except:
        return {"title": title, "chapters": []}

if __name__ == "__main__":
    key = os.getenv("ANTHROPIC_API_KEY","")
    if not key:
        print("Set ANTHROPIC_API_KEY"); exit(1)

    output = Path("kdp_books"); output.mkdir(exist_ok=True)
    print(f"\n📚 Generating {len(KDP_NICHES)} KDP book outlines...\n")

    for book in KDP_NICHES[:2]:
        print(f"  {book['title']}...")
        outline = generate_book_outline(book["title"], book["pages"], key)
        filepath = output / f"{book['title'].replace(' ','_')[:30]}_outline.json"
        filepath.write_text(json.dumps(outline, indent=2))
        chapters = len(outline.get("chapters", []))
        print(f"  ✅ {chapters} chapters | ${book['price']} | ~${book['price']*0.7*100:.0f}/mo at 100 sales")

    print(f"\nOutlines saved to: {output.absolute()}")
    print("Next: Write each chapter (use Claude), format in Calibre (free), upload to kdp.amazon.com")
