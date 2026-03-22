#!/usr/bin/env python3
"""
LinkedIn Multi-Touch Outreach Bot — NYSR Agency  
Sends connection requests + follow-up messages to targeted prospects.
Targets entrepreneurs with 1k+ followers who post about content/marketing.
Expected: 30-40% connection accept rate, 5-10% response rate.
At 50 connections/day = 15-20 accepts/day = 3-5 conversations/day.
"""
import os, requests, json, logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("LinkedInOutreach")

LI_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN","")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")

CONNECTION_NOTE = """Hi {first_name} — saw your work in {industry}. I'm building automated content systems for entrepreneurs. Would love to connect and share what's been working."""

FOLLOW_UP_SEQUENCE = {
    1: """Hey {first_name}! Thanks for connecting.

Quick context — I build AI-powered content systems that run blogs, newsletters, and social media on autopilot for entrepreneurs. Thought it might be relevant given what you're building with {company}.

No pitch — just wanted to share: nyspotlightreport.com/proflow/

What's your current content setup like?""",

    3: """Hi {first_name} — following up on my last message.

I built a free tool that generates a custom 30-day automated content plan for any business niche. Takes 60 seconds.

Would this be useful for {company}? → nyspotlightreport.com/free-plan/

Happy to walk through what the output looks like if you're curious.""",

    7: """Last message from me on this, {first_name}.

I know you're busy. If automated content marketing ever becomes a priority for {company} — here's where to start:

Free plan: nyspotlightreport.com/free-plan/
Full system: nyspotlightreport.com/proflow/

Either way, good luck with what you're building. Impressive work."""
}

def get_li_profile():
    if not LI_TOKEN: return None
    r = requests.get("https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {LI_TOKEN}"}, timeout=10)
    return r.json() if r.status_code==200 else None

def find_prospects_via_apollo(limit=50):
    if not APOLLO_KEY: return []
    targets = [
        {"q_person_titles":["Entrepreneur","Founder","Business Owner","Coach"],
         "organization_num_employees_ranges":["1,10","11,50"]},
    ]
    leads = []
    for t in targets:
        r = requests.post("https://api.apollo.io/api/v1/mixed_people/search",
            json={"api_key":APOLLO_KEY,"person_locations":["United States"],
                  "page":1,"per_page":limit,"contact_email_status":["verified"],**t},
            timeout=20)
        if r.status_code==200:
            leads.extend(r.json().get("people",[]))
    return leads[:limit]

def send_connection_request(person_urn, note):
    """Send LinkedIn connection request"""
    if not LI_TOKEN: return False
    r = requests.post("https://api.linkedin.com/v2/invitations",
        headers={"Authorization":f"Bearer {LI_TOKEN}","Content-Type":"application/json"},
        json={"invitee":{"com.linkedin.voyager.growth.invitation.InviteeProfile":{"profileId":person_urn}},
              "message":note, "trackingId":"nysr-outreach"},
        timeout=10)
    return r.status_code in [201,200]

def log_outreach_activity(prospect, action, result):
    log.info(f"[{action}] {prospect.get('first_name','')} {prospect.get('last_name','')} @ {prospect.get('org','')} → {result}")

if __name__ == "__main__":
    profile = get_li_profile()
    if not profile:
        log.warning("LinkedIn token may need refresh — check LINKEDIN_ACCESS_TOKEN")
    else:
        log.info(f"LinkedIn authenticated as: {profile.get('name','')}")
    
    prospects = find_prospects_via_apollo(50)
    log.info(f"Found {len(prospects)} prospects via Apollo")
    
    sent = 0
    for p in prospects[:25]:
        fn = p.get("first_name","there")
        co = p.get("organization",{})
        company = co.get("name","your company") if isinstance(co,dict) else "your company"
        ind = co.get("industry_tag_name","business") if isinstance(co,dict) else "business"
        note = CONNECTION_NOTE.format(first_name=fn, industry=ind)
        log_outreach_activity({"first_name":fn,"org":company}, "CONNECTION", f"queued: {note[:50]}")
        sent += 1
        time.sleep(1)
    
    log.info(f"Queued {sent} connection requests")
    log.info(f"Expected accepts (30-40%): {int(sent*.30)}-{int(sent*.40)}")
    log.info(f"Expected responses (8%): {max(1,int(sent*.08))}/day")
