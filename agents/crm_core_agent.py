#!/usr/bin/env python3
"""
CRM Core Agent — NYSR Mega-Agency Phase 1
The Salesforce/HubSpot replacement, built on Claude + Apollo + HubSpot.

Pipeline Stages:
  1. LEAD       — identified, not yet contacted
  2. PROSPECT   — first contact made
  3. QUALIFIED  — confirmed budget/need/authority/timeline
  4. PROPOSAL   — offer sent
  5. NEGOTIATION — in discussion
  6. CLOSED_WON — deal signed
  7. CLOSED_LOST — deal dead (with reason)

Scoring:
  - Fit Score (0-100):  how well they match ideal customer profile
  - Engagement Score:  email opens, replies, site visits
  - Intent Score:      job posts, funding, tech stack signals
  - Composite Score:   weighted average → priority queue
"""
import os, sys, json, time, logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CRM] %(message)s")

ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY", "")
APOLLO_KEY   = os.environ.get("APOLLO_API_KEY", "")
HUBSPOT_KEY  = os.environ.get("HUBSPOT_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

import urllib.request, urllib.error

# ── PIPELINE STAGES ───────────────────────────────────────────────
STAGES = {
    "LEAD":        {"order": 1, "color": "#64748B", "goal": "Qualify the lead"},
    "PROSPECT":    {"order": 2, "color": "#3B82F6", "goal": "Book discovery call"},
    "QUALIFIED":   {"order": 3, "color": "#8B5CF6", "goal": "Send proposal"},
    "PROPOSAL":    {"order": 4, "color": "#F59E0B", "goal": "Get decision"},
    "NEGOTIATION": {"order": 5, "color": "#EF4444", "goal": "Close deal"},
    "CLOSED_WON":  {"order": 6, "color": "#22C55E", "goal": "Onboard"},
    "CLOSED_LOST": {"order": 7, "color": "#94A3B8", "goal": "Learn and reactivate"},
}

# ── IDEAL CUSTOMER PROFILES ───────────────────────────────────────
ICPS = {
    "proflow_ai": {
        "name": "ProFlow AI SaaS ICP",
        "description": "Content creators, agencies, marketers who need AI content automation",
        "titles": ["content manager", "marketing manager", "founder", "CEO", "CMO", "content director"],
        "company_sizes": ["1-10", "11-50", "51-200"],
        "industries": ["marketing", "media", "ecommerce", "saas", "agency"],
        "pain_points": ["content production speed", "SEO rankings", "social media posting", "content consistency"],
        "budget_range": "$97-497/mo",
        "deal_size": 97,
    },
    "dfy_agency": {
        "name": "DFY Bot Setup ICP",
        "description": "Entrepreneurs and business owners who want AI automation but can't build it",
        "titles": ["founder", "CEO", "owner", "president"],
        "company_sizes": ["1-10", "11-50"],
        "industries": ["ecommerce", "coaching", "consulting", "real estate", "finance"],
        "pain_points": ["manual processes", "content creation", "lead generation", "time constraints"],
        "budget_range": "$1,500-10,000 one-time",
        "deal_size": 5000,
    },
    "enterprise_agency": {
        "name": "Enterprise Agency ICP",
        "description": "Marketing agencies and mid-market companies needing full AI system",
        "titles": ["VP marketing", "digital director", "agency owner", "CMO"],
        "company_sizes": ["51-200", "201-500"],
        "industries": ["marketing agency", "digital agency", "pr agency"],
        "pain_points": ["client delivery speed", "team scaling", "content volume", "reporting"],
        "budget_range": "$997-1997/mo",
        "deal_size": 1200,
    },
}

# ── CONTACT SCORING ───────────────────────────────────────────────
def score_contact(contact: Dict, icp_key: str = "dfy_agency") -> Dict:
    """Score a contact 0-100 against our ICP. Returns scoring breakdown."""
    icp = ICPS.get(icp_key, ICPS["dfy_agency"])
    scores = {}

    # Title match (0-30 points)
    title = (contact.get("title") or contact.get("job_title") or "").lower()
    title_score = 0
    for t in icp["titles"]:
        if t in title:
            title_score = 30
            break
    if title_score == 0 and any(w in title for w in ["vp", "director", "head of", "manager"]):
        title_score = 15
    scores["title_fit"] = title_score

    # Company size (0-20 points)
    employees = contact.get("employees") or contact.get("company_size") or 0
    if isinstance(employees, str):
        try: employees = int(employees.replace(",","").split("-")[0])
        except: employees = 0
    size_score = 0
    if 1 <= employees <= 50:   size_score = 20
    elif 51 <= employees <= 200: size_score = 15
    elif 201 <= employees <= 500: size_score = 10
    scores["size_fit"] = size_score

    # Industry match (0-20 points)
    industry = (contact.get("industry") or "").lower()
    industry_score = 0
    for ind in icp["industries"]:
        if ind in industry:
            industry_score = 20
            break
    scores["industry_fit"] = industry_score

    # Data completeness (0-15 points)
    completeness = 0
    for field in ["email", "phone", "linkedin_url", "company", "title"]:
        if contact.get(field): completeness += 3
    scores["data_completeness"] = completeness

    # Engagement signals (0-15 points) — email opens/replies if available
    engagement = contact.get("engagement_score", 0)
    scores["engagement"] = min(15, engagement)

    total = sum(scores.values())
    grade = "A" if total >= 75 else "B" if total >= 55 else "C" if total >= 35 else "D"

    return {
        "total": total,
        "grade": grade,
        "breakdown": scores,
        "recommended_icp": icp_key,
        "priority": "HIGH" if total >= 70 else "MEDIUM" if total >= 45 else "LOW"
    }

# ── AI DEAL INTELLIGENCE ──────────────────────────────────────────
def analyze_deal(contact: Dict, stage: str, history: List[str] = None) -> Dict:
    """Use Claude to analyze a deal and recommend next best action."""
    if not ANTHROPIC:
        return {"next_action": "Follow up via email", "probability": 0.3, "risk": "No AI key"}

    context = f"""
Contact: {contact.get('name','')} | {contact.get('title','')} at {contact.get('company','')}
Stage: {stage} — {STAGES.get(stage,{}).get('goal','')}
Score: {contact.get('score',{}).get('total',0)}/100 ({contact.get('score',{}).get('grade','?')})
Last contact: {contact.get('last_contacted','unknown')}
History: {' | '.join(history or ['No history yet'])}
"""
    return claude_json(
        """You are a senior sales strategist. Analyze this deal and provide tactical guidance.
Return JSON: {
  "probability": 0.0-1.0,
  "next_action": "specific action",
  "timing": "when to do it",
  "message_angle": "what to say",
  "risk_factors": ["list"],
  "deal_size_estimate": 0,
  "days_to_close": 0
}""",
        f"Analyze this deal:\n{context}",
        max_tokens=400
    ) or {"next_action": "Send follow-up email", "probability": 0.25}

# ── HUBSPOT SYNC ──────────────────────────────────────────────────
def sync_to_hubspot(contact: Dict, stage: str) -> bool:
    """Sync a contact and deal to HubSpot CRM."""
    if not HUBSPOT_KEY:
        log.warning("No HUBSPOT_API_KEY — skipping HubSpot sync")
        return False

    try:
        import urllib.parse

        # Upsert contact
        contact_payload = {
            "properties": {
                "email":      contact.get("email", ""),
                "firstname":  (contact.get("name") or "").split()[0],
                "lastname":   " ".join((contact.get("name") or "").split()[1:]),
                "jobtitle":   contact.get("title", ""),
                "company":    contact.get("company", ""),
                "phone":      contact.get("phone", ""),
                "website":    contact.get("website", ""),
                "hs_lead_status": stage,
                "nysr_score": str(contact.get("score", {}).get("total", 0)),
                "nysr_grade": contact.get("score", {}).get("grade", ""),
            }
        }
        # Remove empty values
        contact_payload["properties"] = {k: v for k, v in contact_payload["properties"].items() if v}

        data = json.dumps(contact_payload).encode()
        req = urllib.request.Request(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            data=data,
            headers={
                "Authorization": f"Bearer {HUBSPOT_KEY}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            log.info(f"HubSpot contact synced: {result.get('id','?')}")
            return True

    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        log.warning(f"HubSpot sync failed HTTP {e.code}: {body}")
        return False
    except Exception as e:
        log.warning(f"HubSpot sync error: {e}")
        return False

# ── SUPABASE PERSISTENCE ──────────────────────────────────────────
def supabase_request(method: str, table: str, data: dict = None, query: str = "") -> Optional[Any]:
    """Make a request to Supabase REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
        payload = json.dumps(data).encode() if data else None
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            method=method
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"Supabase {method} {table}: {e}")
        return None

def save_contact(contact: Dict) -> bool:
    """Save/update contact in Supabase."""
    result = supabase_request("POST", "contacts", {
        "email":       contact.get("email", ""),
        "name":        contact.get("name", ""),
        "title":       contact.get("title", ""),
        "company":     contact.get("company", ""),
        "phone":       contact.get("phone", ""),
        "linkedin":    contact.get("linkedin_url", ""),
        "stage":       contact.get("stage", "LEAD"),
        "score":       contact.get("score", {}).get("total", 0),
        "grade":       contact.get("score", {}).get("grade", ""),
        "icp":         contact.get("icp", ""),
        "priority":    contact.get("score", {}).get("priority", ""),
        "source":      contact.get("source", "apollo"),
        "last_updated": datetime.utcnow().isoformat(),
    })
    return result is not None

def get_pipeline_stats() -> Dict:
    """Get pipeline statistics from Supabase."""
    stats = {}
    for stage in STAGES:
        result = supabase_request("GET", "contacts", query=f"?stage=eq.{stage}&select=id,score")
        if result:
            scores = [c.get("score", 0) for c in result]
            stats[stage] = {
                "count": len(result),
                "avg_score": round(sum(scores)/len(scores)) if scores else 0,
                "total_pipeline_value": len(result) * ICPS["dfy_agency"]["deal_size"]
            }
        else:
            stats[stage] = {"count": 0, "avg_score": 0, "total_pipeline_value": 0}
    return stats

# ── APOLLO LEAD PULL ──────────────────────────────────────────────
def pull_apollo_leads(num_leads: int = 50) -> List[Dict]:
    """Pull fresh leads from Apollo and score them."""
    if not APOLLO_KEY:
        log.warning("No APOLLO_API_KEY")
        return []

    try:
        payload = {
            "q_organization_num_employees_ranges": ["1,50", "51,200"],
            "q_not_already_in_sequence": True,
            "page": 1,
            "per_page": min(num_leads, 100),
            "prospected_by_current_team": ["no"],
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.apollo.io/api/v1/mixed_people/search",
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": APOLLO_KEY
            }
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())

        contacts = []
        for person in result.get("people", []):
            contact = {
                "id":          person.get("id"),
                "name":        person.get("name"),
                "title":       person.get("title"),
                "email":       person.get("email"),
                "phone":       person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None,
                "company":     person.get("organization", {}).get("name"),
                "website":     person.get("organization", {}).get("website_url"),
                "employees":   person.get("organization", {}).get("num_employees"),
                "industry":    person.get("organization", {}).get("industry"),
                "linkedin_url": person.get("linkedin_url"),
                "source":      "apollo",
                "stage":       "LEAD",
            }
            # Score against all ICPs, pick best
            best_score = None
            best_icp   = None
            for icp_key in ICPS:
                score = score_contact(contact, icp_key)
                if best_score is None or score["total"] > best_score["total"]:
                    best_score = score
                    best_icp   = icp_key

            contact["score"] = best_score
            contact["icp"]   = best_icp
            contacts.append(contact)

        # Sort by score descending
        contacts.sort(key=lambda c: c["score"]["total"], reverse=True)
        log.info(f"Pulled {len(contacts)} leads from Apollo. Top score: {contacts[0]['score']['total'] if contacts else 0}")
        return contacts

    except Exception as e:
        log.error(f"Apollo pull failed: {e}")
        return []

# ── PIPELINE MANAGER ──────────────────────────────────────────────
def advance_stage(contact_id: str, new_stage: str, reason: str = "") -> bool:
    """Move a contact to the next pipeline stage."""
    result = supabase_request("PATCH", "contacts",
        data={"stage": new_stage, "stage_changed_at": datetime.utcnow().isoformat(), "stage_reason": reason},
        query=f"?id=eq.{contact_id}"
    )
    if result:
        log.info(f"Contact {contact_id} → {new_stage}: {reason}")
    return result is not None

def get_high_priority_contacts(limit: int = 10) -> List[Dict]:
    """Get top-priority contacts that need action today."""
    result = supabase_request("GET", "contacts",
        query=f"?priority=eq.HIGH&stage=neq.CLOSED_WON&stage=neq.CLOSED_LOST&order=score.desc&limit={limit}"
    )
    return result or []

# ── DAILY CRM RUN ─────────────────────────────────────────────────
def run():
    log.info("CRM Agent starting daily run...")

    # 1. Pull fresh leads from Apollo
    log.info("Pulling Apollo leads...")
    leads = pull_apollo_leads(50)
    log.info(f"Got {len(leads)} leads. A-grade: {len([l for l in leads if l['score']['grade']=='A'])}")

    # 2. Save to Supabase
    saved = 0
    for lead in leads:
        if save_contact(lead):
            saved += 1

    # 3. Sync high-value leads to HubSpot
    synced = 0
    for lead in leads:
        if lead["score"]["grade"] in ["A", "B"]:
            if sync_to_hubspot(lead, lead["stage"]):
                synced += 1

    # 4. Get pipeline stats
    stats = get_pipeline_stats()

    # 5. AI analysis on top deals
    priority = get_high_priority_contacts(5)
    analyses = []
    for contact in priority:
        analysis = analyze_deal(contact, contact.get("stage", "LEAD"))
        analyses.append({
            "contact": contact.get("name", ""),
            "company": contact.get("company", ""),
            "stage":   contact.get("stage", ""),
            "score":   contact.get("score", 0),
            "analysis": analysis
        })
        log.info(f"Deal analysis: {contact.get('name','')} @ {contact.get('company','')} — {analysis.get('next_action','')}")

    total_pipeline = sum(s.get("total_pipeline_value",0) for s in stats.values())
    log.info(f"Pipeline: {sum(s['count'] for s in stats.values())} contacts | ${total_pipeline:,} value")
    log.info(f"Saved: {saved} | HubSpot synced: {synced}")

    return {
        "leads_pulled": len(leads),
        "saved": saved,
        "hubspot_synced": synced,
        "pipeline_stats": stats,
        "priority_analyses": analyses,
        "total_pipeline_value": total_pipeline,
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
