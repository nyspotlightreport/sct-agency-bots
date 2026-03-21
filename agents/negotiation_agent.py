#!/usr/bin/env python3
# Negotiation Agent - Deal structuring, concession strategy, closing tactics.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

CONCESSION_LADDER = [
    {"concession":"Free 2-week pilot","cost":"low","use_when":"prospect unsure about fit"},
    {"concession":"First month 50% off","cost":"low","use_when":"price objection, first deal"},
    {"concession":"Free onboarding session","cost":"medium","use_when":"complexity concern"},
    {"concession":"Annual billing at 10-month price","cost":"medium","use_when":"budget tight, want annual"},
    {"concession":"3 months free with annual","cost":"high","use_when":"large deal, strong competitor"},
    {"concession":"Custom payment schedule","cost":"low","use_when":"cash flow concern"},
]

NEGOTIATION_RULES = [
    "Never discount more than 20% without Chairman approval",
    "Trade concessions - never give without getting something",
    "Concede slowly - first offer is never final",
    "Use silence after every concession",
    "Always attach conditions - if-then language",
    "Anchor high first",
    "Create urgency through legitimate scarcity",
]

def recommend_strategy(deal):
    stage = deal.get("stage","PROPOSAL")
    score = deal.get("score",{}).get("total",50)
    value = deal.get("value",0)
    return claude_json(
        "Recommend a negotiation strategy. Return JSON: {strategy, opening_position, walkaway_point, concessions_to_offer, tactics}",
        f"Deal: ${value} | Stage: {stage} | Score: {score} | Competitor: {deal.get('competitor','none')}",
        max_tokens=400
    ) or {"strategy":"anchor_and_concede","opening_position":"full_price","walkaway_point":"15pct_below","concessions_to_offer":["free_pilot","annual_discount"]}

def handle_price_pressure(current_price, max_discount=0.20):
    floor = current_price * (1 - max_discount)
    concessions = [c for c in CONCESSION_LADDER if c["cost"] in ["low","medium"]]
    return {
        "current_price": current_price,
        "floor_price": round(floor),
        "recommended_concessions": concessions[:3],
        "next_step": "Ask: what would make this work for you today?",
    }

def run():
    deal = {"stage":"NEGOTIATION","value":4997,"score":{"total":78},"competitor":"freelancer"}
    strategy = recommend_strategy(deal)
    log.info(f"Negotiation strategy: {strategy.get('strategy','?')}") 
    return strategy

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()