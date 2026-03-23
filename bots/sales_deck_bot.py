#!/usr/bin/env python3
# Sales Deck Bot - Generates custom sales presentations for each prospect.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

DECK_SLIDES = [
    "Title Slide",
    "The Problem (personalized to prospect)",
    "The Cost of Inaction",
    "Our Solution",
    "How It Works (3-step)",
    "Results / Case Studies",
    "ROI Calculator",
    "Pricing",
    "Implementation Timeline",
    "Next Steps",
]

def generate_slide_content(slide_name, contact, product="ProFlow Growth"):
    company = contact.get("company","Your Company")
    return claude(
        f"Write slide content for: {slide_name}. 3 bullet points max. Specific and compelling.",
        f"Slide: {slide_name}. Company: {company}. Product: {product}. Pain: content production.",
        max_tokens=150
    ) or f"{slide_name}:\n• Key point 1\n• Key point 2\n• Key point 3"

def generate_deck(contact, product="proflow_growth"):
    company = contact.get("company","Your Company")
    deck = {
        "title": f"AI Automation for {company}",
        "prospect": contact,
        "product": product,
        "slides": {},
    }
    for slide in DECK_SLIDES[:5]:
        deck["slides"][slide] = generate_slide_content(slide, contact, product)
    return deck

def run():
    contact = {"name":"Alex Chen","company":"ContentCo","title":"CEO","icp":"proflow_ai"}
    deck = generate_deck(contact)
    log.info(f"Generated deck: {deck['title']} - {len(deck['slides'])} slides")
    return deck

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
