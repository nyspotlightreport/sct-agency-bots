#!/usr/bin/env python3
# ML Engineer Agent - AI/ML integrations, prompt engineering, model selection, fine-tuning.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

MODEL_SELECTION = {
    "claude-haiku-4-5":   {"use_case":"Simple classification, routing, short outputs","cost_per_1m_in":0.80,"cost_per_1m_out":4.00,"speed":"fast"},
    "claude-sonnet-4-5":  {"use_case":"Complex reasoning, long-form, code generation","cost_per_1m_in":3.00,"cost_per_1m_out":15.00,"speed":"medium"},
    "claude-opus-4-5":    {"use_case":"Highest capability tasks, enterprise","cost_per_1m_in":15.00,"cost_per_1m_out":75.00,"speed":"slow"},
}

PROMPT_PATTERNS = {
    "chain_of_thought": "Add 'Think step by step' for complex reasoning",
    "few_shot":         "Provide 2-3 examples before the task",
    "role_play":        "You are a [expert role]. Your goal is [goal].",
    "output_format":    "Return ONLY valid JSON: {field: type}",
    "constraint":       "Under N words. No preamble. No explanations.",
    "self_consistency": "Generate 3 approaches, then pick the best",
}

def select_model(task_description, budget_sensitive=True):
    return claude_json(
        "Select the best AI model for this task. Return JSON: {model, reasoning, estimated_tokens_per_call, monthly_cost_estimate}",
        f"Task: {task_description}. Budget sensitive: {budget_sensitive}. Options: {list(MODEL_SELECTION.keys())}",
        max_tokens=200
    ) or {"model":"claude-haiku-4-5","reasoning":"Default to Haiku for cost efficiency","monthly_cost_estimate":5}

def optimize_prompt(raw_prompt, task_type="general"):
    return claude(
        "Optimize this prompt for Claude. Apply best practices: clear role, specific output format, constraints, examples if needed. Return only the improved prompt.",
        f"Raw prompt: {raw_prompt}. Task type: {task_type}",
        max_tokens=500
    ) or raw_prompt

def estimate_cost(calls_per_day, avg_input_tokens=500, avg_output_tokens=300, model="claude-haiku-4-5"):
    m = MODEL_SELECTION.get(model, MODEL_SELECTION["claude-haiku-4-5"])
    daily = calls_per_day * (avg_input_tokens*m["cost_per_1m_in"]/1000000 + avg_output_tokens*m["cost_per_1m_out"]/1000000)
    return {"daily":round(daily,4),"monthly":round(daily*30,2),"model":model}

def run():
    for model, data in MODEL_SELECTION.items():
        cost = estimate_cost(100, model=model)
        log.info(f"{model}: ${cost['monthly']}/mo for 100 calls/day")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
