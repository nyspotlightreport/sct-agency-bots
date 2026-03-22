#!/usr/bin/env python3
"""
agents/opportunity_discovery.py — NYSR Opportunity Discovery (Larridin Concept)
Finds high-value prospects daily using market signals, intent data, and
competitive intelligence. Feeds directly into Sloane Pierce's sales pipeline.
"""
import os, sys, json, logging, base64
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.supercore import SuperDirector, pushover, supa
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def pushover(*a,**k): pass
    def supa(*a,**k): return None

log = logging.getLogger("opportunity")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [OPPORTUNITY] %(message)s")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")
GH_PAT = os.environ.get("GH_PAT","")
REPO = "nyspotlightreport/sct-agency-bots"
import urllib.request as urlreq, urllib.parse

def apollo_search(title_keywords, industry=None, limit=25):
    if not APOLLO_KEY: return []
    params = {"api_key":APOLLO_KEY,"per_page":min(limit,25),
        "person_titles[]":title_keywords,"contact_email_status[]":["verified"]}
    if industry: params["organization_industry_tag_ids[]"] = [industry]
    try:
        data = json.dumps(params).encode()
        req = urlreq.Request("https://api.apollo.io/api/v1/mixed_people/search",
            data=data, headers={"Content-Type":"application/json","X-Api-Key":APOLLO_KEY})
        with urlreq.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            return result.get("people",[])
    except Exception as e:
        log.warning(f"Apollo search: {e}"); return []

def score_opportunity(prospect):
    score = 50
    title = (prospect.get("title") or "").lower()
    company_size = prospect.get("organization",{}).get("estimated_num_employees",0) or 0
    if any(k in title for k in ["ceo","founder","owner","president"]): score += 25
    elif any(k in title for k in ["director","vp","head"]): score += 15
    elif any(k in title for k in ["manager"]): score += 10
    if 1 <= company_size <= 50: score += 15
    elif 50 < company_size <= 200: score += 10
    if prospect.get("email"): score += 10
    return min(score, 100)

def generate_outreach(prospect, offer):
    name = prospect.get("first_name","there")
    company = prospect.get("organization",{}).get("name","your company")
    title = prospect.get("title","")
    return claude(
        "You are Sloane Pierce, Sales Director. Write a 4-sentence cold email. First line = specific hook about THEM. No fluff. End with soft CTA.",
        f"Prospect: {name}, {title} at {company}\nOffer: {offer['name']} — {offer['price']} — {offer['hook']}\nWrite the email. Subject line first.",
        max_tokens=300) or f"Subject: Quick question, {name}\n\nHi {name},\n\nI noticed {company} is growing its content presence. We built an AI system that automates 90% of content production — blog, social, newsletter, video — for {offer['price']}.\n\n{offer['cta']}\n\nBest,\nSean Thomas\nNY Spotlight Report"

OFFERS = {
    "proflow_ai": {"name":"ProFlow AI","price":"$97/mo","hook":"cuts content production by 80%","cta":"Want a 15-min demo?"},
    "dfy_agency": {"name":"DFY Agency Automation","price":"$4,997","hook":"automates entire agency ops","cta":"Open to a 30-min call this week?"},
}

def run(limit=20):
    log.info("="*50)
    log.info("OPPORTUNITY DISCOVERY — Finding high-value prospects")
    log.info("="*50)
    targets = [
        ("Marketing Agency Owner", None),
        ("Digital Marketing Director", None),
        ("Content Marketing Manager", None),
        ("Agency Founder", None),
    ]
    all_prospects = []
    for title_kw, industry in targets:
        people = apollo_search(title_kw, industry, limit=limit//len(targets))
        for p in people:
            p["opportunity_score"] = score_opportunity(p)
        all_prospects.extend(people)
        log.info(f"  {title_kw}: {len(people)} found")
    all_prospects.sort(key=lambda x: x.get("opportunity_score",0), reverse=True)
    top = all_prospects[:limit]
    log.info(f"\nTop {len(top)} opportunities (scored):")
    outreach_ready = []
    for p in top[:10]:
        offer = OFFERS["dfy_agency"] if p.get("opportunity_score",0) >= 80 else OFFERS["proflow_ai"]
        email_draft = generate_outreach(p, offer)
        outreach_ready.append({
            "name": p.get("name",""),
            "email": p.get("email",""),
            "title": p.get("title",""),
            "company": p.get("organization",{}).get("name",""),
            "score": p.get("opportunity_score",0),
            "offer": offer["name"],
            "draft": email_draft,
        })
        log.info(f"  [{p.get('opportunity_score',0)}] {p.get('name','')} — {p.get('title','')} @ {p.get('organization',{}).get('name','')}")
    # Save to Supabase
    for o in outreach_ready:
        supa("POST","contacts",{"name":o["name"],"email":o["email"],"title":o["title"],
            "company":o["company"],"score":o["score"],"stage":"LEAD","source":"opportunity_discovery",
            "created_at":datetime.utcnow().isoformat()})
    supa("POST","director_outputs",{"director":"Opportunity Discovery","output_type":"daily_prospects",
        "content":json.dumps(outreach_ready[:5],indent=2)[:2000],
        "metrics":json.dumps({"total_found":len(all_prospects),"top_scored":len(top),"outreach_ready":len(outreach_ready)}),
        "created_at":datetime.utcnow().isoformat()})
    pushover("Opportunity Discovery",
        f"Found {len(all_prospects)} prospects, {len(outreach_ready)} outreach-ready\nTop: {outreach_ready[0]['name'] if outreach_ready else 'none'} ({outreach_ready[0]['score'] if outreach_ready else 0})")
    log.info(f"\nDiscovery complete: {len(all_prospects)} found, {len(outreach_ready)} outreach-ready")
    return {"total":len(all_prospects),"outreach_ready":outreach_ready}

if __name__=="__main__":
    run()
