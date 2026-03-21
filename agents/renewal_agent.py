#!/usr/bin/env python3
# Renewal Agent - Subscription renewals, price increases, multi-year deals.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

RENEWAL_PLAYBOOK = {
    "90_days_before": "Start renewal conversation. Review usage and ROI.",
    "60_days_before": "Send renewal proposal. Offer multi-year discount.",
    "30_days_before": "Follow up. Address any concerns.",
    "7_days_before":  "Final reminder. Escalate to ensure continuity.",
    "renewal_day":    "Confirm auto-renewal or collect new payment.",
}

MULTIYEAR_DISCOUNTS = {
    "annual":     0.17,
    "2_year":     0.25,
    "3_year":     0.33,
}

def get_upcoming_renewals(days_ahead=90):
    from_date = datetime.utcnow().isoformat()
    to_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
    return supabase_request("GET","deals",
        query=f"?stage=eq.CLOSED_WON&expected_close=gte.{from_date[:10]}&expected_close=lte.{to_date[:10]}&limit=50") or []

def generate_renewal_email(customer, days_until_renewal, current_price):
    name = (customer.get("name","") or "").split()[0] or "there"
    company = customer.get("company","")
    annual_price = current_price * 10
    multi_year_price = current_price * 9
    return {
        "subject": f"Your NYSR renewal is coming up - {company}",
        "body": claude(
            "Write a renewal email. Thank for loyalty. Show usage stats. Offer upgrade or multi-year discount. Under 120 words.",
            f"Customer {name} at {company}. {days_until_renewal} days until renewal. Current: ${current_price}/mo. Annual saves ${current_price*2}. 2yr saves ${current_price*4}.",
            max_tokens=200
        ) or f"Hi {name}, your NYSR subscription renews in {days_until_renewal} days. Thanks for your continued trust! Lock in annual billing and save ${current_price*2} vs monthly. Want to lock it in? S.C."
    }

def run():
    renewals = get_upcoming_renewals(90)
    log.info(f"Upcoming renewals (90d): {len(renewals)}")
    return renewals

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()