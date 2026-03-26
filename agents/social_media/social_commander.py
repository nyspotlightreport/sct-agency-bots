"""
Social Media Commander — 7 Brand Identities, 8 Platform Formats, Cross-Platform Content Engine
Generates branded content packages from articles and ProFlow case studies.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "social"
PACKAGES_DIR = DATA_DIR / "content_packages"
PROFLOW_DIR = DATA_DIR / "proflow_content"

# ---------- 7 BRAND IDENTITIES ----------
BRAND_IDENTITIES = {
    "nysr_editorial": {
        "name": "NY Spotlight Report",
        "handle": "@NYSpotlightReport",
        "voice": "Authoritative NYC media voice. Sharp, investigative, culturally aware. Breaks stories that matter to New Yorkers. Mixes hard news with cultural commentary.",
        "content_pillars": [
            "NYC business and economic news",
            "Cultural events and nightlife coverage",
            "Investigative features on local industries",
            "NYC real estate and development",
            "Local politics and community impact"
        ],
        "cta": "Read the full story on NYSpotlightReport.com",
        "hashtags": ["#NYSpotlightReport", "#NYC", "#NewYork", "#NYCNews", "#NYCBusiness"],
        "posting_frequency": "3x daily"
    },
    "proflow_results": {
        "name": "ProFlow AI",
        "handle": "@ProFlowAI",
        "voice": "Results-driven tech brand. Confident, data-backed, no-fluff. Speaks in ROI and outcomes. Makes AI accessible to small business owners.",
        "content_pillars": [
            "Client success stories and case studies",
            "AI automation tips for small businesses",
            "Industry-specific growth strategies",
            "Product feature spotlights",
            "Small business growth data and insights"
        ],
        "cta": "See what ProFlow can do for your business at myproflow.org",
        "hashtags": ["#ProFlowAI", "#SmallBusinessGrowth", "#AIAutomation", "#BusinessAI", "#GrowWithAI"],
        "posting_frequency": "2x daily"
    },
    "sc_thomas_authority": {
        "name": "S.C. Thomas",
        "handle": "@SCThomasOfficial",
        "voice": "Thought leader and entrepreneur. Personal brand mixing business wisdom, NYC culture, and tech innovation. Authentic, bold, unfiltered. Speaks from experience.",
        "content_pillars": [
            "Entrepreneurship and business building",
            "AI and technology trends",
            "NYC lifestyle and culture",
            "Leadership and personal development",
            "Media and publishing industry insights"
        ],
        "cta": "Follow for daily business and tech insights",
        "hashtags": ["#SCThomas", "#Entrepreneur", "#TechLeader", "#NYCBusiness", "#BuildInPublic"],
        "posting_frequency": "2x daily"
    },
    "nyc_nightlife_guide": {
        "name": "NYC Nightlife Guide",
        "handle": "@NYCNightlifeGuide",
        "voice": "The insider's guide to NYC after dark. Energetic, trendy, FOMO-inducing. Knows every venue, every DJ, every event worth attending.",
        "content_pillars": [
            "Club and bar reviews and recommendations",
            "Event listings and ticket giveaways",
            "DJ and artist spotlights",
            "Nightlife industry news",
            "Best-of lists and seasonal guides"
        ],
        "cta": "Tag us in your night out pics",
        "hashtags": ["#NYCNightlife", "#NYCClubs", "#NYCBars", "#NightOut", "#NYCEvents"],
        "posting_frequency": "3x daily"
    },
    "nyc_lgbtq_news": {
        "name": "NYC LGBTQ+ News",
        "handle": "@NYCLGBTQ",
        "voice": "Proud, informed, community-first. Covers LGBTQ+ news, events, rights, and culture in NYC. Celebratory and activist. Amplifies queer voices and businesses.",
        "content_pillars": [
            "LGBTQ+ rights and policy updates",
            "Queer-owned business spotlights",
            "Pride and community event coverage",
            "Cultural features and artist profiles",
            "Health and wellness resources"
        ],
        "cta": "Support queer NYC — share and follow",
        "hashtags": ["#NYCLGBTQ", "#QueerNYC", "#Pride", "#LGBTQNews", "#QueerBusiness"],
        "posting_frequency": "2x daily"
    },
    "nyc_fashion_report": {
        "name": "NYC Fashion Report",
        "handle": "@NYCFashionReport",
        "voice": "Sleek, editorial, trend-forward. Covers NYC fashion from streetwear to runway. Highlights emerging designers, local boutiques, and style culture.",
        "content_pillars": [
            "NYC street style and trend reports",
            "Designer and brand spotlights",
            "Fashion week coverage",
            "Local boutique and store reviews",
            "Style guides and seasonal lookbooks"
        ],
        "cta": "Follow for daily NYC style inspiration",
        "hashtags": ["#NYCFashion", "#StreetStyle", "#NYCStyle", "#FashionReport", "#NYCDesigners"],
        "posting_frequency": "2x daily"
    },
    "voice_ai_service": {
        "name": "Voice AI Solutions",
        "handle": "@VoiceAISolutions",
        "voice": "Tech-forward, practical, ROI-focused. Demystifies voice AI for business owners. Speaks in savings, efficiency, and customer experience improvements.",
        "content_pillars": [
            "Voice AI use cases and demos",
            "Cost comparison: AI vs. human receptionist",
            "Customer experience automation tips",
            "Industry-specific voice AI applications",
            "AI technology trends and updates"
        ],
        "cta": "Never miss another call — learn more at myproflow.org",
        "hashtags": ["#VoiceAI", "#AIReceptionist", "#BusinessAutomation", "#NeverMissACall", "#AIPhone"],
        "posting_frequency": "1x daily"
    }
}

# ---------- 8 PLATFORM FORMATS ----------
PLATFORM_FORMATS = {
    "twitter": {
        "max_length": 280,
        "style": "Punchy, hook-driven. Thread-friendly. Use line breaks for emphasis. Emojis sparingly.",
        "media": "Image or short video clip",
        "format_template": "{hook}\n\n{key_point}\n\n{cta}\n\n{hashtags}"
    },
    "linkedin": {
        "max_length": 3000,
        "style": "Professional but not boring. Story-driven. Use line breaks heavily. Start with a bold statement or question.",
        "media": "Article image or infographic",
        "format_template": "{hook}\n\n{story}\n\n{key_points}\n\n{cta}\n\n{hashtags}"
    },
    "instagram": {
        "max_length": 2200,
        "style": "Visual-first. Caption is secondary to image. Conversational, authentic. Heavy hashtag usage in first comment.",
        "media": "High-quality image or carousel",
        "format_template": "{hook}\n\n{body}\n\n{cta}\n\n.\n.\n.\n{hashtags}"
    },
    "tiktok": {
        "max_length": 300,
        "style": "Hook in first 2 seconds. Trendy, fast-paced. Speak directly to camera or use text overlays. Pattern interrupt.",
        "media": "Short-form video (15-60 seconds)",
        "format_template": "HOOK: {hook}\n\nSCRIPT: {script}\n\nCTA: {cta}\n\n{hashtags}"
    },
    "facebook": {
        "max_length": 5000,
        "style": "Conversational, community-oriented. Ask questions. Encourage comments. Share stories.",
        "media": "Image, video, or link preview",
        "format_template": "{hook}\n\n{body}\n\n{cta}\n\nWhat do you think? Drop your thoughts below.\n\n{hashtags}"
    },
    "threads": {
        "max_length": 500,
        "style": "Casual, conversational, slightly edgy. Like Twitter but more personal. Thread-native.",
        "media": "Optional image",
        "format_template": "{hook}\n\n{key_point}\n\n{cta}"
    },
    "reddit": {
        "max_length": 10000,
        "style": "Value-first. No self-promotion vibes. Educational, detailed, genuine. Respond to the subreddit's culture.",
        "media": "Text post with optional image",
        "format_template": "Title: {title}\n\n{body}\n\nTL;DR: {tldr}"
    },
    "pinterest": {
        "max_length": 500,
        "style": "Aspirational, visual, searchable. Use keywords for discoverability. Tips and how-tos perform best.",
        "media": "Vertical pin image (2:3 ratio)",
        "format_template": "Pin Title: {title}\n\nDescription: {body}\n\n{hashtags}"
    }
}


def generate_content_package(article: dict, brand_key: str = "nysr_editorial") -> dict:
    """
    Generate a cross-platform content package from an article.
    Returns content formatted for all 8 platforms using the specified brand voice.
    """
    brand = BRAND_IDENTITIES.get(brand_key, BRAND_IDENTITIES["nysr_editorial"])
    title = article.get("title", "")
    summary = article.get("summary", "")
    key_points = article.get("key_points", [])
    url = article.get("url", "")

    package = {
        "id": hashlib.md5(f"{title}{brand_key}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        "article_title": title,
        "brand": brand_key,
        "brand_name": brand["name"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platforms": {}
    }

    hashtags_str = " ".join(brand["hashtags"][:5])
    hook = title if len(title) <= 100 else title[:97] + "..."
    key_points_text = "\n".join(f"- {kp}" for kp in key_points[:5]) if key_points else summary
    cta = brand["cta"]

    for platform, fmt in PLATFORM_FORMATS.items():
        max_len = fmt["max_length"]

        if platform == "twitter":
            content = f"{hook}\n\n{summary[:120] if summary else ''}\n\n{cta}\n\n{hashtags_str}"
            if len(content) > max_len:
                content = f"{hook}\n\n{cta}\n\n{hashtags_str}"
            if len(content) > max_len:
                content = f"{hook[:200]}\n\n{hashtags_str}"

        elif platform == "linkedin":
            content = f"{hook}\n\n{summary}\n\n{key_points_text}\n\n{cta}\n\n{hashtags_str}"

        elif platform == "instagram":
            content = f"{hook}\n\n{summary}\n\n{cta}\n\n.\n.\n.\n{hashtags_str}"

        elif platform == "tiktok":
            script = summary[:200] if summary else "Check this out..."
            content = f"HOOK: {hook}\n\nSCRIPT: {script}\n\nCTA: {cta}\n\n{hashtags_str}"

        elif platform == "facebook":
            content = f"{hook}\n\n{summary}\n\n{key_points_text}\n\n{cta}\n\nWhat do you think? Drop your thoughts below.\n\n{hashtags_str}"

        elif platform == "threads":
            content = f"{hook}\n\n{summary[:300] if summary else ''}\n\n{cta}"

        elif platform == "reddit":
            tldr = summary[:150] if summary else hook
            content = f"Title: {title}\n\n{summary}\n\n{key_points_text}\n\nTL;DR: {tldr}"

        elif platform == "pinterest":
            content = f"Pin Title: {title}\n\nDescription: {summary}\n\n{hashtags_str}"

        else:
            content = f"{hook}\n\n{summary}\n\n{cta}"

        package["platforms"][platform] = {
            "content": content[:max_len],
            "media_type": fmt["media"],
            "style_guide": fmt["style"],
            "character_count": len(content[:max_len])
        }

    return package


def generate_proflow_social_content(case_study: dict) -> dict:
    """
    Generate social content specifically for ProFlow case studies.
    Uses proflow_results brand identity.
    """
    brand = BRAND_IDENTITIES["proflow_results"]
    biz = case_study.get("business_name", "a local business")
    industry = case_study.get("industry", "small business")
    result = case_study.get("result", "saw incredible growth")
    metric = case_study.get("metric", "")
    timeframe = case_study.get("timeframe", "90 days")

    hashtags_str = " ".join(brand["hashtags"])

    package = {
        "id": hashlib.md5(f"proflow_{biz}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        "type": "proflow_case_study",
        "business_name": biz,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platforms": {}
    }

    twitter_content = f"Case Study: {biz} {result} in just {timeframe}.\n\n{metric}\n\nThis is what AI automation looks like for {industry}.\n\n{hashtags_str}"
    linkedin_content = (
        f"Real results from a real {industry} business.\n\n"
        f"{biz} was struggling with the same challenges every {industry} owner faces.\n\n"
        f"After implementing ProFlow AI:\n- {result}\n- {metric}\n- Timeline: {timeframe}\n\n"
        f"The best part? It runs 24/7 with zero manual work.\n\n"
        f"If you are a {industry} owner, I would love to show you how to get similar results.\n\n"
        f"{brand['cta']}\n\n{hashtags_str}"
    )
    instagram_content = (
        f"From struggling to thriving. {biz} did it in {timeframe}.\n\n"
        f"The result: {result}\n{metric}\n\n"
        f"AI automation is not the future. It is right now.\n\n"
        f"{brand['cta']}\n\n.\n.\n.\n{hashtags_str}"
    )
    tiktok_content = (
        f"HOOK: This {industry} went from struggling to CRUSHING it in {timeframe}\n\n"
        f"SCRIPT: {biz} was losing customers every day. Then they tried ProFlow AI. "
        f"Result? {result}. {metric}. All automated.\n\n"
        f"CTA: Link in bio to see how.\n\n{hashtags_str}"
    )

    package["platforms"] = {
        "twitter": {"content": twitter_content[:280], "media_type": "Before/after graphic"},
        "linkedin": {"content": linkedin_content[:3000], "media_type": "Case study infographic"},
        "instagram": {"content": instagram_content[:2200], "media_type": "Carousel: problem -> solution -> results"},
        "tiktok": {"content": tiktok_content[:300], "media_type": "Short-form video with text overlays"},
        "facebook": {"content": linkedin_content[:5000], "media_type": "Link to case study page"},
        "threads": {"content": twitter_content[:500], "media_type": "Optional image"},
        "reddit": {"content": f"Title: How a {industry} used AI to {result}\n\n{linkedin_content}", "media_type": "Text post"},
        "pinterest": {"content": f"Pin Title: {industry} AI Success Story\n\nDescription: {biz} {result} in {timeframe}. {metric}\n\n{hashtags_str}", "media_type": "Vertical infographic"}
    }

    return package


def save_content_package(package: dict, output_dir: Path = PACKAGES_DIR):
    """Save a content package to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{package['id']}_{package.get('brand', 'content')}.json"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(package, f, indent=2)
    print(f"[+] Saved content package: {filepath}")
    return filepath


def run_daily_content_generation(articles: list[dict] | None = None):
    """
    Daily content generation pipeline:
    1. Process articles into cross-platform content packages
    2. Generate ProFlow-specific case study content
    3. Save all packages to disk
    """
    if articles is None:
        articles = [
            {
                "title": "NYC Small Businesses Embrace AI Automation in 2026",
                "summary": "A growing wave of NYC small businesses are adopting AI-powered automation tools to compete with larger chains. From restaurants to law firms, AI is leveling the playing field.",
                "key_points": [
                    "72% of NYC small businesses plan to adopt AI tools by end of 2026",
                    "Average ROI for AI automation: 340% within 90 days",
                    "Top use cases: customer service, review management, lead generation",
                    "Restaurants and salons seeing the fastest adoption rates",
                    "Voice AI replacing traditional receptionists across healthcare and legal"
                ],
                "url": "https://nyspotlightreport.com/nyc-small-business-ai-2026"
            }
        ]

    all_packages = []

    # Generate content for each article across multiple brand identities
    for article in articles:
        for brand_key in ["nysr_editorial", "sc_thomas_authority", "proflow_results"]:
            package = generate_content_package(article, brand_key)
            save_content_package(package, PACKAGES_DIR)
            all_packages.append(package)

    # Generate ProFlow case study content
    case_studies = [
        {"business_name": "Lucia's Trattoria", "industry": "restaurant", "result": "went from 3.6 to 4.7 stars on Google", "metric": "Weekend reservations up 34%", "timeframe": "90 days"},
        {"business_name": "Glow Studio", "industry": "salon", "result": "increased rebooking rate to 81%", "metric": "No-shows dropped from 8/week to 1", "timeframe": "60 days"},
        {"business_name": "Torres Realty Group", "industry": "real estate", "result": "closed 7 additional deals", "metric": "Lead response time: 47 seconds", "timeframe": "one quarter"},
        {"business_name": "Martinez & Associates", "industry": "law firm", "result": "captured 14 new qualified clients", "metric": "8 from after-hours inquiries", "timeframe": "30 days"},
        {"business_name": "FitBox Studios", "industry": "fitness studio", "result": "reached 91% class fill rate", "metric": "Churn dropped from 11% to 4.2%", "timeframe": "60 days"},
    ]

    for cs in case_studies:
        package = generate_proflow_social_content(cs)
        save_content_package(package, PROFLOW_DIR)
        all_packages.append(package)

    print(f"\n[+] Daily content generation complete.")
    print(f"    Articles processed: {len(articles)}")
    print(f"    Brand variants: {len(articles) * 3}")
    print(f"    ProFlow case studies: {len(case_studies)}")
    print(f"    Total packages: {len(all_packages)}")
    print(f"    Platforms per package: {len(PLATFORM_FORMATS)}")
    print(f"    Total content pieces: {len(all_packages) * len(PLATFORM_FORMATS)}")

    return all_packages


if __name__ == "__main__":
    run_daily_content_generation()
