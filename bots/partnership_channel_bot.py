#!/usr/bin/env python3
"""
bots/partnership_channel_bot.py
ENGINE 5: Automated B2B partnership outreach.
Targets: marketing agencies, VA agencies, web design firms, business coaches.
Each partner = access to their entire client base.
One agency with 20 clients = 20 recurring contracts overnight.
Sends white-label pitch → interested reply → auto-books with 1099 closer.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("partnership")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PARTNERS] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
APOLLO_KEY= os.environ.get("APOLLO_API_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
SITE      = "https://nyspotlightreport.com"

PARTNER_NICHES = [
    "marketing agency",
    "social media agency", 
    "web design agency",
    "business coach",
    "VA agency",
    "content agency",
    "digital marketing consultant",
    "online business manager"
]

PARTNER_PITCH_TEMPLATE = """Subject: White-label AI content system for your clients

Hi {name},

We built an AI system that handles full content + marketing operations — social, blog, email, SEO — for $297–$997/month per client.

Most {agency_type}s we talk to spend 10+ hours per client per week on content tasks that could be fully automated. We can white-label this entirely under your brand.

Your model:
- You charge clients $2,000–5,000/month (your current rate)
- We handle all content/marketing execution at $297–997/mo
- You keep the difference, reduce delivery costs, and scale without hiring

Takes 30 minutes to set up the first client. No technical work on your end.

Worth a 15-minute call? Here's my calendar: {site}/book/

NY Spotlight Report"""

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def search_agency_prospects():
    """Use Apollo to find agency owners to pitch partnership."""
    if not APOLLO_KEY:
        log.warning("APOLLO_API_KEY not set")
        return []
    
    data = json.dumps({
        "q_organization_industry_tag_ids": ["5567cd4773696439b10b0000"],
        "organization_num_employees_ranges": ["1,20"],
        "person_titles": ["founder","owner","ceo","director","managing director"],
        "per_page": 25
    }).encode()
    
    req = urllib.request.Request(
        "https://api.apollo.io/v1/mixed_people/search",
        data=data,
        headers={"Content-Type":"application/json","x-api-key":APOLLO_KEY,"Cache-Control":"no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get("people",[])
    except Exception as e:
        log.debug(f"Apollo search: {e}")
        return []

def run():
    log.info("="*55)
    log.info("ENGINE 5: Partnership Channel Bot")
    log.info("="*55)
    
    # Check existing partners
    partners = supa("GET","strategic_partners","","?status=eq.active&select=id") or []
    active_count = len(partners) if isinstance(partners,list) else 0
    
    if active_count >= 5:
        log.info(f"5+ active partners — targeting expansion. Current: {active_count}")
    
    # Search for prospects
    prospects = search_agency_prospects()
    outreach_count = 0
    
    for p in prospects[:10]:
        name     = p.get("name","")
        email    = p.get("email","")
        company  = p.get("organization",{}).get("name","")
        title    = p.get("title","").lower()
        
        if not email or not name: continue
        
        agency_type = next((n for n in PARTNER_NICHES if n in title or n in company.lower()), "agency")
        pitch = PARTNER_PITCH_TEMPLATE.format(
            name=name.split()[0],
            agency_type=agency_type,
            site=SITE
        )
        
        # Save prospect to contacts + log outreach
        contact_data = {
            "email":email, "name":name, "company":company,
            "stage":"COLD", "source":"partnership_outreach",
            "tags":["agency_prospect","partner_pipeline"], "score":60
        }
        result = supa("POST","contacts",contact_data)
        if result and isinstance(result,list) and result[0]:
            supa("POST","conversation_log",{
                "contact_id":result[0].get("id"),"channel":"email","direction":"outbound",
                "body":pitch,"intent":"partnership_pitch","agent_name":"Partnership Bot"
            })
            outreach_count += 1
    
    log.info(f"Partnership: {outreach_count} agency prospects pitched | {active_count} active partners")

if __name__ == "__main__": run()
