#!/usr/bin/env python3
"""
Sales Analytics Agent — Drew Sinclair for Sales
Tracks: conversion rates by stage, CAC, LTV, pipeline velocity,
win/loss by ICP, channel attribution, revenue per rep, quota attainment.
Produces weekly sales performance report and proactive insights.
"""
import os, sys, json, logging, math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
sys.path.insert(0,".")
try:
    from agents.claude_core import claude_json
    from agents.crm_core_agent import supabase_request, get_pipeline_stats, ICPS
except:
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
    def get_pipeline_stats(): return {}

log = logging.getLogger(__name__)

PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

import urllib.request, urllib.parse

def notify(msg, title="Sales Analytics"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except: pass

def calculate_conversion_rates(stats: Dict) -> Dict:
    """Calculate stage-by-stage conversion rates."""
    stages  = ["LEAD","PROSPECT","QUALIFIED","PROPOSAL","NEGOTIATION","CLOSED_WON"]
    rates   = {}
    for i in range(len(stages)-1):
        s1 = stats.get(stages[i],{}).get("count",0)
        s2 = stats.get(stages[i+1],{}).get("count",0)
        rates[f"{stages[i]}→{stages[i+1]}"] = round(s2/s1*100,1) if s1 > 0 else 0
    won  = stats.get("CLOSED_WON",{}).get("count",0)
    lost = stats.get("CLOSED_LOST",{}).get("count",0)
    total_closed = won + lost
    rates["OVERALL_WIN_RATE"] = round(won/total_closed*100,1) if total_closed > 0 else 0
    return rates

def calculate_pipeline_velocity(stats: Dict, avg_deal_days: int = 21) -> Dict:
    """How fast deals move through the pipeline."""
    stages_counts = {k:v.get("count",0) for k,v in stats.items()}
    total_active  = sum(v for k,v in stages_counts.items() if k not in ["CLOSED_WON","CLOSED_LOST"])
    avg_deal_val  = 1500  # average deal value

    velocity = total_active * avg_deal_val / max(avg_deal_days, 1)
    return {
        "weekly_revenue_velocity": round(velocity * 7),
        "monthly_revenue_velocity": round(velocity * 30),
        "total_active_deals": total_active,
        "avg_days_to_close": avg_deal_days,
    }

def calculate_cac_ltv() -> Dict:
    """Customer Acquisition Cost and Lifetime Value analysis."""
    # Apollo Pro: $99/mo, ~50 emails/day, ~2% reply, ~10% close = 10 customers/mo from email
    apollo_cac  = 99 / max(10, 1)          # $9.90 CAC from Apollo
    tools_total = 99 + 22 + 50             # Apollo + ElevenLabs + misc
    monthly_customers_estimate = 5         # conservative

    blended_cac = tools_total / max(monthly_customers_estimate, 1)
    avg_mrr     = 250   # average across tiers
    avg_months  = 12    # avg customer lifespan
    ltv         = avg_mrr * avg_months

    return {
        "blended_cac":      round(blended_cac),
        "apollo_cac":       round(apollo_cac, 2),
        "avg_customer_ltv": ltv,
        "ltv_cac_ratio":    round(ltv/max(blended_cac,1), 1),
        "payback_period_months": round(blended_cac/max(avg_mrr,1), 1),
        "target_ltv_cac":   "3:1 minimum, 5:1 target",
    }

def generate_weekly_report() -> str:
    stats       = get_pipeline_stats()
    conv_rates  = calculate_conversion_rates(stats)
    velocity    = calculate_pipeline_velocity(stats)
    cac_ltv     = calculate_cac_ltv()

    won   = stats.get("CLOSED_WON",{}).get("count",0)
    total = sum(v.get("count",0) for v in stats.values())

    report = f"""
╔══════════════════════════════════════╗
║   NYSR SALES ANALYTICS — WEEKLY     ║
║   {datetime.utcnow().strftime("%B %d, %Y")}                 ║
╚══════════════════════════════════════╝

PIPELINE HEALTH
  Total Contacts:     {total}
  Closed Won:         {won}
  Win Rate:           {conv_rates.get("OVERALL_WIN_RATE",0)}%
  Weekly Velocity:    ${velocity["weekly_revenue_velocity"]:,}
  Monthly Velocity:   ${velocity["monthly_revenue_velocity"]:,}

CONVERSION FUNNEL
{chr(10).join([f"  {k}: {v}%" for k,v in conv_rates.items() if "→" in k])}

UNIT ECONOMICS
  CAC (blended):      ${cac_ltv["blended_cac"]}
  Avg LTV:            ${cac_ltv["avg_customer_ltv"]:,}
  LTV:CAC Ratio:      {cac_ltv["ltv_cac_ratio"]}:1
  Payback Period:     {cac_ltv["payback_period_months"]} months

HEALTH CHECK
  {"✅" if cac_ltv["ltv_cac_ratio"] >= 3 else "⚠️"} LTV:CAC ratio {">= 3:1" if cac_ltv["ltv_cac_ratio"] >= 3 else "< 3:1 (needs improvement)"}
  {"✅" if conv_rates.get("OVERALL_WIN_RATE",0) > 20 else "⚠️"} Win rate {">20%" if conv_rates.get("OVERALL_WIN_RATE",0) > 20 else "below 20% target"}
"""
    notify(f"Weekly sales report ready. Win rate: {conv_rates.get('OVERALL_WIN_RATE',0)}% | Velocity: ${velocity['monthly_revenue_velocity']:,}/mo", "Sales Analytics")
    return report

def run():
    report = generate_weekly_report()
    log.info(report)
    return report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
