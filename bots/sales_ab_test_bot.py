#!/usr/bin/env python3
"""
Sales A/B Test Bot — Systematic testing of subject lines, CTAs, and angles.
Tracks which variants perform best and auto-updates the winning copy.
"""
import os, sys, json, logging, random
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude_json
    from agents.crm_core_agent import supabase_request
except:
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

TEST_ELEMENTS = {
    "subject_lines": [
        "Quick question, {first_name}",
        "Your {company} + AI = ?",
        "Saw your work at {company}",
        "How {company} could 10x content output",
        "Re: {company} growth",
        "{first_name} — honest question",
    ],
    "openers": [
        "I came across {company} while researching {industry} companies and had to reach out.",
        "Your {title} role caught my attention because most {industry} teams are leaving serious money on the table.",
        "Quick question for the {title} at {company}:",
    ],
    "ctas": [
        "Worth a 15-min call this week?",
        "Want to see how it works?",
        "Could we grab 15 minutes?",
        "Open to a quick demo?",
    ],
}

def generate_ab_variants(element_type: str, context: dict = None) -> list:
    variants = TEST_ELEMENTS.get(element_type, [])
    if context:
        processed = []
        for v in variants:
            try:
                processed.append(v.format(
                    first_name=context.get("first_name","there"),
                    company=context.get("company","your company"),
                    title=context.get("title","your role"),
                    industry=context.get("industry","your industry"),
                ))
            except: processed.append(v)
        return processed
    return variants

def pick_winning_variant(element_type: str, context: dict = None) -> str:
    """Pick the statistically best variant, or random if no data yet."""
    variants = generate_ab_variants(element_type, context)
    if not variants: return ""
    results = supabase_request("GET","ab_test_results",
        query=f"?element_type=eq.{element_type}&order=open_rate.desc&limit=1"
    )
    if results and isinstance(results, list) and results[0].get("winning_variant"):
        winning_idx = results[0].get("winning_variant_index",0)
        if winning_idx < len(variants): return variants[winning_idx]
    return random.choice(variants)

def record_result(element_type: str, variant_index: int, opened: bool, replied: bool):
    supabase_request("POST","ab_test_results",{
        "element_type":     element_type,
        "variant_index":    variant_index,
        "opened":           opened,
        "replied":          replied,
        "recorded_at":      datetime.utcnow().isoformat(),
    })

def run():
    log.info("A/B Test Bot: generating test variants...")
    test_context = {"first_name":"Alex","company":"ContentCo","title":"CEO","industry":"marketing"}
    for el_type in TEST_ELEMENTS:
        variants = generate_ab_variants(el_type, test_context)
        winner = pick_winning_variant(el_type, test_context)
        log.info(f"  {el_type}: {len(variants)} variants | Winner: {winner[:60]}")
    return {"status": "running", "elements_tracked": len(TEST_ELEMENTS)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [ABTest] %(message)s")
    run()
