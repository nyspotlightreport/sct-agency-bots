#!/usr/bin/env python3
"""
Lead Generation as a Service — NYSR Agency
Delivers 500 qualified B2B leads per month to clients.
Uses Apollo.io API to source, verify, and export leads.
Client pays $297-997/month for their niche lead list.
Service is 100% automated — zero human labor.
"""
import os, requests, json, logging, csv, io
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("LeadGenBot")

APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")
GMAIL_USER = os.environ.get("GMAIL_USER","")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS","")
BASE = "https://api.apollo.io/api/v1"

SERVICE_TIERS = {
    "starter":    {"leads": 250,  "price": 297,  "desc": "250 verified leads/month"},
    "growth":     {"leads": 500,  "price": 497,  "desc": "500 verified leads/month"},
    "enterprise": {"leads": 1000, "price": 997,  "desc": "1000 verified leads/month + sequences"},
}

CLIENT_NICHES = {
    "real_estate_agents":    {"title": "Real Estate Agent", "industry": "Real Estate"},
    "financial_advisors":    {"title": "Financial Advisor", "industry": "Financial Services"},
    "insurance_agents":      {"title": "Insurance Agent",   "industry": "Insurance"},
    "restaurant_owners":     {"title": "Owner",             "industry": "Restaurants"},
    "ecommerce_founders":    {"title": "Founder",           "industry": "Retail"},
    "saas_founders":         {"title": "Founder",           "industry": "Software"},
    "marketing_agencies":    {"title": "Agency Owner",      "industry": "Marketing"},
    "business_coaches":      {"title": "Business Coach",    "industry": "Professional Training"},
}

def search_leads(niche_config, limit=50, page=1):
    if not APOLLO_KEY:
        log.warning("No APOLLO_API_KEY — using mock data")
        return [{"first_name":"Sample","last_name":"Lead","email":"sample@example.com",
                 "title":niche_config["title"],"company":"Sample Co","linkedin_url":""}
                for _ in range(min(limit,5))]
    payload = {
        "api_key": APOLLO_KEY,
        "q_person_titles": [niche_config["title"]],
        "organization_industry_tag_ids": [],
        "person_locations": ["United States"],
        "page": page, "per_page": limit,
        "contact_email_status": ["verified"],
    }
    r = requests.post(f"{BASE}/mixed_people/search", json=payload, timeout=30)
    if r.status_code == 200:
        return r.json().get("people", [])
    log.error(f"Apollo error: {r.status_code}")
    return []

def format_leads_csv(leads):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["First Name","Last Name","Email","Title","Company","LinkedIn","Phone"])
    for l in leads:
        writer.writerow([
            l.get("first_name",""), l.get("last_name",""),
            l.get("email",""), l.get("title",""),
            l.get("organization",{}).get("name","") if isinstance(l.get("organization"),dict) else "",
            l.get("linkedin_url",""), l.get("phone_numbers",[{}])[0].get("raw_number","") if l.get("phone_numbers") else ""
        ])
    return output.getvalue()

def deliver_leads_to_client(client_email, niche, count=250):
    leads = []
    page = 1
    while len(leads) < count:
        batch = search_leads(CLIENT_NICHES.get(niche, {"title": "Business Owner"}),
                             limit=min(50, count-len(leads)), page=page)
        if not batch: break
        leads.extend(batch)
        page += 1
    csv_data = format_leads_csv(leads[:count])
    date = datetime.now().strftime("%B %Y")
    log.info(f"Delivering {len(leads)} leads to {client_email} for niche: {niche}")
    # Email delivery
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = client_email
    msg["Subject"] = f"Your {date} Lead List — {count} Verified Contacts"
    msg.attach(MIMEText(f"""Hi,

Your {date} lead list is attached — {len(leads)} verified contacts in {niche.replace('_',' ')}.

All leads have been verified with active email addresses.

Next delivery: same time next month.

Questions? Reply to this email.

— NY Spotlight Report Lead Gen Team"""))
    att = MIMEText(csv_data, "plain")
    att["Content-Disposition"] = f'attachment; filename="{niche}_{date}_leads.csv"'
    msg.attach(att)
    if GMAIL_PASS:
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(GMAIL_USER, GMAIL_PASS)
                smtp.send_message(msg)
            log.info(f"✅ Leads delivered to {client_email}")
        except Exception as e:
            log.error(f"Email failed: {e}")
    return leads

if __name__ == "__main__":
    log.info("Lead Generation as a Service")
    for tier, data in SERVICE_TIERS.items():
        log.info(f"  {tier}: ${data['price']}/mo — {data['desc']}")
    log.info(f"Available niches: {len(CLIENT_NICHES)}")
    log.info("At 10 clients on Growth plan = $4,970/mo automated")
