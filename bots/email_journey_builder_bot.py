#!/usr/bin/env python3
"""
Email Journey Builder Bot — Visual journey automation engine.
Highest ROI Phase 1 component. Takes contacts at each funnel stage
and runs them through the correct nurture sequence automatically.

Journeys:
  1. COLD → WARM:      First contact → value sequence (7 days)
  2. WARM → HOT:       Engaged → proposal trigger (5 days)
  3. HOT → CUSTOMER:   Demo booked → close sequence (3 days)
  4. CUSTOMER → LOYAL: Post-purchase onboarding + upsell (30 days)
  5. LOST → RE-ENGAGE: Inactive 60 days → win-back (7 days)

Runs daily. Each contact advances one step per day.
Apollo sends the emails. Supabase tracks progress.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, advance_stage
    from agents.cold_outreach_agent import write_cold_email, select_offer, NYSR_OFFERS
except Exception as e:
    print(f"Import partial: {e}")
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
    def write_cold_email(c,o,t,a): return {"subject":"","body":""}
    def select_offer(c): return {}

import urllib.request, urllib.parse
log = logging.getLogger(__name__)

APOLLO_KEY    = os.environ.get("APOLLO_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

JOURNEYS = {
    "cold_to_warm": {
        "trigger_stage":   "LEAD",
        "exit_stage":      "PROSPECT",
        "days":            7,
        "goal":            "Get reply or click",
        "steps": [
            {"day":1, "angle":"problem_aware",  "channel":"email"},
            {"day":3, "angle":"value_add",       "channel":"email"},
            {"day":5, "angle":"case_study",      "channel":"linkedin"},
            {"day":7, "angle":"breakup_almost",  "channel":"email"},
        ]
    },
    "warm_to_hot": {
        "trigger_stage":   "PROSPECT",
        "exit_stage":      "QUALIFIED",
        "days":            5,
        "goal":            "Book discovery call",
        "steps": [
            {"day":1, "angle":"value_add",      "channel":"email"},
            {"day":2, "angle":"case_study",     "channel":"email"},
            {"day":4, "angle":"book_call",      "channel":"email"},
            {"day":5, "angle":"final_breakup",  "channel":"email"},
        ]
    },
    "hot_to_customer": {
        "trigger_stage":   "QUALIFIED",
        "exit_stage":      "PROPOSAL",
        "days":            3,
        "goal":            "Send proposal + book closing call",
        "steps": [
            {"day":1, "angle":"proposal_send",  "channel":"email"},
            {"day":2, "angle":"proposal_follow","channel":"email"},
            {"day":3, "angle":"closing_urgency","channel":"email"},
        ]
    },
    "onboarding": {
        "trigger_stage":   "CLOSED_WON",
        "exit_stage":      "CLOSED_WON",
        "days":            30,
        "goal":            "Activate + upsell within 30 days",
        "steps": [
            {"day":1,  "angle":"welcome_access",    "channel":"email"},
            {"day":3,  "angle":"quick_win_tip",      "channel":"email"},
            {"day":7,  "angle":"first_result_check", "channel":"email"},
            {"day":14, "angle":"upgrade_suggestion", "channel":"email"},
            {"day":21, "angle":"referral_ask",       "channel":"email"},
            {"day":30, "angle":"renewal_reminder",   "channel":"email"},
        ]
    },
    "win_back": {
        "trigger_stage":   "CLOSED_LOST",
        "exit_stage":      "PROSPECT",
        "days":            7,
        "goal":            "Re-engage dormant leads",
        "steps": [
            {"day":1, "angle":"checking_in",       "channel":"email"},
            {"day":3, "angle":"new_offer_update",  "channel":"email"},
            {"day":7, "angle":"final_win_back",    "channel":"email"},
        ]
    },
}

def write_journey_email(contact: dict, journey_key: str, step: dict, offer: dict) -> dict:
    """Write a journey-specific email using Claude."""
    journey = JOURNEYS[journey_key]
    angle   = step["angle"]
    first   = (contact.get("name","") or "").split()[0] or "there"
    co      = contact.get("company","your company")

    system = "You are an expert email copywriter for B2B SaaS. Write high-converting nurture emails."
    prompt = f"""Journey: {journey_key} | Goal: {journey["goal"]}
Step angle: {angle} | Day: {step["day"]} of {journey["days"]}
Contact: {first} | {contact.get("title","")} at {co} | Industry: {contact.get("industry","")}
Offer: {offer.get("name","ProFlow AI")} — {offer.get("hook","")}

Write a {angle}-angle email for this journey step.
Rules:
- problem_aware: surface their pain, no pitch yet
- value_add: give them something genuinely useful (tip, resource, insight)
- case_study: "a client like you" story with specific outcome
- breakup_almost: "I won't bother you again unless..." 
- book_call: specific calendar link ask with clear value of the call
- proposal_send: "here's what I put together for you"
- closing_urgency: price goes up Friday / spot filling
- welcome_access: warm, excited onboarding with first steps
- upgrade_suggestion: "based on your usage, here's what's next"
- referral_ask: genuine, low-pressure referral request
- checking_in: casual re-engagement after silence
- new_offer_update: "since we last spoke, we added X"
- final_win_back: last-chance offer with clear expiry

Return JSON: {{"subject":"...","body":"...","key_message":"1 sentence"}}"""

    return claude_json(system, prompt, max_tokens=500) or {
        "subject": f"Quick note, {first}",
        "body": f"Hi {first},\n\nJust checking in on you.\n\nBest,\nSean",
        "key_message": "Nurture touchpoint"
    }

def get_contacts_for_journey(journey_key: str) -> list:
    journey    = JOURNEYS[journey_key]
    stage      = journey["trigger_stage"]
    max_days   = journey["days"]
    cutoff_new = (datetime.utcnow() - timedelta(days=max_days+1)).isoformat()

    if journey_key == "win_back":
        # Re-engage CLOSED_LOST contacts older than 60 days
        cutoff = (datetime.utcnow() - timedelta(days=60)).isoformat()
        return supabase_request("GET","contacts",
            query=f"?stage=eq.{stage}&stage_changed_at=lt.{cutoff}&journey_key=is.null&order=score.desc&limit=20"
        ) or []
    else:
        return supabase_request("GET","contacts",
            query=f"?stage=eq.{stage}&score=gte.35&order=score.desc&limit=30"
        ) or []

def log_journey_step(contact_id: str, journey_key: str, step_num: int, email: dict):
    supabase_request("POST","journey_steps",{
        "contact_id":  contact_id,
        "journey_key": journey_key,
        "step_num":    step_num,
        "subject":     email.get("subject","")[:200],
        "body":        email.get("body","")[:2000],
        "sent_at":     datetime.utcnow().isoformat(),
    })
    supabase_request("PATCH","contacts",
        data={
            "journey_key":  journey_key,
            "journey_step": step_num,
            "last_contacted": datetime.utcnow().isoformat(),
        },
        query=f"?id=eq.{contact_id}"
    )

def run():
    log.info("Email Journey Builder starting...")
    total_sent   = 0
    journey_stats = {}

    for journey_key, journey in JOURNEYS.items():
        contacts = get_contacts_for_journey(journey_key)
        log.info(f"  Journey [{journey_key}]: {len(contacts)} contacts")
        sent_this = 0

        for contact in contacts:
            current_step = contact.get("journey_step", 0)
            if current_step >= len(journey["steps"]):
                continue  # Journey complete

            step   = journey["steps"][current_step]
            offer  = select_offer(contact)
            email  = write_journey_email(contact, journey_key, step, offer)

            if contact.get("id"):
                log_journey_step(contact["id"], journey_key, current_step+1, email)

            log.info(f"    → {contact.get('name','?')} | step {current_step+1} | {step['angle']}: {email.get('subject','')[:50]}")
            sent_this  += 1
            total_sent += 1

        journey_stats[journey_key] = sent_this

    # Send Pushover summary
    if PUSHOVER_API and PUSHOVER_USER and total_sent > 0:
        msg = f"📧 Journey Engine: {total_sent} emails queued\n" + "\n".join([f"  {k}: {v}" for k,v in journey_stats.items()])
        try:
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Journey Builder","message":msg}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except: pass

    log.info(f"Journey Builder complete: {total_sent} emails queued across {len(JOURNEYS)} journeys")
    return {"total_sent": total_sent, "journey_stats": journey_stats}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Journey] %(message)s")
    run()
