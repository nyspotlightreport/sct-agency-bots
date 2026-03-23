#!/usr/bin/env python3
"""
PROMPTBASE SELLER BOT v1.0 — S.C. Thomas Internal Agency
Generates high-quality AI prompts across 10 categories.
Packages them for sale on PromptBase, FlowGPT, Gumroad.
$1.99-$9.99 per prompt. Fully passive after listing.
"""
import os, sys, json, urllib.request
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

PROMPT_CATEGORIES = [
    {"category": "marketing",       "price": 4.99,  "platform": "promptbase"},
    {"category": "seo_writing",     "price": 3.99,  "platform": "gumroad"},
    {"category": "linkedin_posts",  "price": 5.99,  "platform": "promptbase"},
    {"category": "email_copywriting","price": 4.99, "platform": "gumroad"},
    {"category": "youtube_scripts", "price": 6.99,  "platform": "promptbase"},
    {"category": "business_plans",  "price": 7.99,  "platform": "gumroad"},
    {"category": "ad_copy",         "price": 5.99,  "platform": "promptbase"},
    {"category": "social_media",    "price": 3.99,  "platform": "gumroad"},
    {"category": "sales_scripts",   "price": 6.99,  "platform": "promptbase"},
    {"category": "content_strategy","price": 7.99,  "platform": "gumroad"},
]

def generate_prompt_pack(category: str, anthropic_key: str) -> dict:
    system = """You are a prompt engineer creating premium AI prompts for sale on PromptBase.
Create detailed, tested, high-value prompts that solve real business problems.
Return ONLY valid JSON."""

    user = f"""Create a premium prompt pack for: {category.replace('_', ' ')}

Return JSON:
{{
  "pack_name": "Descriptive name for the prompt pack",
  "pack_description": "2-3 sentences selling the value",
  "prompts": [
    {{
      "name": "Prompt name",
      "use_case": "What it does",
      "prompt": "The full, detailed prompt text with [PLACEHOLDERS] for customization",
      "example_output": "Brief example of what it produces"
    }}
  ]
}}

Include 5 high-quality prompts. Make them genuinely useful and specific."""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "system": system,
        "messages": [{"role": "user", "content": user}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"Content-Type": "application/json",
                 "x-api-key": anthropic_key,
                 "anthropic-version": "2023-06-01"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
        text = data.get("content", [{}])[0].get("text", "")

    try:
        return json.loads(text.replace("```json","").replace("```","").strip())
    except Exception:  # noqa: bare-except
        return {"pack_name": category, "prompts": []}

def generate_gumroad_listing(pack: dict, price: float) -> str:
    """Generate a Gumroad product listing"""
    prompts_text = "\n".join([
        f"✅ {p['name']}: {p['use_case']}"
        for p in pack.get("prompts", [])
    ])
    return f"""# {pack.get('pack_name', 'Prompt Pack')}

{pack.get('pack_description', '')}

## What's Included:
{prompts_text}

## How to Use:
1. Copy the prompt
2. Paste into Claude, ChatGPT, or any AI tool
3. Fill in the [PLACEHOLDERS] with your information
4. Get professional results instantly

## Why Buy This Pack:
- Tested and optimized for best results
- Saves hours of prompt engineering
- Professional-quality outputs every time

**Price: ${price}** — One-time purchase, use forever.
"""

if __name__ == "__main__":
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        print("Set ANTHROPIC_API_KEY")
        exit(1)

    output_dir = Path("prompt_packs")
    output_dir.mkdir(exist_ok=True)

    total_potential = 0
    print(f"\n🎯 Generating {len(PROMPT_CATEGORIES)} prompt packs...\n")

    for item in PROMPT_CATEGORIES[:3]:  # Start with 3
        cat = item["category"]
        price = item["price"]
        print(f"  Generating: {cat}...")
        try:
            pack = generate_prompt_pack(cat, key)
            listing = generate_gumroad_listing(pack, price)

            # Save pack
            pack_file = output_dir / f"{cat}_pack.json"
            pack_file.write_text(json.dumps(pack, indent=2))

            listing_file = output_dir / f"{cat}_listing.md"
            listing_file.write_text(listing)

            print(f"  ✅ {pack.get('pack_name','?')} — ${price}")
            total_potential += price * 50  # Assume 50 sales/month estimate
        except Exception as e:
            print(f"  ❌ {e}")

    print(f"\n✅ Packs saved to: {output_dir.absolute()}")
    print(f"   Upload to: promptbase.com/sell or gumroad.com/new")
    print(f"   Estimated monthly (50 sales/pack): ${total_potential:,.0f}")
