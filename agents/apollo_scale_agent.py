#!/usr/bin/env python3
"""
Apollo Pro Scale Bot — NYSR Agency
With Apollo Pro (10,000 exports/month vs 50 free):
- 200 prospects/day instead of 2
- Full email verification
- Phone numbers included
- Company technographics (what tools they use)
- Intent data (who is researching competitors)

At 200 emails/day × 10% reply rate = 20 replies/day
At 5% close rate = 1 sale/day = $97-297/day minimum
"""
import os, sys, json, logging, time, requests
sys.path.insert(0,".")
from agents.claude_core import claude, claude_json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ApolloScale] %(message)s")
log = logging.getLogger()

APOLLO_KEY   = os.environ.get("APOLLO_API_KEY","")
GMAIL_USER   = os.environ.get("GMAIL_USER","")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS","")
HUBSPOT_KEY  = os.environ.get("HUBSPOT_API_KEY","")

DAILY_TARGET = 200  # With Pro plan

SEGMENTS = [
    {
        "name": "Coaches & Consultants",
        "titles": ["Business Coach","Life Coach","Executive Coach","Consultant","Advisor"],
        "revenue_range": "1M-10M",
        "pain": "spending too much time on content, not enough on clients",
        "pitch_angle": "proflow",
        "target_count": 50
    },
    {
        "name": "Agency Owners",
        "titles": ["Agency Owner","Founder","Managing Director"],
        "industry": "Marketing and Advertising",
        "pain": "selling content services but struggling to deliver at scale",
        "pitch_angle": "white_label",
        "target_count": 40
    },
    {
        "name": "E-commerce Founders",
        "titles": ["Founder","CEO","Owner"],
        "industry": "Retail",
        "revenue_range": "1M-50M",
        "pain": "need content for SEO but no in-house team",
        "pitch_angle": "dfy_agency",
        "target_count": 50
    },
    {
        "name": "SaaS Founders",
        "titles": ["Founder","Co-Founder","CEO"],
        "industry": "Computer Software",
        "revenue_range": "1M-20M",
        "pain": "content marketing is a bottleneck to growth",
        "pitch_angle": "proflow",
        "target_count": 60
    },
]

PITCH_ANGLES = {
    "proflow": {
        "cta": "14-day free trial",
        "url": "https://nyspotlightreport.com/proflow/",
        "one_liner": "automated content system that publishes daily for you"
    },
    "dfy_agency": {
        "cta": "free 30-min strategy call",
        "url": "https://nyspotlightreport.com/agency/",
        "one_liner": "done-for-you content operation from $997/month"
    },
    "white_label": {
        "cta": "white-label partnership call",
        "url": "https://nyspotlightreport.com/agency/",
        "one_liner": "white-label content system for your agency clients"
    }
}

def get_segment_prospects(segment: dict) -> list:
    if not APOLLO_KEY: return []
    payload = {
        "api_key": APOLLO_KEY,
        "q_person_titles": segment["titles"],
        "person_locations": ["United States"],
        "page": 1,
        "per_page": segment["target_count"],
        "contact_email_status": ["verified"],
    }
    if "industry" in segment:
        payload["organization_industry_tag_ids"] = []
    r = requests.post("https://api.apollo.io/api/v1/mixed_people/search",
        json=payload, timeout=30)
    return r.json().get("people",[]) if r.status_code==200 else []

def write_segment_email(prospect: dict, segment: dict) -> dict:
    """Claude writes a unique email per prospect using segment context."""
    org = prospect.get("organization",{})
    company = org.get("name","") if isinstance(org,dict) else ""
    angle = PITCH_ANGLES[segment.get("pitch_angle","proflow")]
    
    return claude_json(
        """You are S.C. Thomas, founder of NY Spotlight Report. Sharp, direct, peer-level.
Write cold emails that sound like a real person reached out — never like a bot.""",
        f"""Write a cold email for this specific prospect.

Name: {prospect.get('first_name','there')}
Company: {company}
Title: {prospect.get('title','')}
Segment: {segment['name']}
Their pain: {segment['pain']}
Our offer: {angle['one_liner']}
CTA: {angle['cta']} → {angle['url']}

Rules:
- Under 100 words
- Open with something SPECIFIC to their industry or role
- One clear problem statement
- One clear value prop
- Soft CTA
- Sound like a peer, not a vendor

Return JSON: {{subject: str, body: str}}""",
        max_tokens=400
    )

def run():
    log.info(f"Apollo Scale Bot — target: {DAILY_TARGET} emails today")
    total_sent = 0
    
    for segment in SEGMENTS:
        prospects = get_segment_prospects(segment)
        log.info(f"Segment [{segment['name']}]: {len(prospects)} prospects")
        
        for p in prospects:
            if total_sent >= DAILY_TARGET: break
            email = p.get("email","")
            if not email: continue
            
            email_data = write_segment_email(p, segment)
            if not email_data or not email_data.get("subject"): continue
            
            # Send
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            if GMAIL_PASS:
                try:
                    msg = MIMEMultipart()
                    msg["From"] = f"S.C. Thomas <{GMAIL_USER}>"
                    msg["To"]   = email
                    msg["Subject"] = email_data["subject"]
                    msg.attach(MIMEText(email_data["body"],"plain"))
                    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
                        smtp.login(GMAIL_USER,GMAIL_PASS)
                        smtp.send_message(msg)
                    total_sent += 1
                    log.info(f"✅ [{segment['name']}] → {email}: {email_data['subject'][:50]}")
                except Exception as e:
                    log.error(f"❌ {email}: {e}")
            time.sleep(2)
    
    log.info(f"Done: {total_sent} emails sent across {len(SEGMENTS)} segments")
    log.info(f"Expected replies (10%): {int(total_sent*.10)}")
    log.info(f"Expected sales (5% of replies): {max(1,int(total_sent*.005))}/day")

if __name__ == "__main__":
    run()
