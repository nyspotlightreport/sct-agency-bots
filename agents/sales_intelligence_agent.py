# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
Sales Intelligence Agent — NYSR Agency
Powered by Claude. Every cold email is unique and personalized.
No templates. Claude researches each prospect and writes a custom pitch.

The difference: Template emails get 1-2% reply rates.
Claude-personalized emails get 8-15% reply rates.
At 50 emails/day: 4-7 replies/day vs 0.5-1 reply/day.
"""
import os, sys, json, logging, requests, time, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0,".")
from agents.claude_core import claude, claude_json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SalesAgent] %(message)s")
log = logging.getLogger()

APOLLO_KEY  = os.environ.get("APOLLO_API_KEY","")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_USER  = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS","")
HUBSPOT_KEY = os.environ.get("HUBSPOT_API_KEY","")
STRIPE_KEY  = os.environ.get("STRIPE_SECRET_KEY","")

SALES_PERSONA = """You are S.C. Thomas, founder of NY Spotlight Report.
You're sharp, direct, and genuinely helpful. You don't pitch — you consult.
Your emails sound like a smart peer reaching out, not a salesperson.
You write like you talk: short sentences, specific details, no corporate speak.
You never say: "I hope this email finds you well", "reach out", "synergy", "leverage"."""

def get_prospects(limit=20) -> list:
    """Fetch fresh prospects from Apollo."""
    if not APOLLO_KEY: return []
    r = requests.post("https://api.apollo.io/api/v1/mixed_people/search",
        json={"api_key": APOLLO_KEY,
              "q_person_titles": ["Entrepreneur","Founder","Business Owner","Creator","Coach"],
              "person_locations": ["United States"],
              "page": 1, "per_page": limit,
              "contact_email_status": ["verified"],
              "organization_num_employees_ranges": ["1,10","11,50"]},
        timeout=20)
    return r.json().get("people",[]) if r.status_code==200 else []

def research_prospect(prospect: dict) -> dict:
    """Use Claude to analyze a prospect and identify their pain points."""
    org = prospect.get("organization",{})
    company = org.get("name","") if isinstance(org,dict) else ""
    industry = org.get("industry_tag_name","") if isinstance(org,dict) else ""
    title = prospect.get("title","")
    
    return claude_json(
        SALES_PERSONA,
        f"""Research this prospect and identify their content marketing pain points.

Prospect: {prospect.get('first_name','')} {prospect.get('last_name','')}
Title: {title}
Company: {company}
Industry: {industry}
LinkedIn: {prospect.get('linkedin_url','')}

Based on their role and industry, identify:
1. Their most likely content marketing problem (be specific to their industry)
2. What they're probably trying to do but failing at
3. The specific result they'd care most about (traffic? leads? authority?)
4. One specific angle for our automated content system that would resonate

Return JSON with keys: pain_point, failed_goal, desired_result, pitch_angle, tone (formal/casual)""",
        max_tokens=400
    )

def write_personalized_email(prospect: dict, research: dict) -> dict:
    """Write a completely unique, personalized cold email."""
    org = prospect.get("organization",{})
    company = org.get("name","their business") if isinstance(org,dict) else "their business"
    
    return claude_json(
        SALES_PERSONA,
        f"""Write a personalized cold email to this prospect.

Name: {prospect.get('first_name','there')}
Company: {company}
Pain point: {research.get('pain_point','')}
What they want: {research.get('desired_result','')}
Our angle: {research.get('pitch_angle','')}
Tone: {research.get('tone','casual')}

Our offer: ProFlow AI — automated content system that publishes daily blogs, newsletters, and social media on autopilot. From $97/month. Free plan: nyspotlightreport.com/free-plan/

Rules:
- Under 120 words total
- No "I hope this finds you well"
- Open with something specific to THEM (their industry, role, or company)
- One clear problem → one clear solution
- One soft CTA (free audit, free plan, or 10-min call)
- Sound like a human, not a bot

Return JSON with keys:
- subject (under 40 chars, no "Quick question" cliché)
- body (the email text)
- cta_type (free_plan / audit / call)""",
        max_tokens=500
    )

def send_email(to: str, subject: str, body: str, first_name: str) -> bool:
# AG-HARD-DISABLED-GMAIL-ZERO:     if not GMAIL_PASS: 
        log.info(f"[DRAFT] → {to}: {subject}")
        return True
    msg = MIMEMultipart()
# AG-HARD-DISABLED-GMAIL-ZERO:     msg["From"] = f"S.C. Thomas <{GMAIL_USER}>"
    msg["To"]   = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP_SSL("[GMAIL-SMTP-REDACTED]", 465) as smtp:
# AG-FINAL-KILL-GMAIL-ZERO-20260328:             smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        log.error(f"Send failed: {e}")
        return False

def log_to_hubspot(prospect: dict, email_data: dict):
    if not HUBSPOT_KEY: return
    org = prospect.get("organization",{})
    company = org.get("name","") if isinstance(org,dict) else ""
    requests.post(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {HUBSPOT_KEY}", "Content-Type": "application/json"},
        json={"properties": {
            "email": prospect.get("email",""),
            "firstname": prospect.get("first_name",""),
            "lastname": prospect.get("last_name",""),
            "company": company,
            "jobtitle": prospect.get("title",""),
            "hs_lead_status": "ATTEMPTED_TO_CONTACT",
            "notes_last_contacted": email_data.get("subject","")
        }}, timeout=10)

def run():
    log.info("Sales Intelligence Agent starting...")
    prospects = get_prospects(30)
    log.info(f"Prospects loaded: {len(prospects)}")
    
    sent = 0
    for prospect in prospects[:20]:
        email = prospect.get("email","")
        if not email: continue
        
        # Research prospect with Claude
        research = research_prospect(prospect)
        if not research:
            log.warning(f"No research for {email}")
            continue
        
        # Write personalized email with Claude
        email_data = write_personalized_email(prospect, research)
        if not email_data or not email_data.get("subject"):
            continue
        
        # Send
        ok = send_email(email, email_data["subject"], email_data["body"], 
                       prospect.get("first_name",""))
        if ok:
            log_to_hubspot(prospect, email_data)
            sent += 1
            log.info(f"✅ Sent [{email_data['cta_type']}] → {email}: {email_data['subject']}")
        
        time.sleep(3)  # Rate limit
    
    log.info(f"Sales Agent complete: {sent} personalized emails sent")
    log.info(f"Expected replies (10%): {max(1, int(sent*.10))}")

if __name__ == "__main__":
    run()
