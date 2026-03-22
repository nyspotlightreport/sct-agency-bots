#!/usr/bin/env python3
"""
Revenue Operations Agent (RevOps)
The connective tissue between Sales, Marketing, and Finance.
Owns: revenue data integrity, forecasting accuracy, process optimization,
tech stack management, quota planning, and compensation.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, get_pipeline_stats
    from agents.sales_analytics_agent import calculate_cac_ltv, calculate_conversion_rates
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
    def get_pipeline_stats(): return {}
    def calculate_cac_ltv(): return {}
    def calculate_conversion_rates(x): return {}

log = logging.getLogger(__name__)

COMP_PLAN = {
    "base_commission_rate": 0.20,        # 20% of first month
    "recurring_commission":  0.05,        # 5% of MRR for 12 months
    "accelerator_threshold": 1.25,        # 25% above quota
    "accelerator_rate":      0.30,        # 30% above threshold
    "dfy_commission":        0.10,        # 10% of one-time DFY projects
    "spiff_new_logos":       50,          # $50 bonus per new customer
}

QUOTA_PLAN = {
    "monthly_new_mrr":       2000,
    "monthly_one_time":      5000,
    "monthly_new_customers": 5,
    "quarter_multiplier":    3.2,
}

def calculate_commission(deals: List[Dict]) -> Dict:
    """Calculate commissions for a period."""
    base_comm     = 0
    recurring_comm = 0
    spiffs         = 0
    new_logos      = 0

    for deal in deals:
        if deal.get("stage") == "CLOSED_WON":
            value    = deal.get("value",0)
            recurring= deal.get("recurring",False)
            if recurring:
                base_comm      += value * COMP_PLAN["base_commission_rate"]
                recurring_comm += value * COMP_PLAN["recurring_commission"] * 12
            else:
                base_comm += value * COMP_PLAN["dfy_commission"]
            new_logos += 1
            spiffs    += COMP_PLAN["spiff_new_logos"]

    total = base_comm + recurring_comm + spiffs
    return {
        "base_commission":      round(base_comm, 2),
        "recurring_commission": round(recurring_comm, 2),
        "spiffs":               spiffs,
        "new_logos":            new_logos,
        "total_commission":     round(total, 2),
    }

def audit_data_quality() -> Dict:
    """Check CRM data quality — missing emails, scores, stages."""
    contacts = supabase_request("GET","contacts",query="?select=id,email,score,stage,name&limit=100") or []
    issues   = {
        "missing_email":  len([c for c in contacts if not c.get("email")]),
        "zero_score":     len([c for c in contacts if c.get("score",0) == 0]),
        "stuck_in_lead":  len([c for c in contacts if c.get("stage") == "LEAD"]),
        "total_checked":  len(contacts),
    }
    quality_score = max(0, 100 - issues["missing_email"]*5 - issues["zero_score"]*2)
    return {**issues, "quality_score": quality_score}

def generate_ops_report() -> Dict:
    stats      = get_pipeline_stats()
    conv_rates = calculate_conversion_rates(stats)
    cac_ltv    = calculate_cac_ltv()
    data_qual  = audit_data_quality()

    # Identify top bottleneck
    min_conv   = min([(v,k) for k,v in conv_rates.items() if "→" in k] or [(100,"none")])
    bottleneck = min_conv[1] if min_conv[0] < 50 else "None — pipeline flowing well"

    report = {
        "date": datetime.utcnow().isoformat(),
        "pipeline_health": stats,
        "conversion_rates": conv_rates,
        "unit_economics": cac_ltv,
        "data_quality": data_qual,
        "bottleneck": bottleneck,
        "recommendations": [],
    }

    # Auto-generate recommendations
    recs = []
    if cac_ltv.get("ltv_cac_ratio",0) < 3:
        recs.append("LTV:CAC below 3:1 — reduce CAC or increase average deal size")
    if data_qual.get("quality_score",100) < 70:
        recs.append(f"Data quality at {data_qual.get('quality_score')}% — run contact enrichment")
    if conv_rates.get("LEAD→PROSPECT",0) < 20:
        recs.append("Low lead→prospect conversion — review ICP targeting")
    if conv_rates.get("PROPOSAL→NEGOTIATION",0) < 50:
        recs.append("Proposals not converting — review pricing/value proposition")
    report["recommendations"] = recs

    return report

def run():
    report = generate_ops_report()
    log.info(f"RevOps Report: {json.dumps(report, indent=2)[:1000]}")
    return report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
