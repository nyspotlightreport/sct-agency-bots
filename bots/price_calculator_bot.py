#!/usr/bin/env python3
"""Price Calculator & ROI Bot — Interactive pricing and ROI for every scenario.
Generates custom pricing proposals and ROI breakdowns for prospects."""
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

def calculate_custom_roi(
    team_size: int = 3,
    avg_hourly: float = 75,
    articles_per_week: int = 5,
    current_tool_cost: float = 0,
    product: str = "proflow_growth"
) -> dict:
    PRODUCT_DATA = {
        "proflow_starter":  {"price": 97,  "articles_mo": 50,  "automations": 3},
        "proflow_growth":   {"price": 297, "articles_mo": 200, "automations": 8},
        "proflow_agency":   {"price": 497, "articles_mo": 9999,"automations": 25},
        "lead_gen_starter": {"price": 297, "leads_mo": 50,     "sequences": 3},
        "lead_gen_growth":  {"price": 497, "leads_mo": 200,    "sequences": 10},
    }
    pd = PRODUCT_DATA.get(product, PRODUCT_DATA["proflow_growth"])
    price = pd["price"]
    articles = pd.get("articles_mo",0)

    # Current state (manual)
    articles_per_mo_manual = articles_per_week * 4
    hours_per_article      = 3.5  # industry average
    manual_time_per_mo     = articles_per_mo_manual * hours_per_article
    manual_cost_per_mo     = manual_time_per_mo * avg_hourly

    # With NYSR
    nysr_time_per_mo    = articles * 0.25  # 15 min review per AI article
    nysr_labor_cost     = nysr_time_per_mo * avg_hourly
    nysr_total_cost     = price + nysr_labor_cost
    nysr_output         = articles

    # Delta
    time_saved          = manual_time_per_mo - nysr_time_per_mo
    cost_saved          = manual_cost_per_mo - nysr_total_cost
    output_increase_pct = round((nysr_output / max(articles_per_mo_manual,1) - 1) * 100)
    monthly_roi         = cost_saved
    roi_pct             = round(cost_saved / max(price,1) * 100)

    return {
        "product":              product,
        "monthly_price":        price,
        "team_size":            team_size,
        "manual_monthly_cost":  round(manual_cost_per_mo),
        "nysr_monthly_cost":    round(nysr_total_cost),
        "monthly_savings":      round(cost_saved),
        "time_saved_hours":     round(time_saved),
        "output_increase_pct":  output_increase_pct,
        "roi_percentage":       roi_pct,
        "annual_savings":       round(cost_saved * 12),
        "payback_period_days":  round(price / max(cost_saved/30,1)) if cost_saved > 0 else 999,
    }

def generate_roi_report(contact: dict, product: str = "proflow_growth") -> str:
    company   = contact.get("company","Your Company")
    team_size = contact.get("employees",5) or 5
    roi       = calculate_custom_roi(team_size=min(team_size,20), product=product)

    return f"""
ROI ANALYSIS FOR {company.upper()}
{'='*45}
Current manual content cost: ${roi['manual_monthly_cost']:,}/mo
NYSR {product} investment:   ${roi['monthly_price']:,}/mo

MONTHLY SAVINGS:    ${roi['monthly_savings']:,}
ANNUAL SAVINGS:     ${roi['annual_savings']:,}
OUTPUT INCREASE:    {roi['output_increase_pct']}% more content
TIME RECLAIMED:     {roi['time_saved_hours']} hours/month
ROI PERCENTAGE:     {roi['roi_percentage']}%
PAYBACK PERIOD:     {roi['payback_period_days']} days

Bottom line: For every $1 invested in NYSR, {company} gets ${round(1+roi['roi_percentage']/100,1):.1f} back.
{'='*45}
"""

def run():
    for product in ["proflow_starter","proflow_growth","proflow_agency"]:
        roi = calculate_custom_roi(team_size=5, product=product)
        log.info(f"{product}: ${roi['monthly_price']}/mo → ${roi['monthly_savings']:,} savings → {roi['roi_percentage']}% ROI")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
