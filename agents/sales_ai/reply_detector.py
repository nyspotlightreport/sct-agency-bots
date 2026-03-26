"""
Reply Detector — Intent Detection + Auto-Response Drafting + Pushover Alerts
Monitors for replies to outreach campaigns and classifies intent:
  hot, warm, objection, cold, referral
"""

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN", "")
FROM_EMAIL = "outreach@mail.nyspotlightreport.com"
FROM_NAME = "ProFlow AI Growth Team"
PROSPECTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "prospects.json"
REPLIES_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "replies_log.json"

# ---------- INTENT DETECTION KEYWORDS ----------
INTENT_KEYWORDS = {
    "hot": {
        "keywords": [
            "interested", "sign me up", "let's do it", "ready to start", "send me details",
            "how do i start", "let's go", "i'm in", "count me in", "when can we start",
            "book a call", "schedule a demo", "tell me more", "pricing", "how much",
            "set it up", "let's talk", "sounds good", "i want this", "onboard me"
        ],
        "priority": 1,
        "description": "Prospect is ready to buy or very close to buying"
    },
    "warm": {
        "keywords": [
            "maybe", "could work", "interesting", "not sure yet", "need more info",
            "can you explain", "what exactly", "how does it work", "send me a proposal",
            "let me look at this", "possibly", "considering", "curious", "open to it",
            "depends", "what is the commitment", "any trial", "free trial"
        ],
        "priority": 2,
        "description": "Prospect is curious but not committed — needs nurturing"
    },
    "objection": {
        "keywords": [
            "too expensive", "cannot afford", "not in the budget", "too much",
            "need to think", "talk to my partner", "not the right time", "maybe later",
            "already have", "use something else", "happy with current", "not interested right now",
            "we tried something similar", "burned before", "does not work for us"
        ],
        "priority": 3,
        "description": "Prospect has a specific objection — use Patterson's Book of Arguments"
    },
    "cold": {
        "keywords": [
            "unsubscribe", "remove me", "stop emailing", "not interested", "do not contact",
            "leave me alone", "spam", "take me off", "no thanks", "pass",
            "never contact", "go away", "reported", "block"
        ],
        "priority": 4,
        "description": "Prospect wants no further contact — respect immediately"
    },
    "referral": {
        "keywords": [
            "my friend", "someone who", "you should talk to", "i know someone",
            "let me connect you", "have a colleague", "referral", "recommend you to",
            "my partner might", "another business", "introduce you to"
        ],
        "priority": 1,
        "description": "Prospect is referring someone else — Girard's 250 Rule in action"
    }
}

# ---------- PRE-WRITTEN RESPONSES PER INTENT ----------
RESPONSE_TEMPLATES = {
    "hot": {
        "subject": "Let's get {business_name} set up — here is the next step",
        "body": """Hi {first_name},

That is exactly what I love to hear. Let's get {business_name} set up with ProFlow.

Here is what happens next:
1. Quick 15-minute onboarding call to customize your setup
2. We configure everything within 48 hours
3. You start seeing results within the first week

I have availability tomorrow between 10am-2pm ET. What time works best for you?

If you prefer, you can also reply with your phone number and I will call you directly.

Let's go.

Best,
ProFlow AI Growth Team"""
    },
    "warm": {
        "subject": "Here is the breakdown you asked about, {first_name}",
        "body": """Hi {first_name},

Great to hear from you. I am happy to share more details.

Here is a quick breakdown of what ProFlow does for businesses like {business_name}:

- Automates your customer acquisition and retention
- Generates reviews, manages your online reputation
- Runs 24/7 so you can focus on what you do best

I put together a personalized demo based on {business_name}'s specific situation. It takes 10 minutes and there is zero obligation.

Would you be open to a quick walkthrough this week? I promise it will be worth your time.

Best,
ProFlow AI Growth Team"""
    },
    "objection": {
        "subject": "Totally understand, {first_name} — one quick thought",
        "body": """Hi {first_name},

I completely hear you, and I appreciate your honesty.

Here is the thing — most of our best clients had the exact same concern before they started. The difference is, once they saw the results in the first 30 days, the concern disappeared.

{objection_response}

No pressure at all. But if you are open to it, I would love to show you a 2-minute case study from a business just like yours. Just reply "show me" and I will send it right over.

Best,
ProFlow AI Growth Team"""
    },
    "cold": {
        "subject": None,
        "body": None,
        "action": "Mark as opted_out. Do NOT send any response. Respect their wishes immediately."
    },
    "referral": {
        "subject": "Thank you for the referral, {first_name} — this means a lot",
        "body": """Hi {first_name},

Wow, thank you for thinking of us. Referrals mean the world — it tells me we are doing something right.

I would love to connect with the person you mentioned. Could you share their name and the best way to reach them? Or if it is easier, feel free to forward my last email to them and CC me.

As a thank you, I want to make sure {business_name} gets VIP treatment going forward. You are part of the ProFlow family now.

Best,
ProFlow AI Growth Team"""
    }
}


def detect_intent(reply_text: str) -> dict:
    """Classify reply intent using keyword matching."""
    reply_lower = reply_text.lower()
    scores = {}

    for intent, config in INTENT_KEYWORDS.items():
        matches = [kw for kw in config["keywords"] if kw in reply_lower]
        if matches:
            scores[intent] = {
                "score": len(matches),
                "matched_keywords": matches,
                "priority": config["priority"],
                "description": config["description"]
            }

    if not scores:
        return {"intent": "warm", "confidence": "low", "matched_keywords": [], "description": "No keywords matched — defaulting to warm for follow-up"}

    # Sort by score descending, then priority ascending (1 = highest)
    best = sorted(scores.items(), key=lambda x: (-x[1]["score"], x[1]["priority"]))[0]
    return {
        "intent": best[0],
        "confidence": "high" if best[1]["score"] >= 2 else "medium",
        "matched_keywords": best[1]["matched_keywords"],
        "description": best[1]["description"]
    }


def draft_response(prospect: dict, intent_result: dict) -> dict | None:
    """Draft a response based on detected intent."""
    intent = intent_result["intent"]
    template = RESPONSE_TEMPLATES.get(intent)

    if not template or template.get("subject") is None:
        return None  # cold = no response

    from agents.sales_ai.godmode_sales_ai import handle_objection, get_bundle_for_industry

    industry_key = prospect.get("industry_key", "restaurants_bars")
    objection_response = ""
    if intent == "objection":
        # Map matched keywords to objection type
        obj_type = "need_to_think"
        for kw in intent_result.get("matched_keywords", []):
            if "expensive" in kw or "afford" in kw or "budget" in kw or "much" in kw:
                obj_type = "too_expensive"
            elif "partner" in kw:
                obj_type = "need_to_talk_to_partner"
            elif "time" in kw or "later" in kw:
                obj_type = "not_the_right_time"
            elif "already" in kw or "current" in kw or "something" in kw:
                obj_type = "already_have_solution"
        objection_response = handle_objection(industry_key, obj_type)

    subject = template["subject"].replace("{first_name}", prospect.get("first_name", "there")).replace("{business_name}", prospect.get("business_name", "your business"))
    body = template["body"].replace("{first_name}", prospect.get("first_name", "there")).replace("{business_name}", prospect.get("business_name", "your business")).replace("{objection_response}", objection_response)

    return {"to": prospect.get("email", ""), "from": f"{FROM_NAME} <{FROM_EMAIL}>", "subject": subject, "body": body, "intent": intent}


def send_pushover_alert(prospect: dict, intent_result: dict):
    """Send Pushover notification for replies. Priority 2 + cashregister sound for hot leads."""
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        print(f"[!] Pushover not configured. Alert: {intent_result['intent']} reply from {prospect.get('email')}")
        return

    intent = intent_result["intent"]
    priority = 2 if intent in ("hot", "referral") else 1 if intent == "warm" else 0
    sound = "cashregister" if intent in ("hot", "referral") else "pushover"

    title = f"ProFlow Reply: {intent.upper()} — {prospect.get('business_name', 'Unknown')}"
    message = (
        f"From: {prospect.get('first_name', '')} {prospect.get('last_name', '')} ({prospect.get('email', '')})\n"
        f"Business: {prospect.get('business_name', '')}\n"
        f"Intent: {intent_result['intent']} ({intent_result['confidence']} confidence)\n"
        f"Keywords: {', '.join(intent_result.get('matched_keywords', []))}\n"
        f"Action: {'RESPOND NOW' if intent in ('hot', 'referral') else 'Follow up' if intent == 'warm' else 'Handle objection' if intent == 'objection' else 'Opted out — removed'}"
    )

    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "priority": priority,
        "sound": sound,
    }
    if priority == 2:
        payload["retry"] = 60
        payload["expire"] = 3600

    resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    print(f"[PUSH] Alert sent: {title} | Status: {resp.status_code}")


def load_prospects() -> dict:
    if PROSPECTS_PATH.exists():
        with open(PROSPECTS_PATH, "r") as f:
            return json.load(f)
    return {"prospects": []}


def save_prospects(data: dict):
    with open(PROSPECTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def log_reply(prospect: dict, intent_result: dict, draft: dict | None):
    """Log the reply for tracking."""
    log = []
    if REPLIES_LOG_PATH.exists():
        with open(REPLIES_LOG_PATH, "r") as f:
            log = json.load(f)

    log.append({
        "prospect_id": prospect.get("id"),
        "email": prospect.get("email"),
        "business_name": prospect.get("business_name"),
        "intent": intent_result,
        "draft_sent": draft is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    REPLIES_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPLIES_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def check_and_respond(dry_run: bool = False):
    """
    Main loop: check for replies, classify intent, draft responses, send alerts.
    In production, this would poll Resend webhooks or an inbox.
    For now, it checks prospects with status='replied' and processes them.
    """
    prospects_data = load_prospects()
    prospects = prospects_data.get("prospects", [])
    processed = 0

    for prospect in prospects:
        if prospect.get("status") != "replied":
            continue
        if prospect.get("reply_processed"):
            continue

        reply_text = prospect.get("reply_text", "")
        intent_result = detect_intent(reply_text)

        print(f"\n[REPLY] {prospect.get('business_name')} | Intent: {intent_result['intent']} ({intent_result['confidence']})")
        print(f"  Keywords: {intent_result.get('matched_keywords', [])}")

        # Send Pushover alert
        send_pushover_alert(prospect, intent_result)

        # Handle cold/opt-out
        if intent_result["intent"] == "cold":
            prospect["status"] = "opted_out"
            prospect["reply_processed"] = True
            log_reply(prospect, intent_result, None)
            print(f"  [OPT-OUT] {prospect['email']} removed from all future outreach.")
            processed += 1
            continue

        # Draft response
        draft = draft_response(prospect, intent_result)
        if draft and not dry_run:
            if RESEND_API_KEY:
                headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
                payload = {"from": draft["from"], "to": [draft["to"]], "subject": draft["subject"], "text": draft["body"]}
                resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
                print(f"  [SENT] Response to {draft['to']} | {resp.json()}")
            else:
                print(f"  [DRY] Would respond to {draft['to']} | Subject: {draft['subject']}")
        elif draft:
            print(f"  [DRY] Draft ready for {draft['to']} | Subject: {draft['subject']}")

        prospect["reply_processed"] = True
        log_reply(prospect, intent_result, draft)
        processed += 1

    save_prospects(prospects_data)
    print(f"\n[+] Reply detection complete. {processed} replies processed.")
    return processed


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    check_and_respond(dry_run=dry)
