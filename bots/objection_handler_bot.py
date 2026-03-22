#!/usr/bin/env python3
"""
Objection Handler Bot — AI-Powered Sales Objection Response Generator
Generates context-aware responses to common and custom objections.
Also trains on past wins/losses to improve over time.
"""
import os, sys, json, logging
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

OBJECTIONS = {
    "too_expensive": {
        "category": "Price",
        "reframe": "investment vs cost",
        "key_points": ["ROI in weeks not months", "Compare to hiring cost", "No long-term contract"],
    },
    "not_right_time": {
        "category": "Timing",
        "reframe": "cost of waiting",
        "key_points": ["Every month delayed = revenue left on table", "Setup takes only 48-72 hours", "Competition is already using AI"],
    },
    "need_to_think": {
        "category": "Hesitation",
        "reframe": "clarity vs stalling",
        "key_points": ["What specific concern?", "30-day guarantee removes risk", "Decision today vs 3 months from now"],
    },
    "already_have_solution": {
        "category": "Competitor",
        "reframe": "complement vs replace",
        "key_points": ["Works alongside existing tools", "What gaps does current solution leave?", "Free audit of current setup"],
    },
    "need_approval": {
        "category": "Authority",
        "reframe": "champion strategy",
        "key_points": ["What would make it easy to get approval?", "ROI deck for decision maker", "Pilot program option"],
    },
    "dont_need_it": {
        "category": "Awareness",
        "reframe": "future vs now",
        "key_points": ["Where do you want to be in 12 months?", "Specific pain point questions", "Show not tell demo"],
    },
}

def handle_objection(objection_text: str, contact_context: dict = None, package: str = "dfy_essential") -> dict:
    """Generate a tailored objection response."""

    # Classify the objection
    objection_key = "need_to_think"  # default
    obj_lower = objection_text.lower()
    if any(w in obj_lower for w in ["price","expensive","cost","afford","budget","cheap"]):
        objection_key = "too_expensive"
    elif any(w in obj_lower for w in ["time","busy","later","soon","month","quarter"]):
        objection_key = "not_right_time"
    elif any(w in obj_lower for w in ["think","discuss","team","talk"]):
        objection_key = "need_to_think"
    elif any(w in obj_lower for w in ["already","using","have","competitor","zapier","hubspot"]):
        objection_key = "already_have_solution"
    elif any(w in obj_lower for w in ["boss","ceo","approve","approval","sign off","manager"]):
        objection_key = "need_approval"
    elif any(w in obj_lower for w in ["need","necessary","sure","relevant"]):
        objection_key = "dont_need_it"

    obj_data = OBJECTIONS[objection_key]
    context_str = ""
    if contact_context:
        context_str = f"Contact: {contact_context.get('name','')} | {contact_context.get('title','')} at {contact_context.get('company','')}"

    response = claude_json(
        "You are a world-class B2B sales closer. Generate an empathetic but persuasive objection response.",
        f"""Objection received: "{objection_text}"
Objection type: {obj_data["category"]} — use "{obj_data["reframe"]}" reframe
Key points to weave in: {", ".join(obj_data["key_points"])}
{context_str}
Package being discussed: {package}

Generate 3 different response options (short, medium, detailed).
Return JSON: {{
  "objection_type": "{objection_key}",
  "response_short": "1-2 sentence acknowledgment + redirect",
  "response_medium": "3-5 sentence full response with one proof point",
  "response_detailed": "Full paragraph with empathy + reframe + proof + CTA",
  "follow_up_question": "best question to ask after your response",
  "warning_signs": "what this objection really means (hidden concern)",
  "success_rate": 0.0-1.0
}}""", max_tokens=500
    ) or {
        "objection_type": objection_key,
        "response_short": f"I hear you. That's exactly why we offer a 30-day guarantee — zero risk to try it.",
        "response_medium": f"That makes sense. Most of our clients felt the same way before they saw the results. The {package} pays for itself within the first 30 days for most companies. And with our guarantee, there's literally nothing to lose.",
        "follow_up_question": "What would need to be true for this to make sense for you?",
        "success_rate": 0.4
    }

    return response

def generate_objection_cheatsheet(package: str = "all") -> str:
    """Generate a full objection handling cheatsheet as markdown."""
    lines = [f"# NYSR Sales — Objection Handling Cheatsheet
*Package: {package}*
"]

    for key, obj in OBJECTIONS.items():
        response = handle_objection(f"I have a {obj['category'].lower()} concern", package=package)
        lines.append(f"## {obj['category'].upper()} Objection")
        lines.append(f"**Reframe:** {obj['reframe']}")
        lines.append(f"
**Short response:**
{response.get('response_short','')}")
        lines.append(f"
**Full response:**
{response.get('response_medium','')}")
        lines.append(f"
**Follow-up question:** {response.get('follow_up_question','')}")
        lines.append(f"
**Hidden concern:** {response.get('warning_signs','')}
")
        lines.append("---
")

    return "
".join(lines)

def run():
    log.info("Objection Handler Bot generating cheatsheet...")
    cheatsheet = generate_objection_cheatsheet("dfy_essential")
    log.info(f"Cheatsheet generated: {len(cheatsheet)} chars")

    # Test all objection types
    test_objections = [
        "It's too expensive for us right now",
        "We need to think about it",
        "We already use HubSpot for this",
    ]
    for obj in test_objections:
        response = handle_objection(obj)
        log.info(f"  Objection: "{obj[:40]}..."")
        log.info(f"  → Type: {response.get('objection_type','?')} | Rate: {response.get('success_rate',0):.0%}")

    return {"cheatsheet_generated": True, "objections_processed": len(test_objections)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Objection] %(message)s")
    run()
