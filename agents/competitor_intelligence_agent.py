#!/usr/bin/env python3
"""
Competitor Intelligence Agent — Battle Cards & Competitive Positioning
Tracks competitors, generates battle cards, and arms sales with winning arguments.
Runs weekly to update intelligence and alert on competitive threats.
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

# Master competitive intelligence database
COMPETITORS = {
    "jasper": {
        "name": "Jasper AI",
        "website": "jasper.ai",
        "pricing": "$49-$125/mo",
        "strengths": ["Brand awareness","Large template library","Team features","Chrome extension"],
        "weaknesses": ["No automation","No lead gen","No scheduling","Just writing tool, not system","Expensive for output"],
        "target_customer": "Content teams, marketers",
        "our_angle": "Jasper gives you a faster typewriter. We give you an autonomous content factory.",
        "win_rate": 0.70,
        "threat_level": "MEDIUM",
    },
    "copy_ai": {
        "name": "Copy.ai",
        "website": "copy.ai",
        "pricing": "$49/mo",
        "strengths": ["Low price","Easy to use","Good short-form copy"],
        "weaknesses": ["No publishing","No SEO","No scheduling","No lead gen","Basic output quality"],
        "our_angle": "Copy.ai writes the words. We publish, rank, and generate leads from them.",
        "win_rate": 0.80,
        "threat_level": "LOW",
    },
    "hubspot": {
        "name": "HubSpot",
        "website": "hubspot.com",
        "pricing": "$800-$3,600/mo",
        "strengths": ["Enterprise brand","Full CRM","Marketing hub","Large ecosystem"],
        "weaknesses": ["Extremely expensive","Not AI-native","Requires team to operate","Complex setup","No content automation"],
        "our_angle": "HubSpot is a $3k/mo tool that still needs a $5k/mo marketing team to run it. We're the team AND the tool.",
        "win_rate": 0.85,
        "threat_level": "LOW",
        "note": "Most clients can't afford HubSpot — we win this comparison easily on price",
    },
    "surfer_seo": {
        "name": "Surfer SEO",
        "website": "surferseo.com",
        "pricing": "$89-$249/mo",
        "strengths": ["Strong SEO features","Good content scoring","Popular in SEO community"],
        "weaknesses": ["Just SEO writing, not publishing","No lead gen","No automation","No social"],
        "our_angle": "Surfer optimizes one article at a time. We publish 200 optimized articles a month automatically.",
        "win_rate": 0.75,
        "threat_level": "MEDIUM",
    },
    "zapier": {
        "name": "Zapier",
        "website": "zapier.com",
        "pricing": "$29-$599/mo",
        "strengths": ["Massive integrations","Brand recognition","No-code"],
        "weaknesses": ["Not AI","You still have to build everything","No content","No lead gen","Expensive at scale"],
        "our_angle": "Zapier connects tools. We replace them. Our bots don't need connecting — they work out of the box.",
        "win_rate": 0.78,
        "threat_level": "MEDIUM",
    },
    "dfy_freelancer": {
        "name": "Freelance Agency / Developer",
        "website": "upwork.com",
        "pricing": "$50-$200/hr, $5k-$50k projects",
        "strengths": ["Custom work","Human creativity","Flexibility"],
        "weaknesses": ["Slow","Expensive","One project at a time","No ongoing automation","No 24/7"],
        "our_angle": "A freelancer builds it once. We build it, run it, improve it, 24/7, for 1/10th the cost.",
        "win_rate": 0.82,
        "threat_level": "HIGH",
        "note": "Most common real competitor — people considering hiring vs buying",
    },
}

BATTLE_CARD_TEMPLATE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BATTLE CARD: NYSR vs {name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When they say: "We're looking at {name}"
You say: "{our_angle}"

THEIR STRENGTHS (acknowledge these):
{strengths}

WHERE WE WIN:
{weaknesses_as_wins}

THE CLOSE:
"Most companies who go with {name} come back to us within 6 months 
because {top_weakness}. What if we did a side-by-side comparison 
so you can see the difference before committing?"

PRICING COMPARISON:
{name}: {pricing}
NYSR:   Starts at $97/mo

WIN RATE vs {name}: {win_rate}% in our favor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def generate_battle_card(competitor_key: str) -> str:
    comp = COMPETITORS.get(competitor_key)
    if not comp: return f"No data for competitor: {competitor_key}"
    strengths_str = "
".join([f"  ✓ {s}" for s in comp["strengths"]])
    wins_str = "
".join([f"  🏆 {w}" for w in comp["weaknesses"]])
    return BATTLE_CARD_TEMPLATE.format(
        name=comp["name"],
        our_angle=comp["our_angle"],
        strengths=strengths_str,
        weaknesses_as_wins=wins_str,
        top_weakness=comp["weaknesses"][0].lower() if comp["weaknesses"] else "limitations",
        pricing=comp["pricing"],
        win_rate=int(comp.get("win_rate",0.75)*100),
    )

def handle_competitive_objection(competitor_key: str, contact: Dict = None) -> str:
    comp = COMPETITORS.get(competitor_key, list(COMPETITORS.values())[0])
    return claude(
        "You are an elite sales rep. Handle this competitive objection with confidence and specificity. 2-3 sentences.",
        f"Prospect is considering {comp['name']}. Our angle: {comp['our_angle']}. Their weaknesses: {comp['weaknesses'][:2]}",
        max_tokens=150
    ) or f"Great choice to evaluate {comp['name']}. {comp['our_angle']} Would it help to do a quick side-by-side comparison?"

def run():
    log.info("Competitor Intelligence — generating all battle cards")
    for key, comp in COMPETITORS.items():
        card = generate_battle_card(key)
        log.info(f"
{card}")
    return {comp: generate_battle_card(key) for key, comp in [(k,v["name"]) for k,v in COMPETITORS.items()]}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
