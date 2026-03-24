#!/usr/bin/env python3
# Prompt Engineer Agent - System prompts, chain-of-thought, few-shot, prompt optimization.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

PROMPT_LIBRARY = {
    "sales_email":    "You are an elite sales copywriter for {company}. Write a {type} email that is personalized, value-first, and ends with a single clear CTA. Under {words} words. No fluff.",
    "content_brief":  "You are a senior SEO content strategist. Create a comprehensive brief for an article about {topic}. Include: target keyword, secondary keywords, outline (H2s only), word count, and tone.",
    "seo_article":    "You are an expert SEO writer. Write a {word_count}-word article about {topic}. Target keyword: {keyword}. Include: engaging intro, H2/H3 structure, examples, FAQ section, CTA. Optimize for featured snippets.",
    "code_review":    "You are a senior engineer doing a code review. Be specific, constructive, and educational. Identify: bugs, security issues, performance problems, style issues. Suggest improvements with examples.",
    "deal_analysis":  "You are a senior sales strategist. Analyze this deal and provide: probability of close (0-1), biggest risk, recommended next action, message angle. Be specific and tactical.",
    "market_research":"You are a market research analyst. Research {topic} and provide: market size, key players, trends, opportunities, threats, and recommended positioning for a new entrant.",
}

def build_system_prompt(role, goal, constraints=None, output_format=None):
    parts = [f"You are {role}.", f"Your goal is to {goal}."]
    if constraints: parts.append(f"Constraints: {', '.join(constraints)}.")
    if output_format: parts.append(f"Always respond in this format: {output_format}")
    return " ".join(parts)

def optimize_for_task(task_description, current_prompt):
    return claude(
        "Improve this prompt. Apply: clear role, specific output format, examples if beneficial, constraints. Return only the improved prompt, nothing else.",
        f"""Task: {task_description}
Current prompt: {current_prompt}""",
        max_tokens=400
    ) or current_prompt

def test_prompt(prompt, test_inputs):
    results = []
    for inp in test_inputs[:3]:
        output = claude(prompt, inp, max_tokens=200) or "No output"
        results.append({"input":inp[:50],"output":output[:100],"length":len(output)})
    return results

def run():
    for name, template in list(PROMPT_LIBRARY.items())[:3]:
        log.info(f"Prompt '{name}': {len(template)} chars")
    system = build_system_prompt("an elite sales copywriter","write personalized cold emails that get replies",["Under 100 words","No generic openers","End with one yes/no question"],"""Subject: [line]
Body: [email]""")
    log.info(f"Built system prompt: {len(system)} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
