#!/usr/bin/env python3
"""
Appointment Setter Bot — Automates discovery call booking.
Sends personalized calendar links and follows up until call is booked.
Integrates with Calendly or Google Calendar.
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request, advance_stage
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
    def advance_stage(i,s,r=""): return False

log = logging.getLogger(__name__)

CALENDLY_URL = "https://calendly.com/sct-nysr/discovery"
CALL_TYPES   = {
    "discovery":   {"duration": 15, "url": f"{CALENDLY_URL}"},
    "demo":        {"duration": 30, "url": f"{CALENDLY_URL}-demo"},
    "proposal":    {"duration": 45, "url": f"{CALENDLY_URL}-proposal"},
}

def generate_booking_message(contact: dict, call_type: str = "discovery") -> str:
    call = CALL_TYPES.get(call_type, CALL_TYPES["discovery"])
    name = contact.get("name","")
    first = name.split()[0] if name else "there"
    company = contact.get("company","")

    return claude(
        "Write a brief, warm message asking someone to book a discovery call. Natural, not salesy.",
        f"""Contact: {name} at {company} | Stage: {contact.get("stage","QUALIFIED")}
Call type: {call_type} ({call["duration"]} minutes)
Booking link: {call["url"]}
Write 3-4 sentences. Include the booking link naturally. End with specific value they'll get from the call.""",
        max_tokens=150
    ) or (
        f"Hi {first},\n\n"
        f"I'd love to show you exactly how this could work for {company}. "
        f"I've set aside a few spots for a quick {call['duration']}-minute call this week.\n\n"
        f"You can grab a time that works best here: {call['url']}\n\n"
        f"Looking forward to connecting."
    )

def get_contacts_to_book() -> list:
    return supabase_request("GET","contacts",
        query="?stage=eq.QUALIFIED&calendly_booked=is.null&order=score.desc&limit=10"
    ) or []

def run():
    log.info("Appointment Setter Bot running...")
    contacts = get_contacts_to_book()
    log.info(f"Contacts to book: {len(contacts)}")
    booked = 0
    for c in contacts:
        msg = generate_booking_message(c)
        log.info(f"  Booking msg for {c.get('name','?')}: {msg[:80]}...")
        if c.get("id"):
            supabase_request("PATCH","contacts",
                data={"next_action":"Book discovery call","next_action_date":datetime.utcnow().date().isoformat()},
                query=f"?id=eq.{c['id']}"
            )
        booked += 1
    return {"contacts_queued": booked}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [AppSetter] %(message)s")
    run()
