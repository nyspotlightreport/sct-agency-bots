#!/usr/bin/env python3
"""
LEAD PIPELINE BOT v2.0 — S.C. Thomas Internal Agency
Apollo → Claude scoring → HubSpot CRM → Email alerts
FIXED: urllib only, correct Apollo v1 endpoint, proper HubSpot push
"""
import os, sys, json, urllib.request, urllib.error, urllib.parse
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY","")
APOLLO_KEY    = os.getenv("APOLLO_API_KEY","")
HUBSPOT_KEY   = os.getenv("HUBSPOT_API_KEY","")
CHAIRMAN_EMAIL= os.getenv("CHAIRMAN_EMAIL","nyspotlightreport@gmail.com")

ICP = {
    "ideal_titles":     ["founder","ceo","owner","director","vp","head","editor","publisher"],
    "ideal_industries": ["media","publishing","marketing","agency","content","digital","news","journalism"],
    "company_size":     [1, 500],
    "locations":        ["new york","los angeles","miami","chicago","remote"],
}

class LeadPipelineBot(BaseBot):
    VERSION = "2.0.0"

    def __init__(self):
        super().__init__("lead-pipeline")

    def search_apollo(self, query="media executives new york", limit=20):
        if not APOLLO_KEY:
            self.logger.warning("No APOLLO_API_KEY")
            return []
        payload = json.dumps({
            "api_key": APOLLO_KEY,
            "q_keywords": query,
            "page": 1, "per_page": limit,
            "contact_email_status": ["verified","likely to engage"],
            "person_titles": ICP["ideal_titles"],
            "person_locations": ["New York","Los Angeles","Miami","Remote"],
            "q_organization_domains_list": [],
        }).encode()
        req = urllib.request.Request(
            "https://api.apollo.io/v1/mixed_people/search",
            data=payload,
            headers={"Content-Type":"application/json","Cache-Control":"no-cache"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                people = data.get("people", [])
                self.logger.info(f"Apollo returned {len(people)} leads for '{query}'")
                return people
        except Exception as e:
            self.logger.error(f"Apollo search error: {e}")
            return []

    def score_lead(self, person):
        name  = f"{person.get('first_name','')} {person.get('last_name','')}".strip()
        title = person.get("title","").lower()
        org   = person.get("organization",{}).get("name","") if person.get("organization") else ""
        email = person.get("email","")

        score = 0
        if any(t in title for t in ICP["ideal_titles"]): score += 30
        if any(i in (person.get("organization",{}) or {}).get("industry","").lower()
               for i in ICP["ideal_industries"]): score += 25
        if "new york" in person.get("city","").lower(): score += 20
        if email and "@" in email: score += 15
        if person.get("linkedin_url"): score += 10

        return {"name": name, "title": title, "company": org, "email": email,
                "score": score, "grade": "HOT" if score>=60 else "WARM" if score>=35 else "COLD",
                "linkedin": person.get("linkedin_url",""), "raw": person}

    def push_to_hubspot(self, lead):
        if not HUBSPOT_KEY or not lead.get("email"): return None
        payload = json.dumps({"properties": {
            "email": lead["email"], "firstname": lead["name"].split()[0] if lead["name"] else "",
            "lastname": " ".join(lead["name"].split()[1:]) if len(lead["name"].split())>1 else "",
            "jobtitle": lead["title"], "company": lead["company"],
            "hs_lead_status": "NEW", "lead_source": "Apollo Pipeline Bot",
            "notes_last_updated": datetime.now().isoformat(),
        }}).encode()
        req = urllib.request.Request(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            data=payload,
            headers={"Authorization":f"Bearer {HUBSPOT_KEY}","Content-Type":"application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read()).get("id")
        except urllib.error.HTTPError as e:
            if e.code == 409: return "already_exists"
            self.logger.error(f"HubSpot push error: {e.code}")
            return None

    def execute(self):
        queries = [
            "media executives new york director VP",
            "publisher editor content marketing agency founder",
            "digital media CEO entrepreneur New York",
        ]
        all_leads = []
        for q in queries:
            leads = self.search_apollo(q, limit=10)
            scored = [self.score_lead(p) for p in leads]
            all_leads.extend(scored)

        # Deduplicate by email
        seen = set()
        unique = []
        for l in all_leads:
            key = l.get("email","") or l.get("name","")
            if key and key not in seen:
                seen.add(key); unique.append(l)

        hot   = [l for l in unique if l["grade"]=="HOT"]
        warm  = [l for l in unique if l["grade"]=="WARM"]

        # Push hot leads to HubSpot
        pushed = 0
        for lead in hot[:10]:
            r = self.push_to_hubspot(lead)
            if r: pushed += 1

        # Alert Chairman
        if hot:
            rows = "".join([f"<tr><td>{l['name']}</td><td>{l['title']}</td><td>{l['company']}</td><td>{l['score']}</td></tr>" for l in hot[:5]])
            AlertSystem.send(
                subject=f"🔥 {len(hot)} Hot Leads Found — {datetime.now().strftime('%b %d')}",
                body_html=f"""<h3>Hot Leads This Week</h3>
<table border='1'><tr><th>Name</th><th>Title</th><th>Company</th><th>Score</th></tr>{rows}</table>
<p>Pushed {pushed} to HubSpot. Total found: {len(unique)}</p>""",
                severity="INFO")

        self.log_summary(total=len(unique), hot=len(hot), warm=len(warm), pushed_hubspot=pushed)
        return {"total": len(unique), "hot": len(hot), "warm": len(warm), "pushed": pushed}

if __name__ == "__main__":
    bot = LeadPipelineBot(); bot.run()
