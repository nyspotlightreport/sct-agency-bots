#!/usr/bin/env python3
# Tech Lead Agent - Architecture decisions, stack selection, code standards.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

TECH_STACKS = {
    "saas_webapp":  {"frontend":"Next.js 14+TypeScript+Tailwind","backend":"FastAPI/Python","db":"Supabase PostgreSQL","auth":"Supabase Auth","payments":"Stripe","hosting":"Vercel+Railway","cost":"$0-50/mo"},
    "ai_service":   {"framework":"FastAPI","ai":"Anthropic Claude","queue":"Redis+RQ","hosting":"Railway","cost":"$5-20/mo"},
    "chrome_ext":   {"manifest":"MV3","framework":"React+Webpack","store":"Chrome Web Store","cost":"$5 one-time"},
    "automation":   {"lang":"Python 3.11","schedule":"GitHub Actions","storage":"Supabase free","cost":"$0/mo"},
    "mobile":       {"framework":"React Native+Expo","backend":"shared API","publish":"EAS Build","cost":"$99/yr Apple+$25 Google"},
}

CODE_STANDARDS = ["Single responsibility per function","No function over 50 lines","Error handling on all external calls",
    "All secrets in env vars","Tests for business logic","README with setup","Type hints in Python","TypeScript over JS"]

def select_stack(project_type):
    return TECH_STACKS.get(project_type, TECH_STACKS["saas_webapp"])

def design_architecture(description):
    return claude_json(
        "You are a senior architect. Design system architecture. Return JSON: {pattern,tech_stack,estimated_dev_days,phase_1_mvp,risks,recommended_free_tier_options}",
        f"Project: {description}. Prefer: free tiers, Next.js, FastAPI, Supabase, Vercel.",
        max_tokens=600
    ) or {"pattern":"monolith","estimated_dev_days":7,"phase_1_mvp":"Auth + core feature + payments"}

def run():
    for name, stack in TECH_STACKS.items():
        log.info(f"{name}: {stack['cost']}")
    return TECH_STACKS

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
