#!/usr/bin/env python3
# Deal Desk Agent - Deal approval, custom pricing, special terms, legal review coordination.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

APPROVAL_THRESHOLDS = {
    "auto_approve":     {"max_discount":0.10, "max_value":4999},
    "manager_approve":  {"max_discount":0.20, "max_value":19999},
    "chairman_approve": {"max_discount":0.35, "max_value":99999},
}

def review_deal(deal):
    value = deal.get("value",0)
    discount = deal.get("discount_pct",0)
    special_terms = deal.get("special_terms",False)
    if discount <= 0.10 and value < 5000 and not special_terms:
        return {"approval":"AUTO","reason":"Within standard parameters"}
    elif discount <= 0.20 and value < 20000:
        return {"approval":"MANAGER","reason":f"Discount {discount*100}% or value ${value:,} requires review"}
    else:
        return {"approval":"CHAIRMAN","reason":f"Large deal or non-standard terms - Chairman approval required"}

def structure_deal(requirements):
    return claude_json(
        "Structure a deal to meet requirements. Return JSON: {product, price, terms, payment_schedule, special_provisions, recommended}",
        f"Requirements: {json.dumps(requirements)[:500]}",
        max_tokens=400
    ) or {"product":"custom","price":requirements.get("budget",2997),"terms":"monthly","recommended":True}

def generate_deal_memo(deal, contact):
    return {
        "memo_date": datetime.utcnow().isoformat(),
        "deal_summary": f"{contact.get('company','?')} - ${deal.get('value',0):,} - {deal.get('product','custom')}",
        "approval_needed": review_deal(deal)["approval"],
        "risk_assessment": "LOW" if deal.get("value",0) < 2000 else "MEDIUM",
        "recommendation": "APPROVE" if deal.get("score",{}).get("total",0) > 60 else "REVIEW",
    }

def run():
    deals = [
        {"value":997,"discount_pct":0.05,"product":"proflow_growth"},
        {"value":9997,"discount_pct":0.15,"product":"enterprise","special_terms":True},
    ]
    for d in deals:
        review = review_deal(d)
        log.info(f"Deal ${d['value']:,}: {review['approval']} - {review['reason']}")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()