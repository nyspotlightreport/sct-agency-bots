#!/usr/bin/env python3
"""Testimonial & Case Study Bot — Automates social proof collection.
Identifies happy customers, requests testimonials, formats case studies."""
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

TESTIMONIAL_FORMATS = {
    "one_liner": "One powerful sentence. Specific result. For use in emails and ads.",
    "short":     "2-3 sentences. Before/after. For website and social.",
    "case_study": "Full story. Problem→Solution→Results. For proposals and sales calls.",
    "video_script": "Talking points for a 60-second video testimonial.",
}

def generate_testimonial_request(customer: dict) -> dict:
    name    = (customer.get("name","") or "").split()[0] or "there"
    company = customer.get("company","your company")
    months  = customer.get("months_active", 3)

    body = claude(
        "Write a testimonial request email. Genuine, specific, easy to respond to. Offer 3 options: quick sentence, short paragraph, or video call. Under 120 words.",
        f"Customer {name} at {company}, {months} months active, happy customer.",
        max_tokens=200
    ) or f"""Hi {name},

Working with {company} has been a highlight — you've really gotten value out of the system.

Would you be open to sharing a quick testimonial? It would mean a lot and help us help more companies like yours.

Three easy options:
1. One sentence I can quote (reply here)
2. A short paragraph for our website (reply here)
3. A 20-min call where I ask 3 questions and write it for you

No pressure — if you're too busy I totally understand.

Thanks either way,
S.C. Thomas"""

    return {
        "to": customer.get("email",""),
        "subject": f"Quick favor — {company}?",
        "body":    body,
    }

def format_testimonial(raw: str, customer: dict, format_type: str = "short") -> str:
    name    = customer.get("name","Customer")
    company = customer.get("company","Company")
    title   = customer.get("title","")
    formatted = claude(
        f"Format this testimonial as a professional {format_type} testimonial. Keep the authentic voice. Add attribution.",
        f"Raw testimonial: {raw}
Customer: {name}, {title} at {company}
Format: {TESTIMONIAL_FORMATS[format_type]}",
        max_tokens=300
    ) or raw
    return f'"{formatted}"
— {name}, {title}, {company}'

def generate_case_study(customer: dict, results: dict) -> str:
    company = customer.get("company","Company")
    return claude(
        "Write a compelling B2B case study. Format: Challenge → Solution → Results. 300 words. Specific numbers.",
        f"Company: {company} | Results: {json.dumps(results)} | Product: {customer.get('product','ProFlow')}",
        max_tokens=500
    ) or f"## {company} Case Study

**Challenge:** Content bottleneck.

**Solution:** NYSR ProFlow.

**Results:** {results}"

def run():
    customers = [{"name":"Sarah Kim","company":"DigitalAgency","title":"Founder","email":"sarah@agency.com","months_active":4}]
    for c in customers:
        req = generate_testimonial_request(c)
        log.info(f"Testimonial request: {req['subject']} → {c.get('email','?')} ")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
