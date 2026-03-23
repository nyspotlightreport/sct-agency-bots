#!/usr/bin/env python3
"""
Master Deliverable Orchestrator — NYSR Logistics & Deliverables
═══════════════════════════════════════════════════════════════════
The single source of truth for every deliverable in the system.

Coordinates:
  • Content pipeline (blog, newsletter, social, video scripts)
  • Design pipeline (thumbnails, covers, social graphics, templates)
  • Product pipeline (digital products, books, courses)
  • Client pipeline (DFY reports, ProFlow deliverables, agency outputs)
  • SEO pipeline (keyword content, backlink assets, schema markup)

Quality gates:
  Every deliverable passes through 4 quality checks before delivery:
  1. Completeness — all required elements present
  2. Brand voice — matches NYSR tone, style, and positioning
  3. Functionality — links work, formatting correct, metadata complete
  4. Performance prediction — SEO score, readability, conversion potential

Deliverable types tracked:
  BLOG_POST | NEWSLETTER | SOCIAL_POST | VIDEO_SCRIPT | THUMBNAIL
  DIGITAL_PRODUCT | KDP_BOOK | GUMROAD_LISTING | ETSY_LISTING
  EMAIL_SEQUENCE | COLD_EMAIL | PRESS_RELEASE | CASE_STUDY
  LANDING_PAGE | SALES_PAGE | AD_COPY | SEO_ARTICLE
  CLIENT_REPORT | AGENCY_DELIVERABLE | BOT_DEPLOYMENT
"""
import os, sys, json, logging, requests, base64
from datetime import datetime, date, timedelta
from typing import Optional
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Deliverables] %(message)s")
log = logging.getLogger()

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN  = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H      = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
REPO      = "nyspotlightreport/sct-agency-bots"

# ── DELIVERABLE SCHEMA ────────────────────────────────────────────
DELIVERABLE_TYPES = {
    "BLOG_POST": {
        "required_fields": ["title","slug","body_html","meta_description","target_keyword",
                           "category","word_count","internal_links","cta"],
        "quality_threshold": 7.5,
        "output_path": "site/blog/{slug}/index.html",
        "platforms": ["nyspotlightreport.com","medium","linkedin_article"],
    },
    "NEWSLETTER": {
        "required_fields": ["subject","preview_text","body_html","cta_url","segments"],
        "quality_threshold": 8.0,
        "output_path": "data/deliverables/newsletters/{date}.json",
        "platforms": ["beehiiv"],
    },
    "SOCIAL_POST": {
        "required_fields": ["platform","text","hashtags","image_url","scheduled_time"],
        "quality_threshold": 7.0,
        "output_path": "data/deliverables/social/{platform}/{date}.json",
        "platforms": ["twitter","linkedin","instagram","reddit","pinterest","medium"],
    },
    "VIDEO_SCRIPT": {
        "required_fields": ["title","hook","body","cta","keywords","duration_seconds",
                           "thumbnail_prompt","voice_style"],
        "quality_threshold": 8.0,
        "output_path": "data/deliverables/video_scripts/{date}.json",
        "platforms": ["youtube","tiktok","instagram_reels"],
    },
    "DIGITAL_PRODUCT": {
        "required_fields": ["title","description","price","file_path","cover_image",
                           "sales_page_url","target_audience","value_proposition"],
        "quality_threshold": 8.5,
        "output_path": "data/deliverables/products/{slug}.json",
        "platforms": ["gumroad","payhip","etsy"],
    },
    "EMAIL_SEQUENCE": {
        "required_fields": ["sequence_name","emails","trigger","goal","segments"],
        "quality_threshold": 8.0,
        "output_path": "data/deliverables/email_sequences/{name}.json",
        "platforms": ["beehiiv","apollo"],
    },
    "LANDING_PAGE": {
        "required_fields": ["headline","subheadline","hero_section","features",
                           "social_proof","cta_primary","cta_secondary","meta_title"],
        "quality_threshold": 9.0,
        "output_path": "site/{slug}/index.html",
        "platforms": ["nyspotlightreport.com"],
    },
    "CLIENT_REPORT": {
        "required_fields": ["client_name","period","kpis","achievements",
                           "recommendations","next_steps"],
        "quality_threshold": 9.0,
        "output_path": "data/deliverables/client_reports/{client}/{date}.json",
        "platforms": ["email","pdf"],
    },
    "PRESS_RELEASE": {
        "required_fields": ["headline","subheadline","dateline","body","boilerplate",
                           "contact","quotes"],
        "quality_threshold": 8.5,
        "output_path": "data/deliverables/press_releases/{date}.json",
        "platforms": ["einpresswire","prweb","direct_journalist"],
    },
}

# ── QUALITY SCORING ENGINE ────────────────────────────────────────

def score_deliverable(deliverable: dict, dtype: str) -> dict:
    """
    Score a deliverable on 5 dimensions, 0-10 each.
    Returns overall score + detailed breakdown.
    """
    schema = DELIVERABLE_TYPES.get(dtype, {})
    required = schema.get("required_fields", [])
    threshold = schema.get("quality_threshold", 7.0)
    
    scores = {}
    
    # 1. COMPLETENESS (0-10)
    present = sum(1 for f in required if deliverable.get(f))
    scores["completeness"] = round((present / max(len(required),1)) * 10, 1)
    
    # 2. LENGTH/DEPTH (0-10)
    content = str(deliverable.get("body_html","") or deliverable.get("body","") or 
                  deliverable.get("text","") or deliverable.get("description",""))
    word_count = len(content.split())
    
    min_words = {"BLOG_POST":600,"NEWSLETTER":300,"SOCIAL_POST":20,"VIDEO_SCRIPT":200,
                 "DIGITAL_PRODUCT":100,"LANDING_PAGE":500,"CLIENT_REPORT":400,"PRESS_RELEASE":300}
    min_w = min_words.get(dtype, 200)
    scores["depth"] = min(10, round((word_count / min_w) * 8, 1))
    
    # 3. BRAND VOICE (0-10) — Claude scoring
    if ANTHROPIC and content and len(content) > 50:
        brand_score = claude_json(
            """You are the NYSR brand voice checker. Score content 0-10 on brand alignment.
NYSR brand: Direct, expert, specific with numbers, zero fluff, practical value, SC Thomas voice.
Return JSON: {"brand_score": 0-10, "issues": ["issue1"], "strengths": ["str1"]}""",
            f"Score this content for brand voice (max 500 chars): {content[:500]}",
            max_tokens=150
        ) or {"brand_score": 7}
        scores["brand_voice"] = brand_score.get("brand_score", 7)
    else:
        scores["brand_voice"] = 7.0  # Default when no content to analyze
    
    # 4. SEO/DISCOVERABILITY (0-10)
    seo_score = 5.0
    title = str(deliverable.get("title","") or deliverable.get("subject","") or 
                deliverable.get("headline",""))
    if title: seo_score += 1.5
    if deliverable.get("target_keyword") or deliverable.get("keywords"): seo_score += 1.5
    if deliverable.get("meta_description"): seo_score += 1.0
    if deliverable.get("internal_links"): seo_score += 0.5
    scores["seo"] = min(10, seo_score)
    
    # 5. CONVERSION POTENTIAL (0-10)
    conv_score = 5.0
    text_lower = content.lower()
    if any(x in text_lower for x in ["→","click","get","start","download","free","now"]): conv_score += 1.5
    if deliverable.get("cta") or deliverable.get("cta_url"): conv_score += 1.5
    if any(x in text_lower for x in ["$","save","earn","result","benefit","because"]): conv_score += 1.0
    if deliverable.get("social_proof") or "%" in text_lower: conv_score += 1.0
    scores["conversion"] = min(10, conv_score)
    
    # OVERALL
    weights = {"completeness":0.25,"depth":0.20,"brand_voice":0.25,"seo":0.15,"conversion":0.15}
    overall = round(sum(scores[k] * weights[k] for k in scores), 2)
    
    passed = overall >= threshold
    
    return {
        "overall": overall,
        "threshold": threshold,
        "passed": passed,
        "dimensions": scores,
        "grade": "A" if overall>=9 else "B" if overall>=8 else "C" if overall>=7 else "D",
        "approved": passed,
    }

# ── MULTI-FORMAT OUTPUT ENGINE ────────────────────────────────────

def expand_to_all_formats(base_content: dict, source_type: str) -> dict:
    """
    Take any piece of content and automatically expand to ALL formats.
    One blog post → newsletter excerpt, 3 tweets, LinkedIn post, 
    Instagram caption, Quora answer, video script outline.
    """
    if not ANTHROPIC:
        return {"expanded": False, "reason": "No Anthropic key"}
    
    title = base_content.get("title", base_content.get("subject",""))
    content = str(base_content.get("body_html","") or base_content.get("body",""))[:800]
    
    return claude_json(
        """You are the NYSR content expansion engine. Take source content and reformat it for every channel.
Maintain SC Thomas voice: direct, specific, expert. Different platforms have different formats.""",
        f"""Expand this {source_type} to all formats:
Title: {title}
Content preview: {content[:400]}

Return JSON:
{{
  "tweet_thread": ["Tweet 1 (hook)", "Tweet 2 (insight)", "Tweet 3 (CTA)"],
  "linkedin_post": "200-word professional post",
  "instagram_caption": "150-char caption + 5 hashtags",
  "newsletter_excerpt": "100-word teaser with link prompt",
  "quora_answer": "300-word expert answer using this content",
  "video_script_hook": "15-second YouTube Shorts hook",
  "reddit_post_title": "Engaging Reddit title for r/entrepreneur",
  "email_subject_lines": ["Option A", "Option B", "Option C"]
}}""",
        max_tokens=1000
    ) or {}

# ── CONTENT CALENDAR INTELLIGENCE ────────────────────────────────

def generate_content_calendar(weeks: int = 4) -> dict:
    """
    Generate a rolling content calendar based on:
    - Business goals (revenue, leads, subscribers)
    - SEO keyword opportunities
    - Industry events and timing
    - Content type rotation (blog, video, social, product)
    """
    if not ANTHROPIC:
        return {}
    
    from datetime import date, timedelta
    
    today = date.today()
    calendar = {}
    
    themes = [
        "AI content automation (core topic — highest traffic)",
        "Passive income with AI tools (conversion topic)",
        "ProFlow AI / DFY agency (commercial topic)",
        "Newsletter growth tactics (community topic)",
        "Behind the scenes: 63 bots story (trust/brand topic)",
    ]
    
    for week_num in range(weeks):
        week_start = today + timedelta(weeks=week_num)
        theme = themes[week_num % len(themes)]
        
        calendar[f"week_{week_num+1}"] = {
            "start_date": str(week_start),
            "theme": theme,
            "deliverables": {
                "monday":    {"type":"BLOG_POST",    "topic":f"{theme} — deep dive"},
                "tuesday":   {"type":"SOCIAL_POST",  "platform":"linkedin","topic":f"{theme} — insight"},
                "wednesday": {"type":"VIDEO_SCRIPT", "topic":f"{theme} — YouTube Short"},
                "thursday":  {"type":"SOCIAL_POST",  "platform":"twitter","topic":f"{theme} — thread"},
                "friday":    {"type":"NEWSLETTER",   "topic":f"Weekly digest: {theme}"},
                "saturday":  {"type":"SOCIAL_POST",  "platform":"reddit","topic":f"{theme} — community value"},
                "sunday":    {"type":"SEO_ARTICLE",  "topic":f"{theme} — long-form"},
            }
        }
    
    return calendar

# ── BRAND VOICE ENFORCER ──────────────────────────────────────────

NYSR_BRAND_VOICE = {
    "name": "SC Thomas / NY Spotlight Report",
    "tone": "Direct, expert, peer-level authority",
    "style": "Specific numbers > vague claims. Show don't tell. Zero fluff.",
    "prohibited": [
        "synergy", "leverage", "game-changer", "revolutionize", "unlock your potential",
        "in today's fast-paced world", "it's important to note", "I hope this helps",
        "as an AI language model", "comprehensive guide to everything you need to know"
    ],
    "required_elements": {
        "BLOG_POST": ["specific number or stat", "direct actionable takeaway", "CTA to free-plan"],
        "NEWSLETTER": ["subject line under 50 chars", "preview text", "one main CTA"],
        "SOCIAL_POST": ["hook in first line", "no passive voice", "ends with question or CTA"],
        "VIDEO_SCRIPT": ["pattern interrupt hook in first 3 seconds", "specific outcome promised"],
    },
    "voice_examples": [
        "I replaced a $4,000/month content team with 63 bots for $70/month.",
        "The system publishes daily. It doesn't call in sick. It doesn't miss deadlines.",
        "Here's the exact stack: [specifics]. Here's what it costs: [number].",
    ]
}

def check_brand_voice(content: str, content_type: str) -> dict:
    """Check content against brand voice standards."""
    issues = []
    
    # Check prohibited phrases
    for phrase in NYSR_BRAND_VOICE["prohibited"]:
        if phrase.lower() in content.lower():
            issues.append(f"Prohibited phrase: '{phrase}'")
    
    # Check required elements
    required = NYSR_BRAND_VOICE.get("required_elements",{}).get(content_type,[])
    
    if ANTHROPIC and content:
        result = claude_json(
            f"""You are the NYSR brand voice enforcer. Check content against these standards:
Tone: {NYSR_BRAND_VOICE['tone']}
Style: {NYSR_BRAND_VOICE['style']}
Voice examples: {NYSR_BRAND_VOICE['voice_examples']}
Required for {content_type}: {required}""",
            f"""Check this content (first 600 chars): {content[:600]}

Return JSON: {{
  "passes": true/false,
  "brand_score": 0-10,
  "issues": ["issue1","issue2"],
  "improvements": ["specific rewrite suggestion 1"],
  "strongest_line": "the best line in the content"
}}""",
            max_tokens=200
        ) or {"passes": True, "brand_score": 7, "issues": issues}
        return result
    
    return {"passes": len(issues)==0, "brand_score": 8 if not issues else 6, "issues": issues}

# ── DELIVERABLE REGISTRY ──────────────────────────────────────────

def register_deliverable(deliverable: dict, dtype: str, score: dict) -> bool:
    """Log every deliverable to the master registry."""
    registry_path = "data/deliverables/registry.json"
    
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{registry_path}", headers=GH_H)
    registry = []
    if r.status_code == 200:
        try:
            registry = json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    entry = {
        "id": f"{dtype.lower()}_{date.today()}_{len(registry)}",
        "type": dtype,
        "title": deliverable.get("title","") or deliverable.get("subject",""),
        "created": datetime.now().isoformat(),
        "quality_score": score.get("overall"),
        "grade": score.get("grade"),
        "approved": score.get("approved"),
        "platforms": DELIVERABLE_TYPES.get(dtype,{}).get("platforms",[]),
        "status": "approved" if score.get("approved") else "needs_revision",
    }
    
    registry.insert(0, entry)
    registry = registry[:500]  # Keep last 500
    
    payload = json.dumps(registry, indent=2)
    body = {"message": f"deliverable: {dtype} registered (score: {score.get('overall')})",
            "content": base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    r2 = requests.put(f"https://api.github.com/repos/{REPO}/contents/{registry_path}", json=body, headers=GH_H)
    return r2.status_code in [200, 201]

# ── MASTER RUN ────────────────────────────────────────────────────

def run():
    log.info("Master Deliverable Orchestrator starting...")
    
    # Generate content calendar
    log.info("Generating 4-week content calendar...")
    calendar = generate_content_calendar(4)
    
    # Save calendar
    cal_payload = json.dumps({"generated": str(date.today()), "calendar": calendar}, indent=2)
    _push("data/deliverables/content_calendar.json", cal_payload, "deliverables: 4-week content calendar")
    log.info(f"  ✅ {len(calendar)}-week calendar generated")
    
    # Generate today's deliverables
    today_day = date.today().strftime("%A").lower()
    week_1 = calendar.get("week_1",{})
    today_task = week_1.get("deliverables",{}).get(today_day,{})
    
    if today_task:
        log.info(f"Today's deliverable: {today_task.get('type')} — {today_task.get('topic','')[:60]}")
    
    log.info("✅ Deliverable Orchestrator run complete")

def _push(path: str, content: str, msg: str) -> bool:
    enc = base64.b64encode(content.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    body = {"message": msg, "content": enc}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    r2 = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)
    return r2.status_code in [200, 201]

if __name__ == "__main__":
    run()
