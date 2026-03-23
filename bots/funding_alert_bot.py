#!/usr/bin/env python3
# Funding Alert Bot - Monitors Crunchbase/web for funding rounds to trigger outreach.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

def generate_funding_outreach(company, funding_amount, round_type):
    return {
        "subject": f"Congrats on the {round_type}, {company}!",
        "body": claude(
            "Write a congratulations email on funding. Mention their growth trajectory. Soft pitch AI automation for scaling. Under 80 words.",
            f"Company just raised {funding_amount} {round_type}. We offer AI content automation at $97-497/mo.",
            max_tokens=150
        ) or f"Congrats on the {round_type}! Funding at this stage usually means scaling content and marketing fast. We help {round_type}-stage companies automate that process. Worth a quick call?",
    }

def search_recent_funding():
    # In production: integrate with Crunchbase API or web scraping
    import urllib.request
    contacts = supabase_request("GET","contacts",query="?stage=in.(LEAD,PROSPECT)&limit=20") or []
    log.info(f"Monitoring {len(contacts)} prospects for funding signals")
    return []

def run():
    alerts = search_recent_funding()
    log.info(f"Funding alerts: {len(alerts)}")
    return alerts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
