#!/usr/bin/env python3
# Data Enrichment Bot - Enriches contacts with missing data from Apollo and web.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")
import urllib.request

def enrich_from_apollo(email):
    if not APOLLO_KEY: return {}
    try:
        import json
        payload = json.dumps({"email":email,"reveal_personal_emails":False}).encode()
        req = urllib.request.Request(
            "https://api.apollo.io/api/v1/people/match",
            data=payload,
            headers={"Content-Type":"application/json","X-Api-Key":APOLLO_KEY}
        )
        with urllib.request.urlopen(req,timeout=10) as r:
            data = json.loads(r.read())
            person = data.get("person",{})
            return {
                "title": person.get("title",""),
                "linkedin_url": person.get("linkedin_url",""),
                "company": person.get("organization",{}).get("name",""),
                "employees": person.get("organization",{}).get("num_employees",0),
                "industry": person.get("organization",{}).get("industry",""),
                "website": person.get("organization",{}).get("website_url",""),
            }
    except Exception as e:
        log.warning(f"Apollo enrich failed: {e}")
        return {}

def enrich_contacts(limit=20):
    contacts = supabase_request("GET","contacts",query=f"?title=is.null&email=not.is.null&limit={limit}") or []
    enriched = 0
    for c in contacts:
        email = c.get("email","")
        if not email: continue
        data = enrich_from_apollo(email)
        if data:
            supabase_request("PATCH","contacts",data=data,query=f"?id=eq.{c.get('id','')}")
            enriched += 1
    log.info(f"Enriched {enriched}/{len(contacts)} contacts")
    return enriched

def run():
    return enrich_contacts(20)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
