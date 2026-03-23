#!/usr/bin/env python3
"""
Content Production Engine — NYSR Social Studio
World-class platform-native content generation.

The philosophy:
- Twitter wants OPINIONS and THREADS. Short, punchy, controversial.
- LinkedIn wants INSIGHTS and LESSONS. Data-backed, professional, ends with question.
- Instagram wants AESTHETIC + HOOKS + SAVES. Visual-first, line breaks, save-worthy.
- Pinterest wants SEARCH-OPTIMIZED educational content. Think like Google.
- TikTok wants TRENDS + ENTERTAINMENT + VALUE. Fast, pattern interrupt, hook.
- YouTube Shorts wants EDUCATION + STORYTELLING. Value in 60 seconds.
- Medium wants DEPTH. Long-form, nuanced, well-structured.

One topic → 10 platform-specific pieces of content.
That's 10x output from one Claude call.
"""
import os, sys, json, logging, time
from datetime import datetime, date
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ContentEngine] %(message)s")
log = logging.getLogger()

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

BRAND = """SC Thomas · NY Spotlight Report · Coram, NY
Voice: Direct authority. Specific numbers. No fluff. Peer-level expert.
Niche: AI automation, passive income, content marketing, entrepreneurship.
Audience: Entrepreneurs 25-45, building online businesses.
Never: "game-changer", "revolutionize", "unlock", "empower", generic advice.
Always: Specific results, real numbers, honest tradeoffs, practical tools."""

CONTENT_PILLARS = {
    "passive_income":     {"emoji":"💰","topics":["bandwidth sharing","digital products","affiliate income","KDP royalties","Gumroad stores"]},
    "ai_automation":      {"emoji":"🤖","topics":["Claude API","GitHub Actions","automated content","AI tools for business","bot building"]},
    "content_marketing":  {"emoji":"📝","topics":["newsletter growth","SEO strategy","blog automation","content calendars","repurposing content"]},
    "cold_outreach":      {"emoji":"🎯","topics":["cold email","Apollo.io","personalization","follow-up sequences","reply rates"]},
    "entrepreneurship":   {"emoji":"🚀","topics":["solopreneur systems","bootstrapping","revenue stacks","client acquisition","pricing strategy"]},
    "digital_products":   {"emoji":"💎","topics":["Gumroad","Etsy digital","templates","guides","Payhip"]},
    "tools_and_stacks":   {"emoji":"🛠️","topics":["Netlify","Beehiiv","GitHub Actions","Apollo","Publer alternatives"]},
}

HASHTAG_BANKS = {
    "passive_income":    "#passiveincome #financialfreedom #makemoneyonline #sidehustle #entrepreneur #digitalproducts #onlinebusiness #incomestreams #wealthbuilding #moneyonline",
    "ai_automation":     "#automation #aitools #artificialintelligence #chatgpt #claude #contentautomation #botbuilding #techentrepreneur #AIbusiness #futureofwork",
    "content_marketing": "#contentmarketing #contentcreation #digitalmarketing #socialmediamarketing #newsletter #blogging #SEO #contentcalendar #marketingstrategy #contentcreator",
    "cold_outreach":     "#coldemail #salesstrategy #B2Bmarketing #leadgeneration #salesautomation #outreach #businessdevelopment #clientacquisition #entrepreneur #sales",
    "entrepreneurship":  "#entrepreneur #startup #solopreneur #businessowner #smallbusiness #hustle #businesstips #entrepreneurship #onlinebusiness #buildingbusiness",
}

def generate_full_content_suite(topic: str, pillar: str = "passive_income") -> dict:
    """Generate complete content suite for all platforms from one topic."""
    
    hashtags = HASHTAG_BANKS.get(pillar, HASHTAG_BANKS["entrepreneurship"])
    date_str = datetime.now().strftime("%B %Y")
    
    if not ANTHROPIC:
        return _fallback_content(topic, hashtags)
    
    prompt = f"""Topic: {topic}
Pillar: {pillar}
Date: {date_str}
Brand: {BRAND}

Generate platform-native content for ALL these platforms.
Each must be optimized for THAT platform's algorithm and culture.

Return JSON with these exact keys:

"twitter_thread": {{
  "hook": "Opening tweet under 280 chars — MUST be controversial, specific, or counterintuitive. No 'Here's a thread on...'",
  "tweets": ["tweet 2 (insight 1)", "tweet 3 (insight 2)", "tweet 4 (insight 3)", "tweet 5 (insight 4)", "tweet 6 (CTA with link)"],
  "best_time": "morning|evening",
  "estimated_reach": "500-2000"
}}

"linkedin_post": {{
  "post": "150-200 word post. Opens with a counterintuitive statement. Uses line breaks. Has specific data. Ends with open question. Includes nyspotlightreport.com",
  "best_time": "Tuesday 8am",
  "estimated_impressions": "2000-8000"
}}

"instagram_caption": {{
  "caption": "3-5 line hook then value then CTA. Line breaks every 1-2 sentences. 20 relevant hashtags at end.",
  "visual_concept": "What should the image/graphic show?",
  "story_concept": "What to post on stories (swipe-up link mention)"
}}

"pinterest_pin": {{
  "title": "SEO-rich title (50-60 chars) — searchable phrase people actually type",
  "description": "200-300 chars — includes keywords naturally, ends with nyspotlightreport.com",
  "board": "Which of our 5 boards this belongs to",
  "best_for_search": ["keyword 1","keyword 2","keyword 3"]
}}

"youtube_short": {{
  "hook": "First 3 seconds script — must stop scroll",
  "script": "Full 45-60 second script. No fluff. Every second earns its keep.",
  "title": "Clickable title with numbers/specificity",
  "description": "YouTube description with keywords + nyspotlightreport.com",
  "tags": ["tag1","tag2","tag3","tag4","tag5"]
}}

"tiktok_script": {{
  "hook": "Pattern interrupt opening — say something unexpected",
  "script": "30-45 second script. Conversational. Fast-paced. Ends with follow CTA.",
  "audio_suggestion": "Trending sound type or original audio recommendation",
  "caption": "Short TikTok caption + hashtags"
}}

"medium_outline": {{
  "title": "Long-form article title",
  "subtitle": "Compelling subtitle",
  "sections": ["H2 section 1","H2 section 2","H2 section 3","H2 section 4"],
  "word_count_target": 1500
}}

"reddit_post": {{
  "subreddit": "r/passive_income or r/entrepreneur etc",
  "title": "Reddit-native title — no marketing language",
  "body_hook": "First paragraph — tells a story or shares something surprising"
}}""",
    
    return claude_json(BRAND, prompt, max_tokens=3000) or _fallback_content(topic, hashtags)

def _fallback_content(topic: str, hashtags: str) -> dict:
    """High-quality fallback content without API."""
    return {
        "twitter_thread": {
            "hook": f"Unpopular opinion: most entrepreneurs should stop trying to {topic} manually and just automate it 🧵",
            "tweets": [
                f"Here's the problem with manual {topic}: it requires consistency. Humans aren't consistent. Systems are.",
                "The 80/20 of automation: Set up the system once. Review monthly. Edit quarterly. That's it.",
                "Most people quit at month 2. That's exactly when compounding starts. The bots don't quit.",
                f"Our system handles {topic} for $2/day in API costs. A human equivalent costs $3k-5k/month.",
                "Full breakdown at nyspotlightreport.com/blog/ — built this over 6 months. Happy to share specifics."
            ],
            "best_time": "morning",
            "estimated_reach": "500-2000"
        },
        "linkedin_post": {
            "post": f"Most entrepreneurs think {topic} is about working harder.

It's not.

It's about building systems that work when you're not.

Here's what 90 days of testing taught us:

→ Manual effort: 20+ hours/week, inconsistent, burns out by month 2
→ AI system: $2/day, posts daily, never misses, compounds over time

The difference isn't talent or hustle.

It's leverage.

We documented the full system at nyspotlightreport.com

What would you automate first if you could?",
            "best_time": "Tuesday 8am",
            "estimated_impressions": "2000-8000"
        },
        "instagram_caption": {
            "caption": f"The {topic} formula nobody teaches you 📌

(Save this before it gets buried)

Step 1: Build the system once
Step 2: Let it run 24/7
Step 3: Optimize monthly, not daily

Most entrepreneurs skip step 1 entirely.

They show up manually every day.

Then burn out.

Then start over.

Don't be that story.

🔗 Free breakdown at nyspotlightreport.com (link in bio)

{hashtags}",
            "visual_concept": "Clean dark background with 3-step framework text overlay, gold accent colors",
            "story_concept": "Poll: 'Do you automate your content?' → Yes/No → swipe up for the system"
        },
        "pinterest_pin": {
            "title": f"How to automate {topic} — complete guide for entrepreneurs",
            "description": f"Step-by-step breakdown of automating {topic} using AI tools. Real results, zero fluff. Build systems that run 24/7 without you. Full guide at nyspotlightreport.com",
            "board": "Content Marketing Automation",
            "best_for_search": [topic, "automation", "entrepreneur tips 2026"]
        },
        "youtube_short": {
            "hook": "I made $80 this month doing literally nothing.",
            "script": f"I made $80 this month doing literally nothing.

Here's exactly how:

I set up 4 apps on a $6-per-month VPS — a tiny cloud server.

Those apps share my unused internet bandwidth.

Honeygain. Traffmonetizer. Pawns. Repocket.

They run 24/7. I haven't touched them since setup.

$80 a month isn't life-changing.

But it's the first income stream.

I have 9 more.

Follow for the full stack.",
            "title": "I earn $80/month doing literally nothing (real setup)",
            "description": f"How I built a {topic} system that runs without me. Full breakdown at nyspotlightreport.com",
            "tags": ["passiveincome","sidehustle","makemoneyonline","automation","entrepreneur"]
        },
        "tiktok_script": {
            "hook": "POV: your business makes money while you sleep",
            "script": f"POV: your business makes money while you sleep.

Not a dream. This is what I actually built.

63 AI bots running my entire content operation.

Every day:
One blog post — written and published
One newsletter — drafted and scheduled  
Six platforms — posted across all of them
Cold emails — 200 personalized per day

What did I do?

Nothing.

The system runs itself.

This is what {topic} actually looks like in 2026.

Follow and I'll show you how to build it.",
            "audio_suggestion": "Trending lo-fi/study beat or original talking head",
            "caption": f"Building a fully automated business in 2026 🤖 #entrepreneur #automation #passiveincome #aitools #sidehustle"
        },
        "medium_outline": {
            "title": f"The Complete Guide to {topic.title()} in 2026: What Actually Works",
            "subtitle": "After 6 months of testing, here's what the data shows",
            "sections": [
                f"Why most approaches to {topic} fail by month 2",
                "The system architecture that actually works (with real numbers)",
                "Step-by-step implementation guide",
                "What you should expect in months 1, 3, and 6",
                "The mistakes I made so you don't have to"
            ],
            "word_count_target": 1800
        },
        "reddit_post": {
            "subreddit": "r/passive_income",
            "title": f"Been running automated {topic} systems for 6 months — here's what the data actually shows",
            "body_hook": f"Six months ago I started building AI systems to automate {topic}. Here's the honest breakdown of what worked, what failed, and what the actual numbers look like — no hype."
        }
    }

def save_content_batch(content: dict, topic: str):
    """Save generated content to repo for scheduling."""
    import base64
    GH_TOKEN = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
    if not GH_TOKEN:
        log.info("No GH_PAT — saving locally")
        with open(f"/tmp/content_{date.today()}.json","w") as f:
            json.dump({"topic":topic,"date":str(date.today()),"content":content}, f, indent=2)
        return
    
    H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    REPO = "nyspotlightreport/sct-agency-bots"
    path = f"data/content_queue/{date.today()}.json"
    
    payload = json.dumps({"topic":topic,"date":str(date.today()),"generated_at":datetime.now().isoformat(),"content":content}, indent=2)
    
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H)
    body = {"message":f"content: generate suite for '{topic}'",
            "content": base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200:
        body["sha"] = r.json()["sha"]
    
    r2 = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=H)
    if r2.status_code in [200,201]:
        log.info(f"✅ Content saved to data/content_queue/{date.today()}.json")
    
import requests

def run():
    log.info("Content Production Engine starting...")
    
    # Pick today's pillar based on day of year
    pillars = list(CONTENT_PILLARS.keys())
    pillar_key = pillars[date.today().timetuple().tm_yday % len(pillars)]
    pillar = CONTENT_PILLARS[pillar_key]
    
    topics = pillar["topics"]
    topic = topics[date.today().timetuple().tm_yday % len(topics)]
    
    log.info(f"Today: [{pillar_key}] → topic: {topic}")
    
    content = generate_full_content_suite(topic, pillar_key)
    
    if content:
        save_content_batch(content, topic)
        
        # Preview
        if "twitter_thread" in content:
            log.info(f"Twitter hook: {str(content['twitter_thread'].get('hook','?'))[:80]}")
        if "linkedin_post" in content:
            log.info(f"LinkedIn: {str(content['linkedin_post'].get('post','?'))[:80]}")
        if "youtube_short" in content:
            log.info(f"YouTube: {str(content['youtube_short'].get('title','?'))[:60]}")
        
        log.info(f"✅ Full content suite generated for: {topic}")
        log.info(f"   Platforms covered: {len(content)} content types")
    else:
        log.error("Content generation failed")

if __name__ == "__main__":
    run()
