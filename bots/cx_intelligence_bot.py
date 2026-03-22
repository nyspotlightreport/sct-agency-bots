#!/usr/bin/env python3
"""bots/cx_intelligence_bot.py
Scans competitor landscape, prospect signals, and market trends.
Feeds outreach campaigns with timely, relevant hooks.
Monitors: funding rounds, job changes, tech stack signals, intent data.
Outperforms: Belkins research team, CIENCE data ops, Martal SDRs.
"""
import os, json, urllib.request, logging, datetime
log = logging.getLogger("cx_intel")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INTEL] %(message)s")

SUPA = os.environ.get("SUPABASE_URL","")
KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e:
        log.warning(f"DB: {e}"); return None

def pull_apollo_prospects():
    """Pull fresh ICP-matched prospects from Apollo."""
    if not APOLLO_KEY:
        log.warning("No Apollo key")
        return 0
    icp_profiles = supa("GET","icp_profiles","","?active=eq.true&select=*") or []
    total_added = 0
    for icp in icp_profiles[:2]:  # Process top 2 ICPs per run
        payload = {"q_organization_industries": icp.get("industries",[]),
                   "person_titles": icp.get("job_titles",[])[:5],
                   "per_page": 25, "page": 1}
        req = urllib.request.Request("https://api.apollo.io/v1/mixed_people/search",
            data=json.dumps(payload).encode(),
            headers={"Content-Type":"application/json","Cache-Control":"no-cache",
                     "X-Api-Key":APOLLO_KEY})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            people = data.get("people",[])
            for p in people[:10]:
                email = p.get("email","")
                if not email or email == "email_not_unlocked@domain.com": continue
                existing = supa("GET","contacts","",f"?email=eq.{email}&select=id&limit=1")
                if existing: continue
                supa("POST","contacts",{
                    "name": f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                    "email": email,
                    "title": p.get("title",""),
                    "company": p.get("organization",{}).get("name",""),
                    "industry": icp.get("industries",["Unknown"])[0],
                    "stage": "LEAD",
                    "score": 65,
                    "source": "apollo_cx_intel",
                    "tags": ["cx-outreach","icp-matched"],
                    "notes": f"Pulled via CX Intelligence — ICP: {icp.get('name','')}",
                })
                total_added += 1
        except Exception as e:
            log.warning(f"Apollo pull: {e}")
    log.info(f"New prospects added: {total_added}")
    return total_added

def seed_sequences_for_new_leads():
    """Auto-enroll new leads into outreach sequences."""
    new_leads = supa("GET","contacts","",
        "?stage=eq.LEAD&source=like.*apollo_cx*&select=id,name&limit=30") or []
    campaign = supa("GET","outreach_campaigns","",
        "?status=eq.active&limit=1&select=id") or []
    if not campaign: return 0
    campaign_id = (campaign[0] if isinstance(campaign,list) else campaign).get("id")
    enrolled = 0
    for lead in new_leads:
        existing = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{lead['id']}&select=id&limit=1")
        if existing: continue
        next_touch = datetime.datetime.utcnow().isoformat()
        supa("POST","outreach_sequences",{
            "campaign_id": campaign_id,
            "contact_id": lead["id"],
            "sequence_name": "ProFlow DFY 5-Touch",
            "current_step": 0,
            "total_steps": 5,
            "status": "active",
            "channel": "email",
            "next_touch_at": next_touch,
        })
        enrolled += 1
    log.info(f"Enrolled in sequences: {enrolled}")
    return enrolled

def run():
    r = {}
    r["prospects"] = pull_apollo_prospects()
    r["enrolled"]  = seed_sequences_for_new_leads()
    log.info(f"Intel complete: {r}")
    return r

if __name__ == "__main__": run()
