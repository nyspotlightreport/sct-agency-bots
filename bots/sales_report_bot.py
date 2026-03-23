#!/usr/bin/env python3
# Sales Report Bot - Weekly/monthly sales reports sent to Chairman via Pushover.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import get_pipeline_stats, supabase_request
    from agents.sales_analytics_agent import calculate_cac_ltv, calculate_conversion_rates
except Exception:  # noqa: bare-except
    def get_pipeline_stats(): return {}
    def supabase_request(m,t,**k): return None
    def calculate_cac_ltv(): return {}
    def calculate_conversion_rates(x): return {}
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg,title="Sales Report"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except Exception:  # noqa: bare-except

        pass
def generate_weekly_report():
    stats = get_pipeline_stats()
    conv  = calculate_conversion_rates(stats)
    econ  = calculate_cac_ltv()
    total = sum(v.get("count",0) for v in stats.values())
    won   = stats.get("CLOSED_WON",{}).get("count",0)
    report = f"WEEKLY SALES - {datetime.utcnow().strftime('%b %d')}\n"
    report += f"Pipeline: {total} contacts\n"
    report += f"Won: {won} | Win rate: {conv.get('OVERALL_WIN_RATE',0)}%\n"
    report += f"LTV:CAC: {econ.get('ltv_cac_ratio',0)}:1\n"
    for stage,data in stats.items():
        if data.get("count",0) > 0:
            report += f"{stage}: {data['count']}\n"
    notify(report,"Weekly Sales")
    return report

def run():
    report = generate_weekly_report()
    log.info(report)
    return report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
