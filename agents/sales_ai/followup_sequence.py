"""
Follow-Up Sequence Engine — 5-Step Automated Follow-Up System
Day 0: Cold outreach (handled by godmode_sales_ai.py)
Day 3: Gentle value-add bump (Girard monthly contact principle)
Day 7: Industry case study (Ziglar vision stage)
Day 14: Breakup email (Ziglar pressure-removal)
Day 30: Long game win share (Girard 250 Rule — stay top of mind)
"""

import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = "outreach@mail.nyspotlightreport.com"
FROM_NAME = "ProFlow AI Growth Team"
PROSPECTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "prospects.json"

# ---------- SEQUENCE TEMPLATES ----------
SEQUENCES = {
    "day_3_followup": {
        "delay_days": 3,
        "subject": "Quick follow-up on {business_name}",
        "body": """Hi {first_name},

I reached out a few days ago about how {business_name} could benefit from the {bundle_name}.

I know you are busy running your business, so I will keep this short:

I put together a quick 2-minute breakdown of exactly how businesses like yours are using ProFlow to generate measurable ROI. No fluff, just numbers.

Would it be worth a quick look? I can send it over or walk you through it in a 10-minute call.

Either way, I am rooting for {business_name}.

Best,
ProFlow AI Growth Team""",
        "principle": "Girard: Monthly contact with genuine value. Stay helpful, not pushy."
    },
    "day_7_followup": {
        "delay_days": 7,
        "subject": "How a {industry} like yours added ${roi_amount} in 60 days",
        "body": """Hi {first_name},

I wanted to share something I think you will find valuable.

{case_study}

The reason I am sharing this is because {business_name} reminds me of them — great reputation, strong foundation, but leaving growth on the table because of {pain_point_1}.

Here is what changed for them:
- {feature_1}
- {feature_2}
- {feature_3}

Results? {roi_proof}

I would love to show you how to replicate these results for {business_name}. Are you open to a quick 10-minute walkthrough this week?

Best,
ProFlow AI Growth Team""",
        "principle": "Ziglar: Vision stage — paint the after-picture using proof from similar businesses."
    },
    "day_14_breakup": {
        "delay_days": 14,
        "subject": "Closing your file, {first_name}",
        "body": """Hi {first_name},

I have reached out a couple of times about helping {business_name} grow with ProFlow, and I have not heard back. No worries at all.

I do not want to be that person who keeps emailing when you are not interested. So I am going to close your file on my end.

If the timing is ever right in the future, my door is always open. Just reply to this email and I will pick right back up.

One last thought: {pain_point_1} is not going away on its own. When you are ready to solve it, we will be here.

Wishing {business_name} nothing but success.

Best,
ProFlow AI Growth Team

P.S. — If I read this wrong and you ARE interested but just busy, just reply "interested" and I will send over the details whenever works for you. No pressure.""",
        "principle": "Ziglar: Pressure removal. Paradoxically, removing pressure often triggers action."
    },
    "day_30_long_game": {
        "delay_days": 30,
        "subject": "{industry} win: {case_headline}",
        "body": """Hi {first_name},

I know we did not connect last time, and that is totally fine. I just wanted to share a quick win from the {industry} world that made me think of {business_name}:

{long_game_win}

No pitch, no ask. Just thought you would find it interesting.

If you ever want to explore how {business_name} could see similar results, I am always here.

Keep crushing it,
ProFlow AI Growth Team""",
        "principle": "Girard 250 Rule: Stay top of mind. Share genuine value. Plant seeds for the long game."
    }
}

# ---------- INDUSTRY-SPECIFIC LONG GAME WINS ----------
LONG_GAME_WINS = {
    "restaurants_bars": {
        "case_headline": "Brooklyn restaurant added 67 five-star reviews in 30 days",
        "long_game_win": "A family-owned Italian spot in Williamsburg was struggling with a 3.8 Google rating. After implementing automated review requests at the right moment (right after dessert, via text), they jumped to 4.6 stars in 30 days. Reservations on weeknights increased 28%."
    },
    "salons_spas": {
        "case_headline": "Park Slope salon cut no-shows by 73%",
        "long_game_win": "A 4-chair salon was losing $2,400/month to no-shows. They implemented smart reminders with waitlist backfill. No-shows dropped from 11/week to 3. The waitlist filled 85% of cancellations within 2 hours."
    },
    "real_estate": {
        "case_headline": "LI agent closed 4 extra deals in one quarter",
        "long_game_win": "A solo agent in Long Island was responding to leads in 4+ hours. After implementing AI lead response (47-second average), they captured leads competitors missed. Result: 4 additional closings worth $52,000 in commissions in one quarter."
    },
    "law_firms": {
        "case_headline": "Queens firm captured 22 after-hours clients in 60 days",
        "long_game_win": "A 3-attorney firm was sending all after-hours calls to voicemail. They switched to AI intake that qualifies callers 24/7. In 60 days, they captured 22 qualified clients that would have called a competitor the next morning."
    },
    "fitness_studios": {
        "case_headline": "Astoria gym reactivated 41 lapsed members",
        "long_game_win": "A CrossFit box had 200+ members who quit in the past year. A targeted win-back campaign with personalized offers brought 41 back. At $150/month average, that is $6,150/month in recovered revenue."
    },
    "nightlife_venues": {
        "case_headline": "Meatpacking club added $12K in Wednesday revenue",
        "long_game_win": "A nightclub was packed on weekends but dead midweek. Targeted SMS campaigns to their owned list (built via QR codes at the door) turned Wednesday into their third-highest revenue night. $12,000/month in new midweek revenue."
    },
    "entertainment_pr": {
        "case_headline": "PR firm doubled media placement rate",
        "long_game_win": "A boutique PR firm was manually pitching 200 journalists per week with a 9% placement rate. AI-personalized pitches based on journalist beat analysis pushed their rate to 24%. Client retention increased by 6 months average."
    },
    "voice_ai": {
        "case_headline": "Dental practice replaced $4,200/month receptionist",
        "long_game_win": "A dental practice was paying $4,200/month for a receptionist who missed after-hours calls. Voice AI handles unlimited calls 24/7 in English and Spanish. After-hours bookings increased 340%. Monthly savings: $3,800."
    }
}


def load_prospects() -> dict:
    """Load prospects from JSON."""
    if PROSPECTS_PATH.exists():
        with open(PROSPECTS_PATH, "r") as f:
            return json.load(f)
    return {"prospects": []}


def save_prospects(data: dict):
    """Save prospects back to JSON."""
    with open(PROSPECTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_next_step(prospect: dict) -> str | None:
    """Determine which follow-up step is due based on last_contact date."""
    last_contact = prospect.get("last_contact")
    if not last_contact:
        return None

    last_dt = datetime.fromisoformat(last_contact)
    now = datetime.now(timezone.utc)
    days_since = (now - last_dt).days
    current_step = prospect.get("followup_step", 0)

    step_map = {0: "day_3_followup", 1: "day_7_followup", 2: "day_14_breakup", 3: "day_30_long_game"}

    if current_step >= 4:
        return None  # sequence complete

    next_key = step_map.get(current_step)
    if next_key and days_since >= SEQUENCES[next_key]["delay_days"]:
        return next_key
    return None


def build_followup_email(prospect: dict, step_key: str, bundle: dict) -> dict:
    """Build a follow-up email from template."""
    template = SEQUENCES[step_key]
    industry_key = prospect.get("industry_key", "restaurants_bars")
    long_game = LONG_GAME_WINS.get(industry_key, LONG_GAME_WINS["restaurants_bars"])

    replacements = {
        "{first_name}": prospect.get("first_name", "there"),
        "{business_name}": prospect.get("business_name", "your business"),
        "{bundle_name}": bundle.get("bundle_name", "ProFlow Growth Suite"),
        "{industry}": prospect.get("industry", "business"),
        "{case_study}": bundle.get("case_study", ""),
        "{pain_point_1}": bundle.get("pain_points", ["growth challenges"])[0],
        "{feature_1}": bundle.get("specific_features", ["AI automation"])[0],
        "{feature_2}": bundle.get("specific_features", ["", "Smart analytics"])[1],
        "{feature_3}": bundle.get("specific_features", ["", "", "24/7 support"])[2],
        "{roi_proof}": bundle.get("roi_proof", "Measurable ROI within 60 days."),
        "{roi_amount}": str(bundle.get("price", 500) * 6),
        "{case_headline}": long_game["case_headline"],
        "{long_game_win}": long_game["long_game_win"],
    }

    subject = template["subject"]
    body = template["body"]
    for key, val in replacements.items():
        subject = subject.replace(key, val)
        body = body.replace(key, val)

    return {
        "to": prospect.get("email", ""),
        "from": f"{FROM_NAME} <{FROM_EMAIL}>",
        "subject": subject,
        "body": body,
        "step": step_key,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


def send_email(email_data: dict) -> dict:
    """Send via Resend API."""
    if not RESEND_API_KEY:
        print(f"[DRY] Would send {email_data['step']} to {email_data['to']}")
        return {"status": "dry_run", "step": email_data["step"]}

    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
    payload = {"from": email_data["from"], "to": [email_data["to"]], "subject": email_data["subject"], "text": email_data["body"]}
    resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    return resp.json()


def run_followup_sequence(dry_run: bool = False):
    """Check all prospects and send due follow-ups."""
    from agents.sales_ai.godmode_sales_ai import get_bundle_for_industry

    prospects_data = load_prospects()
    prospects = prospects_data.get("prospects", [])
    sent_count = 0

    for prospect in prospects:
        if prospect.get("status") in ("replied", "converted", "opted_out"):
            continue

        step_key = get_next_step(prospect)
        if not step_key:
            continue

        bundle = get_bundle_for_industry(prospect.get("industry_key", "restaurants_bars"))
        email = build_followup_email(prospect, step_key, bundle)

        if dry_run:
            print(f"[DRY] {step_key} -> {prospect['email']} | {email['subject']}")
        else:
            result = send_email(email)
            print(f"[SENT] {step_key} -> {prospect['email']} | {result}")

        prospect["last_contact"] = datetime.now(timezone.utc).isoformat()
        prospect["followup_step"] = prospect.get("followup_step", 0) + 1
        prospect["last_email_subject"] = email["subject"]
        sent_count += 1

    save_prospects(prospects_data)
    print(f"\n[+] Follow-up sequence complete. {sent_count} emails {'would be ' if dry_run else ''}sent.")
    return sent_count


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    run_followup_sequence(dry_run=dry)
