#!/usr/bin/env python3
"""
PromptBase Store Builder — NYSR Agency
Creates and manages AI prompt listings on PromptBase.
Each prompt sells for $1.99-9.99. Zero marginal cost.
High-demand categories: marketing, business, coding, art.
"""
import os, requests, json, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("PromptBaseBot")

PROMPTS = [
    {
        "title": "Viral Twitter Thread Generator for Any Topic",
        "price": 2.99,
        "desc": "Generate high-engagement Twitter threads that go viral. Just input your topic and get a 10-tweet thread with hook, value bombs, and CTA.",
        "prompt": """You are a viral Twitter thread writer. Create a 10-tweet thread about [TOPIC].

Tweet 1 (Hook): Start with a shocking stat or bold claim that stops the scroll.
Tweets 2-8 (Value): Each tweet = 1 actionable insight. Short. Punchy. No fluff.
Tweet 9 (Proof): Add credibility - data, results, or social proof.
Tweet 10 (CTA): Tell readers what to do next + ask them to RT if useful.

Format: Number each tweet. Keep each under 240 chars. Use line breaks.
Make it feel human, not AI-generated. Conversational tone.""",
        "category": "marketing"
    },
    {
        "title": "Cold Email That Actually Gets Replies",
        "price": 3.99,
        "desc": "Write personalized cold emails with 30%+ open rates. Uses proven AIDA framework with pattern interrupts.",
        "prompt": """Write a cold outreach email for [PURPOSE] targeting [TARGET_AUDIENCE].

Requirements:
- Subject line: 5-7 words, create curiosity not spam
- Opening: Reference something specific about them (not generic)
- Problem: Name their likely pain point in their own words
- Solution: Brief mention of what you do (1-2 sentences max)
- Social proof: One relevant result or client
- CTA: One specific easy ask (15 min call, quick reply, yes/no question)
- Length: Under 150 words total
- Tone: Peer-to-peer, not salesy

Output the subject line separately, then the email body.""",
        "category": "business"
    },
    {
        "title": "SEO Blog Post Outline Generator (Ranks on Google)",
        "price": 4.99,
        "desc": "Generate complete SEO blog post outlines that rank. Includes H1, H2s, LSI keywords, meta description, and featured snippet target.",
        "prompt": """Create a comprehensive SEO blog post outline for the keyword: [TARGET_KEYWORD]

Include:
1. Optimized H1 title (include keyword, under 60 chars)
2. Meta description (include keyword, 150-160 chars, include CTA)
3. Introduction hook (first 100 words that keep readers reading)
4. 6-8 H2 sections with 2-3 H3 sub-points each
5. Featured snippet target (answer the main question in 40-60 words)
6. LSI keywords to include naturally (list 10)
7. Internal link opportunities (suggest 3 related post ideas)
8. Conclusion with CTA
9. Recommended word count for this topic

For each H2, include: what to cover + why it ranks.""",
        "category": "writing"
    },
    {
        "title": "Passive Income Business Plan in 60 Seconds",
        "price": 2.99,
        "desc": "Generate a complete passive income business plan for any niche. Includes revenue model, traffic sources, and 90-day action plan.",
        "prompt": """Create a detailed passive income business plan for: [NICHE/IDEA]

Structure:
**Business Model**: How money is made (be specific about revenue streams)
**Target Market**: Who buys + why they pay
**Content Strategy**: What content drives traffic (3 types, 1 platform each)
**Product Stack**: 3 products at 3 price points ($7-15 / $47-97 / $197-497)
**Traffic Plan**: Top 3 free traffic channels for this niche + timeline
**90-Day Milestones**: Week 1-4, Month 2, Month 3 specific goals
**Revenue Projection**: Conservative/Realistic/Optimistic monthly at 90 days
**Startup Cost**: What it costs to start ($0 version + premium version)
**First 3 Actions**: What to do TODAY to start

Be specific. No generic advice. Assume the person has $0 budget.""",
        "category": "business"
    },
    {
        "title": "YouTube Script That Keeps People Watching",
        "price": 3.99,
        "desc": "Write YouTube scripts optimized for watch time and CTR. Proven hook formula, retention loops, and end screen CTA.",
        "prompt": """Write a YouTube video script about [TOPIC] targeting [AUDIENCE].

Format:
**TITLE** (3 options, each under 60 chars, include curiosity gap)
**THUMBNAIL IDEA** (describe the visual)
**HOOK** (0-30 seconds): Open with the payoff. Tell them exactly what they'll get.
**INTRO** (30-90 seconds): Who you are in 1 sentence. Why watch THIS video.
**SECTION 1-4**: Each section needs an open loop at the end to keep watching.
**MIDROLL HOOK** (at 50% mark): Re-engage viewers who are about to leave.
**MAIN VALUE**: The core content — 3-7 key points.
**CTA**: What to click/subscribe to next.

Target length: [LENGTH] minutes
Tone: [TONE — educational/entertaining/authoritative]
Add [IN BRACKETS] wherever the creator should show something on screen.""",
        "category": "video"
    },
]

def display_prompts():
    total = sum(p["price"] for p in PROMPTS)
    log.info(f"PromptBase catalog: {len(PROMPTS)} prompts | ${total:.2f} total value")
    for p in PROMPTS:
        log.info(f"  ${p['price']:.2f} — {p['title'][:55]}")
    log.info("\nSetup: promptbase.com → Sell → Upload each prompt")
    log.info("At 10 sales/month per prompt = $150-200/mo passive")

if __name__ == "__main__":
    display_prompts()
    with open("data/promptbase_catalog.json", "w") as f:
        import json
        json.dump(PROMPTS, f, indent=2)
    log.info("Catalog saved to data/promptbase_catalog.json")
