#!/usr/bin/env python3
"""
Cold Outreach Agent ΓÇö NYSR Multi-Channel Cold Outreach Engine
Generates and sends personalized cold outreach across email, LinkedIn, Twitter.

Channels:
  - Email via Apollo sequences (primary ΓÇö 200/day limit)
  - LinkedIn via direct message drafts
  - Twitter/X via DM

Personalization uses Claude to:
  1. Research the company/contact
  2. Find a relevant hook (pain point, recent news, mutual connection)
  3. Write hyper-personalized first line
  4. Generate full sequence (7 touches over 21 days)

NYSR Offer Menu:
  A. ProFlow AI Starter ($97/mo) ΓÇö for content teams
  B. ProFlow AI Growth ($297/mo) ΓÇö for agencies
  C. DFY Bot Setup ($1,497 one-time) ΓÇö done-for-you system build
  D. DFY Bot Agency ($4,997 one-time) ΓÇö full agency automation
  E. Newsletter Monetization System ($997) ΓÇö for newsletter operators
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, ICPS
except Exception as e:
    print(f"Import partial: {e}")
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None

import urllib.request, urllib.parse, urllib.error

# === MEMORY ENGINE (auto-wired) ===
import sys as _sys
_sys.path.insert(0, '/opt/nysr')
try:
    from agent_memory_engine import read_memory as _read_memory, write_memory as _write_memory
    _agent_name = __file__.split('/')[-1].replace('.py','')
    _prior_memory = _read_memory(_agent_name)
except:
    _read_memory = lambda x: {}
    _write_memory = lambda x, y: None
    _prior_memory = {}
# === END MEMORY ENGINE ===



log = logging.getLogger(__name__)

APOLLO_KEY    = os.environ.get("APOLLO_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

NYSR_OFFERS = {
    "proflow_starter": {
        "name":    "ProFlow AI Starter",
        "price":   "$97/mo",
        "hook":    "cuts content production time by 80%",
        "cta":     "Want me to show you how it works in 15 minutes?",
        "url":     "https://nyspotlightreport.com/proflow/",
        "for":     ["content manager","marketing manager","blogger","creator"],
    },
    "proflow_growth": {
        "name":    "ProFlow AI Growth",
        "price":   "$297/mo",
        "hook":    "automates 90% of your agency content workflow",
        "cta":     "Happy to show you a custom demo for your agency ΓÇö 20 mins?",
        "url":     "https://nyspotlightreport.com/proflow/",
        "for":     ["agency owner","marketing director","CMO","digital director"],
    },
    "dfy_essential": {
        "name":    "DFY Bot Setup",
        "price":   "$1,497 one-time",
        "hook":    "we build your entire AI system so you don't have to touch code",
        "cta":     "Are you open to a quick 15-min call to see if it's a fit?",
        "url":     "https://nyspotlightreport.com/dfy/",
        "for":     ["founder","CEO","owner","entrepreneur"],
    },
    "dfy_agency": {
        "name":    "DFY Agency Automation",
        "price":   "$4,997 one-time",
        "hook":    "automates your entire agency operations ΓÇö lead gen, content, client delivery",
        "cta":     "Could we jump on a 30-min call this week?",
        "url":     "https://nyspotlightreport.com/dfy/",
        "for":     ["agency owner","agency CEO","digital agency"],
    },
}

SEQUENCE_TEMPLATES = {
    "7_touch": [
        {"day": 0,  "type": "email",    "angle": "problem_aware",    "length": "short"},
        {"day": 3,  "type": "email",    "angle": "value_add",        "length": "medium"},
        {"day": 5,  "type": "linkedin", "angle": "connection_req",   "length": "ultra_short"},
        {"day": 7,  "type": "email",    "angle": "case_study",       "length": "medium"},
        {"day": 10, "type": "email",    "angle": "breakup_almost",   "length": "short"},
        {"day": 14, "type": "linkedin", "angle": "follow_up_nudge",  "length": "short"},
        {"day": 21, "type": "email",    "angle": "final_breakup",    "length": "ultra_short"},
    ]
}

def select_offer(contact: dict) -> dict:
    """Select the best offer for this contact based on their profile."""
    title = (contact.get("title") or "").lower()
    company_size = contact.get("employees") or 0
    if isinstance(company_size, str):
        try: company_size = int(company_size.replace(",","").split("-")[0])
        except: company_size = 0

    # Match offer to contact
    if any(k in title for k in ["agency","director","CMO","vp"]) and company_size >= 10:
        return NYSR_OFFERS["dfy_agency"]
    elif any(k in title for k in ["founder","CEO","owner"]) and company_size <= 20:
        return NYSR_OFFERS["dfy_essential"]
    elif any(k in title for k in ["content","marketing","creator","blogger"]):
        return NYSR_OFFERS["proflow_starter"]
    else:
        return NYSR_OFFERS["dfy_essential"]

def write_cold_email(contact: dict, offer: dict, touch_num: int = 1, angle: str = "problem_aware") -> dict:
    """Use Claude to write a hyper-personalized cold email."""
    prompt = f"""Write a cold outreach email for touch #{touch_num} using the "{angle}" angle.

Contact: {contact.get("name","")} | {contact.get("title","")} at {contact.get("company","")}
Industry: {contact.get("industry","unknown")} | ~{contact.get("employees","?")} employees
Offer: {offer["name"]} ΓÇö {offer["price"]} ΓÇö {offer["hook"]}
CTA: {offer["cta"]}

Rules:
- Touch 1: Problem-aware hook, NO pitch. 3-5 sentences max. End with soft question.
- Touch 2-3: Value add. Reference something specific about their company. 5-7 sentences.
- Touch 4-5: Case study angle. "A client like you..." format. Brief proof.
- Touch 6-7: Breakup email. Ultra short. Create urgency/scarcity.
- Never: "I hope this email finds you well", "I wanted to reach out", corporate fluff
- Always: First line = hyper-specific hook about THEM (not us)
- Closing: {offer["cta"]}

Return JSON: {{
  "subject": "subject line (A/B test: also provide subject_b)",
  "subject_b": "alternate subject line",
  "body": "full email body",
  "personalization_note": "what makes this specific to them",
  "expected_reply_rate": 0.0-0.15
}}"""

    return claude_json(
        "You are a world-class B2B cold email writer. You write emails with 15-25% reply rates.",
        prompt, max_tokens=600
    ) or {
        "subject": f"Quick question, {contact.get('name','').split()[0] if contact.get('name') else 'there'}",
        "body": f"Hi {contact.get('name','').split()[0] if contact.get('name') else 'there'},\n\nQuick question ΓÇö are you currently using any AI tools to automate your content workflow?\n\nReason I ask: {offer['hook']}.\n\n{offer['cta']}\n\nBest,\nSean\nNY Spotlight Report",
        "personalization_note": "Generic fallback",
        "expected_reply_rate": 0.05
    }

def write_linkedin_message(contact: dict, offer: dict, msg_type: str = "connection_req") -> str:
    """Write a LinkedIn connection request or message."""
    if msg_type == "connection_req":
        prompt = f"""Write a LinkedIn connection request note (max 300 chars).
Contact: {contact.get("name","")} | {contact.get("title","")} at {contact.get("company","")}
My offer: {offer["name"]} ΓÇö {offer["hook"]}
Rules: No pitch. Reference something specific. Sound human. Max 300 chars."""
    else:
        prompt = f"""Write a LinkedIn DM follow-up (max 500 chars).
Contact: {contact.get("name","")} | {contact.get("title","")} at {contact.get("company","")}
My offer: {offer["name"]}
Type: {msg_type}
Rules: Reference connection. Brief value proposition. Clear ask. Max 500 chars."""

    return claude(
        "You write LinkedIn messages with 35%+ acceptance rates.",
        prompt, max_tokens=150
    ) or f"Hi {contact.get('name','').split()[0] if contact.get('name') else 'there'} ΓÇö saw your work at {contact.get('company','')} and thought it'd be worth connecting. Always great to connect with {contact.get('title','')}s in this space."

def send_apollo_email(contact_id: str, sequence_id: str = None) -> bool:
    """Enroll contact in Apollo email sequence."""
    if not APOLLO_KEY or not sequence_id:
        return False
    try:
        data = json.dumps({"contact_ids": [contact_id], "emailer_campaign_id": sequence_id}).encode()
        req = urllib.request.Request(
            "https://api.apollo.io/api/v1/emailer_campaign_add_contact_ids",
            data=data,
            headers={"Content-Type":"application/json","X-Api-Key":APOLLO_KEY}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        log.warning(f"Apollo enroll failed: {e}")
        return False

def generate_full_sequence(contact: dict) -> dict:
    """Generate complete 7-touch outreach sequence for a contact."""
    offer = select_offer(contact)
    sequence = []

    for touch in SEQUENCE_TEMPLATES["7_touch"]:
        if touch["type"] == "email":
            content = write_cold_email(contact, offer, len(sequence)+1, touch["angle"])
            sequence.append({
                "day":     touch["day"],
                "channel": "email",
                "subject": content.get("subject",""),
                "subject_b": content.get("subject_b",""),
                "body":    content.get("body",""),
                "angle":   touch["angle"],
            })
        elif touch["type"] == "linkedin":
            msg = write_linkedin_message(contact, offer, touch["angle"])
            sequence.append({
                "day":     touch["day"],
                "channel": "linkedin",
                "body":    msg,
                "angle":   touch["angle"],
            })

    return {
        "contact":  contact.get("name",""),
        "company":  contact.get("company",""),
        "offer":    offer["name"],
        "sequence": sequence,
        "generated_at": datetime.utcnow().isoformat(),
    }

def save_sequence(contact_id: str, sequence: dict) -> bool:
    """Save sequence to Supabase for tracking."""
    return supabase_request("POST", "sequences", {
        "contact_id":   contact_id,
        "offer":        sequence.get("offer",""),
        "sequence_data": json.dumps(sequence.get("sequence",[])),
        "status":       "active",
        "touch_count":  0,
        "created_at":   datetime.utcnow().isoformat(),
    }) is not None

def run(limit: int = 20):
    """Generate outreach sequences for top uncontacted leads."""
    log.info(f"Cold Outreach Agent: generating sequences for {limit} leads...")

    # Get uncontacted A/B grade leads
    contacts = supabase_request("GET", "contacts",
        query=f"?stage=eq.LEAD&grade=in.(A,B)&order=score.desc&limit={limit}"
    ) or []

    sequences_generated = 0
    for contact in contacts:
        seq = generate_full_sequence(contact)
        if contact.get("id"):
            save_sequence(contact["id"], seq)
        sequences_generated += 1
        log.info(f"  Sequence for {contact.get('name','')} @ {contact.get('company','')} ΓÇö {seq['offer']}")

    log.info(f"Generated {sequences_generated} sequences")
    return {"sequences_generated": sequences_generated, "contacts_processed": len(contacts)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Outreach] %(message)s")
    run()
