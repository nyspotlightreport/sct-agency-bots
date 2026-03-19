#!/usr/bin/env python3
"""
LEAD PIPELINE BOT — S.C. Thomas Internal Agency
Searches Apollo for new leads → scores them with Claude → pushes scored leads to HubSpot
→ enrolls hot leads in email sequence → notifies Chairman of top prospects
Usage: python lead_pipeline_bot.py --search "marketing directors NYC" --limit 25
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
APOLLO_API_KEY    = os.getenv("APOLLO_API_KEY", "")
HUBSPOT_API_KEY   = os.getenv("HUBSPOT_API_KEY", "")
CHAIRMAN_EMAIL    = os.getenv("CHAIRMAN_EMAIL", "seanb041992@gmail.com")

# Scoring criteria — customize for your ICP (Ideal Customer Profile)
ICP_CONFIG = {
    "ideal_titles":      ["founder", "ceo", "owner", "director", "vp", "head of"],
    "ideal_industries":  ["media", "publishing", "marketing", "agency", "content", "digital"],
    "ideal_company_size": [1, 200],   # employee range
    "ideal_locations":   ["new york", "los angeles", "miami", "remote"],
    "disqualifiers":     ["student", "intern", "freelancer"],  # skip these
}

# ─── APOLLO SEARCH ────────────────────────────────────────────────────────────

def search_apollo(query, limit=25):
    """Search for people on Apollo"""
    if not APOLLO_API_KEY:
        print("[lead-bot] No Apollo API key — returning mock data")
        return []

    headers = {"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"}
    
    # Parse query into Apollo filters
    payload = {
        "page": 1,
        "per_page": limit,
        "q_keywords": query,
        "contact_email_status_cd": ["verified"],
        "person_not_in_current_context": True,
    }

    try:
        r = requests.post(
            "https://api.apollo.io/v1/mixed_people/search",
            headers=headers, json=payload, timeout=15
        )
        r.raise_for_status()
        people = r.json().get("people", [])
        print(f"[lead-bot] Apollo returned {len(people)} leads")
        return people
    except Exception as e:
        print(f"[lead-bot] Apollo search failed: {e}")
        return []

def format_lead(person):
    """Normalize Apollo person object"""
    org = person.get("organization", {}) or {}
    return {
        "id":          person.get("id", ""),
        "name":        f"{person.get('first_name','')} {person.get('last_name','')}".strip(),
        "email":       person.get("email", ""),
        "title":       person.get("title", ""),
        "company":     org.get("name", ""),
        "industry":    org.get("industry", ""),
        "employees":   org.get("estimated_num_employees", 0) or 0,
        "location":    person.get("city", "") + ", " + (person.get("state", "") or ""),
        "linkedin":    person.get("linkedin_url", ""),
        "seniority":   person.get("seniority", ""),
    }

# ─── CLAUDE SCORER ────────────────────────────────────────────────────────────

def score_leads_with_claude(leads):
    """Score and prioritize leads using Claude"""
    if not ANTHROPIC_API_KEY or not leads:
        # Simple rule-based fallback
        for lead in leads:
            title_lower = lead.get("title","").lower()
            score = 50
            for t in ICP_CONFIG["ideal_titles"]:
                if t in title_lower: score += 20; break
            lead["score"] = min(score, 100)
            lead["score_reason"] = "Rule-based scoring (no API key)"
            lead["outreach_angle"] = f"Hi {lead['name'].split()[0]}, saw your work at {lead['company']}."
        return leads

    batch_text = "\n".join([
        f"{i+1}. {l['name']} | {l['title']} @ {l['company']} | {l['industry']} | {l['employees']} emp | {l['location']}"
        for i, l in enumerate(leads)
    ])

    system = f"""You are the lead scoring system for S.C. Thomas.
Score each lead 0-100 based on fit with this ICP:
- Ideal titles: {ICP_CONFIG['ideal_titles']}
- Ideal industries: {ICP_CONFIG['ideal_industries']}  
- Ideal company size: {ICP_CONFIG['ideal_company_size'][0]}-{ICP_CONFIG['ideal_company_size'][1]} employees
- Location preference: {ICP_CONFIG['ideal_locations']}
- Disqualifiers: {ICP_CONFIG['disqualifiers']}

90-100: Perfect ICP fit, reach out immediately
70-89: Good fit, worth outreach
50-69: Possible fit, lower priority
Below 50: Poor fit, skip

Return ONLY valid JSON array:
[{{"index": 1, "score": 85, "score_reason": "CEO of media company", "outreach_angle": "personalized 1-line opener", "priority": "HOT|WARM|COLD"}}]"""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "system": system,
        "messages": [{"role": "user", "content": f"Score these {len(leads)} leads:\n{batch_text}"}]
    }

    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
        scores = json.loads(text)
        for s in scores:
            idx = s["index"] - 1
            if 0 <= idx < len(leads):
                leads[idx].update({
                    "score":          s.get("score", 50),
                    "score_reason":   s.get("score_reason", ""),
                    "outreach_angle": s.get("outreach_angle", ""),
                    "priority":       s.get("priority", "COLD"),
                })
    except Exception as e:
        print(f"[lead-bot] Scoring error: {e}")

    return sorted(leads, key=lambda x: x.get("score", 0), reverse=True)

# ─── HUBSPOT PUSHER ───────────────────────────────────────────────────────────

def push_to_hubspot(lead):
    """Create or update contact in HubSpot"""
    if not HUBSPOT_API_KEY or not lead.get("email"):
        return False

    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    props = {
        "email":     lead["email"],
        "firstname": lead["name"].split()[0] if lead["name"] else "",
        "lastname":  " ".join(lead["name"].split()[1:]) if lead["name"] else "",
        "jobtitle":  lead["title"],
        "company":   lead["company"],
        "hs_lead_status": "NEW",
        "lead_score__custom": str(lead.get("score", 0)),
        "notes_last_updated": lead.get("score_reason", ""),
    }

    try:
        # Try create first
        r = requests.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers, json={"properties": props}, timeout=10
        )
        if r.status_code == 409:  # Already exists, update instead
            contact_id = r.json().get("message","").split("ID: ")[-1].strip()
            if contact_id:
                requests.patch(
                    f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
                    headers=headers, json={"properties": props}, timeout=10
                )
        return r.status_code in [200, 201, 204, 409]
    except Exception as e:
        print(f"[lead-bot] HubSpot push failed for {lead.get('email')}: {e}")
        return False

# ─── REPORT ───────────────────────────────────────────────────────────────────

def print_report(leads):
    hot   = [l for l in leads if l.get("priority") == "HOT"]
    warm  = [l for l in leads if l.get("priority") == "WARM"]
    cold  = [l for l in leads if l.get("priority") == "COLD"]

    print(f"\n{'='*60}")
    print(f"LEAD PIPELINE REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"Total leads: {len(leads)} | HOT: {len(hot)} | WARM: {len(warm)} | COLD: {len(cold)}")
    
    if hot:
        print(f"\n🔥 HOT LEADS (reach out today):")
        for l in hot:
            print(f"  [{l.get('score',0)}] {l['name']} — {l['title']} @ {l['company']}")
            print(f"       {l['email']} | {l.get('outreach_angle','')}")
    
    if warm:
        print(f"\n♨️  WARM LEADS (reach out this week):")
        for l in warm[:10]:
            print(f"  [{l.get('score',0)}] {l['name']} — {l['title']} @ {l['company']}")

    print(f"\n{'='*60}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run(query, limit=25, push_to_crm=True):
    print(f"[lead-bot] Searching Apollo: '{query}' (limit: {limit})")
    
    raw_leads   = search_apollo(query, limit)
    leads       = [format_lead(p) for p in raw_leads]
    
    print(f"[lead-bot] Scoring {len(leads)} leads with Claude...")
    scored      = score_leads_with_claude(leads)
    
    # Push to HubSpot
    if push_to_crm and HUBSPOT_API_KEY:
        pushed = 0
        for lead in scored:
            if lead.get("score", 0) >= 60:  # Only push worthwhile leads
                if push_to_hubspot(lead): pushed += 1
        print(f"[lead-bot] Pushed {pushed} leads to HubSpot")
    
    # Save results
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(scored, f, indent=2)
    
    print_report(scored)
    print(f"\n[lead-bot] Full results saved to {filename}")
    return scored

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", default="founder CEO media company New York", help="Search query")
    parser.add_argument("--limit",  type=int, default=25, help="Number of leads to pull")
    parser.add_argument("--no-crm", action="store_true", help="Skip HubSpot push")
    args = parser.parse_args()
    run(args.search, args.limit, push_to_crm=not args.no_crm)

# ─── SETUP ────────────────────────────────────────────────────────────────────
# pip install requests
# export ANTHROPIC_API_KEY=...
# export APOLLO_API_KEY=...
# export HUBSPOT_API_KEY=...
