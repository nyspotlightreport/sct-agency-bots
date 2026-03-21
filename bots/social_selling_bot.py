#!/usr/bin/env python3
"""Social Selling Bot — LinkedIn + Twitter/X DM outreach with personalized research.
Finds buying signals, engages content, sends warm DMs."""
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

BUYING_SIGNALS = [
    "posted about hiring content team",
    "liked/commented on competitor content",
    "job posting for marketing role",
    "announced funding round",
    "company growth announcement",
    "complained about content bottleneck",
    "asked for tool recommendations",
    "followed NYSR account",
]

def generate_linkedin_dm(contact: dict, trigger: str = "") -> str:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","your company")
    title   = contact.get("title","")
    trigger_context = f"Trigger: {trigger}" if trigger else ""

    return claude(
        """Write a LinkedIn DM. Under 60 words. Personal, genuine, conversational.
Reference something specific. End with a low-friction question. No selling yet.""",
        f"To: {name}, {title} at {company}. {trigger_context}",
        max_tokens=100
    ) or f"Hi {name}, saw your post about {company}'s growth — congrats! I work with a few {contact.get('industry','')} companies on AI content automation. Would love to share what's working. Open to a quick chat?"

def generate_twitter_dm(contact: dict) -> str:
    name    = (contact.get("name","") or "").split()[0] or "there"
    company = contact.get("company","")
    return claude(
        "Write a Twitter/X DM. Under 40 words. Casual, direct, interesting. Not salesy.",
        f"To: {name} at {company}",
        max_tokens=70
    ) or f"Hey {name} — love what you're building at {company}. Working on something that might be relevant — got 10 min for a quick DM chat?"

def generate_comment_strategy(post: str, contact: dict) -> str:
    """Generate a value-adding comment to warm up a prospect."""
    name = (contact.get("name","") or "").split()[0]
    return claude(
        "Write a LinkedIn comment. Adds genuine value. Positions expertise. Under 50 words. Not promotional.",
        f"Post content: {post[:300]}
Commenter persona: AI automation expert building AI agency systems",
        max_tokens=80
    ) or "Great perspective on this. The companies seeing the most traction right now are combining this with AI automation — the compounding effect is significant."

def run():
    contacts = [
        {"name":"Alex Chen","company":"ContentCo","title":"CEO","industry":"marketing"},
        {"name":"Sarah Kim","company":"Agency NYC","title":"Founder","industry":"digital agency"},
    ]
    for c in contacts:
        dm = generate_linkedin_dm(c, "posted job for content manager")
        log.info(f"LinkedIn DM for {c['name']}: {dm[:80]}...")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
