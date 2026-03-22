#!/usr/bin/env python3
# Account Manager Agent - Existing account health, QBRs, expansion planning.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

def generate_qbr(customer, metrics):
    company = customer.get("company","")
    return claude(
        "Create a QBR (Quarterly Business Review) outline. 5 sections. Focus on ROI achieved and next quarter goals.",
        f"Company: {company}. Metrics: {json.dumps(metrics)[:400]}",
        max_tokens=500
    ) or f"QBR - {company} Q{(datetime.utcnow().month-1)//3+1}\n1. Results Review\n2. ROI Analysis\n3. Challenges\n4. Next Quarter Plan\n5. Expansion Opportunities"

def identify_expansion_signals(customer):
    signals = []
    if customer.get("usage_pct",0) > 80: signals.append("hitting plan limits")
    if customer.get("team_size",0) > 3: signals.append("team growth")
    if customer.get("months_active",0) >= 3 and not customer.get("upsell_offered"): signals.append("tenure milestone")
    return signals

def build_account_plan(customer):
    return {
        "account": customer.get("company"),
        "current_mrr": customer.get("mrr",0),
        "target_mrr": customer.get("mrr",0) * 2,
        "expansion_signals": identify_expansion_signals(customer),
        "next_qbr": "90 days",
        "health_status": "HEALTHY",
        "action_items": ["Review usage","Offer upgrade","Collect testimonial"],
    }

def run():
    accounts = supabase_request("GET","contacts",query="?stage=eq.CLOSED_WON&limit=50") or []
    log.info(f"Managing {len(accounts)} accounts")
    return [build_account_plan(a) for a in accounts[:5]]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()