#!/usr/bin/env python3
# Discount Engine Bot - Smart discounting with guardrails, approval workflows, ROI tracking.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

DISCOUNT_RULES = {
    "annual_upfront":   {"pct":0.17,"condition":"pays annual","auto_approve":True},
    "multi_year":       {"pct":0.25,"condition":"2+ years","auto_approve":True},
    "competitive":      {"pct":0.15,"condition":"documented competitor","auto_approve":True},
    "nonprofit":        {"pct":0.30,"condition":"501c3 verified","auto_approve":False},
    "startup":          {"pct":0.20,"condition":"less than 1yr old, <10 employees","auto_approve":True},
    "referral_credit":  {"pct":0.10,"condition":"came via referral","auto_approve":True},
    "trial_convert":    {"pct":0.25,"condition":"first-time buyer","auto_approve":True},
    "winback":          {"pct":0.20,"condition":"returning customer","auto_approve":True},
}

def calculate_discount(base_price, discount_type, verify_condition=True):
    rule = DISCOUNT_RULES.get(discount_type)
    if not rule: return {"error":f"Unknown discount type: {discount_type}"}
    discounted = base_price * (1 - rule["pct"])
    return {
        "original_price": base_price,
        "discount_type": discount_type,
        "discount_pct": f"{rule['pct']*100:.0f}%",
        "discounted_price": round(discounted,2),
        "savings": round(base_price - discounted,2),
        "auto_approve": rule["auto_approve"],
        "condition": rule["condition"],
    }

def apply_best_discount(contact, base_price):
    scores = {
        "annual_upfront": 5,
        "trial_convert": contact.get("source","") != "trial" and 0 or 8,
        "referral_credit": contact.get("source","") == "referral" and 10 or 0,
        "startup": contact.get("employees",100) < 10 and 7 or 0,
        "competitive": bool(contact.get("competitor")) and 6 or 0,
    }
    best = max(scores, key=scores.get)
    return calculate_discount(base_price, best)

def run():
    for dtype, rule in list(DISCOUNT_RULES.items())[:5]:
        result = calculate_discount(297, dtype)
        log.info(f"{dtype}: ${result['original_price']} -> ${result['discounted_price']} ({result['discount_pct']})")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
