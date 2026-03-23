#!/usr/bin/env python3
# Sales Enablement Agent - Training materials, playbooks, coaching, onboarding new reps.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

PLAYBOOK_SECTIONS = [
    "Ideal Customer Profile",
    "Value Proposition by ICP",
    "Discovery Call Framework",
    "Demo Best Practices",
    "Objection Handling Library",
    "Competitor Battle Cards",
    "Proposal Templates",
    "Closing Techniques",
    "Follow-up Cadences",
    "Win/Loss Analysis Process",
]

def generate_playbook_section(section, product="ProFlow"):
    return claude(
        f"Write the {section} section of a B2B SaaS sales playbook. Specific, actionable, concise. 200 words.",
        f"Product: {product}. Section: {section}",
        max_tokens=400
    ) or f"# {section}\n\nTODO: Populate this section with {product}-specific content."

def generate_full_playbook(product="ProFlow"):
    playbook = {"product":product,"sections":{},"generated_at":__import__("datetime").datetime.utcnow().isoformat()}
    for section in PLAYBOOK_SECTIONS[:3]:
        playbook["sections"][section] = generate_playbook_section(section, product)
    return playbook

def create_coaching_card(rep_name, deal, weakness):
    return claude(
        "Write a 3-point coaching card for a sales rep. Specific, kind, actionable.",
        f"Rep: {rep_name}. Deal: {json.dumps(deal)[:200]}. Weakness to address: {weakness}",
        max_tokens=200
    ) or f"Coaching for {rep_name}: 1. {weakness} - practice this. 2. Review playbook section. 3. Role play with manager."

def generate_training_quiz(topic):
    return claude_json(
        "Generate a 5-question multiple choice quiz for sales training. Return JSON: {questions:[{q,options:[],answer}]}",
        f"Topic: {topic}. Context: B2B SaaS sales for AI automation product.",
        max_tokens=600
    ) or {"questions":[{"q":f"What is the best opener for a cold email about {topic}?","options":["A","B","C","D"],"answer":"A"}]}

def run():
    playbook = generate_full_playbook("ProFlow")
    log.info(f"Generated playbook: {len(playbook['sections'])} sections")
    quiz = generate_training_quiz("objection handling")
    log.info(f"Training quiz: {len(quiz.get('questions',{}))} questions")
    return playbook

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()