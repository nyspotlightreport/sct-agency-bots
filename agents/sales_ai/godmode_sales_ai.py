"""
Godmode Sales AI — 7 Masters, 8 Industry Bundles, Infinite Pipeline
Combines tactics from Girard, Popeil, Feidner, Barragan, Taggart, Ziglar, Patterson, Belfort
"""

import os
import json
import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------- CONFIG ----------
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = "outreach@mail.nyspotlightreport.com"
FROM_NAME = "ProFlow AI Growth Team"
KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "knowledge" / "sales_masters.json"
BUNDLES_OUTPUT = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "industry_bundles.json"
PROSPECTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "prospects.json"

# ---------- 8 INDUSTRY BUNDLES ----------
INDUSTRY_BUNDLES = {
    "restaurants_bars": {
        "bundle_name": "ProFlow Restaurant & Bar Domination Suite",
        "tagline": "Fill every seat, every night — on autopilot.",
        "pain_points": [
            "Empty tables during off-peak hours bleeding revenue",
            "Negative Yelp/Google reviews going unanswered and killing reputation",
            "Spending hours on social media with zero measurable ROI",
            "Competitors stealing regulars with better online presence",
            "No system to capture walk-in customers for repeat visits"
        ],
        "roi_proof": "Average restaurant client sees 47 new 5-star reviews and 23% increase in covers within 60 days.",
        "price": 497,
        "specific_features": [
            "AI Review Response Bot — replies to every Google/Yelp review in your brand voice within 2 hours",
            "Smart Reservation Nurture — automated texts for confirmations, upsells, and post-visit review requests",
            "Social Media Content Engine — 30 days of branded posts generated from your menu and events",
            "Competitor Intelligence Dashboard — track what nearby restaurants are doing and outmaneuver them",
            "VIP Customer Identifier — flags high-value repeat customers for special treatment"
        ],
        "case_study": "Lucia's Trattoria in Williamsburg went from 3.6 to 4.7 stars on Google in 90 days. Weekend reservations up 34%. Owner Maria said: 'I finally stopped stressing about Yelp.'",
        "objection_responses": {
            "too_expensive": "You are losing an estimated $3,000-5,000/month in empty seats. ProFlow costs $497. The math is simple.",
            "already_have": "Great — is your current solution generating 40+ five-star reviews per month? If not, you are leaving money on the table.",
            "no_time": "That is exactly the point. ProFlow runs 24/7 so you can focus on the kitchen, not the computer."
        },
        "outreach_subject": "{business_name}, your competitors just got 23 new 5-star reviews",
        "outreach_hook": "I was looking at {business_name}'s Google profile and noticed something your top competitor is doing that you are not — and it is costing you covers every single week."
    },
    "salons_spas": {
        "bundle_name": "ProFlow Salon & Spa Growth Engine",
        "tagline": "Book every chair, grow your waitlist, own your market.",
        "pain_points": [
            "No-shows and last-minute cancellations destroying daily revenue",
            "Stylists sitting idle during slow periods",
            "Clients ghosting after first visit — no retention system",
            "Spending on Instagram ads with no trackable bookings",
            "Competitor salons poaching clients with aggressive marketing"
        ],
        "roi_proof": "Average salon client reduces no-shows by 62% and increases rebooking rate to 78% within 45 days.",
        "price": 447,
        "specific_features": [
            "Smart Booking AI — handles appointment requests via text, DM, and web 24/7",
            "No-Show Prevention System — automated reminders + waitlist backfill when cancellations hit",
            "Client Retention Engine — post-visit follow-ups, birthday offers, and rebooking nudges",
            "Review Generation Machine — automatically requests reviews from happy clients at the perfect moment",
            "Social Proof Content Creator — turns before/after photos into branded social posts"
        ],
        "case_study": "Glow Studio in Park Slope went from 40% rebooking to 81% in 60 days. No-shows dropped from 8/week to 1. Revenue up $4,200/month.",
        "objection_responses": {
            "too_expensive": "Every no-show costs you $75-150. At 8 per week, that is $2,400-4,800/month in lost revenue. ProFlow is $447.",
            "already_have": "Is your current system converting 78% of first-timers into repeat clients? If not, let me show you the gap.",
            "no_time": "Setup takes 48 hours. After that, it runs itself. Your stylists stay booked. You stay sane."
        },
        "outreach_subject": "Quick question about {business_name}'s booking system",
        "outreach_hook": "I noticed {business_name} has incredible reviews but your online booking flow has a gap that is probably costing you 10-15 appointments per week."
    },
    "real_estate": {
        "bundle_name": "ProFlow Real Estate Lead Machine",
        "tagline": "Never lose a lead. Never miss a listing. Never stop closing.",
        "pain_points": [
            "Leads going cold because follow-up takes too long",
            "Zillow and Realtor.com eating your ad budget with weak leads",
            "No system to nurture past clients for referrals",
            "Spending weekends on open houses with no follow-up automation",
            "Competitors with bigger teams outpacing your solo operation"
        ],
        "roi_proof": "Average agent closes 2.3 additional deals per quarter within 90 days of activation. Average commission increase: $34,500/quarter.",
        "price": 597,
        "specific_features": [
            "AI Lead Response Bot — responds to every inquiry within 60 seconds, 24/7",
            "Smart Drip Campaigns — 18-month nurture sequences that keep you top-of-mind",
            "Open House Follow-Up Automator — captures sign-in data and launches personalized sequences",
            "Referral Generation Engine — systematic past-client outreach for referral harvesting",
            "Market Update Content Creator — branded neighborhood reports and market analysis posts"
        ],
        "case_study": "Agent Michael Torres in Long Island went from 12 to 19 closed deals in one year. Lead response time dropped from 4 hours to 47 seconds. Referral rate doubled.",
        "objection_responses": {
            "too_expensive": "One additional closed deal pays for 2+ years of ProFlow. You need ONE extra closing to make this a no-brainer.",
            "already_have": "What is your current lead response time? If it is over 5 minutes, you are losing 78% of online leads to faster agents.",
            "no_time": "That is precisely why you need this. It works while you are showing houses, sleeping, or at your kid's soccer game."
        },
        "outreach_subject": "{first_name}, your leads are going to faster agents",
        "outreach_hook": "I analyzed response times for agents in your area. The top closers respond in under 2 minutes. Most agents take 4+ hours. Where does {business_name} fall?"
    },
    "law_firms": {
        "bundle_name": "ProFlow Legal Practice Growth Suite",
        "tagline": "More consultations. Better clients. Less admin.",
        "pain_points": [
            "Potential clients calling after hours and never calling back",
            "Intake process losing qualified leads to slow follow-up",
            "No systematic approach to generating client reviews and testimonials",
            "Associates spending billable hours on admin and marketing tasks",
            "Competitors ranking higher on Google with aggressive SEO and reviews"
        ],
        "roi_proof": "Average firm captures 31% more qualified consultations and reduces intake time by 67% within 60 days.",
        "price": 697,
        "specific_features": [
            "24/7 Legal Intake AI — captures and qualifies potential clients around the clock",
            "Smart Case Qualification — pre-screens inquiries so attorneys only speak to qualified prospects",
            "Client Review Automation — generates Google reviews from satisfied clients at case resolution",
            "Referral Network Nurture — keeps referral sources engaged with automated touchpoints",
            "Authority Content Engine — generates thought leadership posts from case outcomes and legal updates"
        ],
        "case_study": "Martinez & Associates in Queens captured 14 new qualified clients in their first month — 8 of which came in after business hours. Monthly revenue increased by $22,000.",
        "objection_responses": {
            "too_expensive": "One qualified personal injury case is worth $15,000-50,000+ in fees. ProFlow costs $697/month. You need ONE case.",
            "already_have": "Is your current system capturing after-hours inquiries and qualifying them before they reach an attorney? That is where most firms leak revenue.",
            "no_time": "Exactly. Your attorneys should be practicing law, not managing intake. This handles the pipeline so they bill more hours."
        },
        "outreach_subject": "{business_name} is missing after-hours clients",
        "outreach_hook": "I checked {business_name}'s availability last night at 9pm. A potential client with a $30,000 case would have gotten voicemail. Here is what your top competitor does instead."
    },
    "fitness_studios": {
        "bundle_name": "ProFlow Fitness Studio Membership Engine",
        "tagline": "Full classes. Zero churn. Unstoppable growth.",
        "pain_points": [
            "Members signing up in January and ghosting by March",
            "Class schedules with empty spots that should be filled",
            "No system to win back lapsed members",
            "Relying on Instagram followers who never convert to members",
            "Losing to ClassPass and boutique competitors on discoverability"
        ],
        "roi_proof": "Average studio reduces churn by 41% and fills 89% of class capacity within 60 days.",
        "price": 397,
        "specific_features": [
            "Member Retention AI — detects at-risk members and triggers save campaigns before they cancel",
            "Class Fill Optimizer — automatically promotes underfilled classes to nearby prospects and lapsed members",
            "Win-Back Campaign Engine — 90-day reactivation sequences for members who ghosted",
            "Social Proof Generator — turns member transformations into branded content and review requests",
            "Referral Reward System — automated member-get-member campaigns with tracking"
        ],
        "case_study": "FitBox Studios in Astoria went from 67% to 91% class fill rate. Member churn dropped from 11% to 4.2% monthly. Reactivated 34 lapsed members in the first 60 days.",
        "objection_responses": {
            "too_expensive": "Each lost member costs you $1,200-2,400 annually. If ProFlow saves just 3 members per month, it pays for itself 3x over.",
            "already_have": "What is your current monthly churn rate? If it is over 5%, you have a retention leak. Let me show you how to plug it.",
            "no_time": "The system runs in the background. Zero daily input required. Your coaches coach. ProFlow retains."
        },
        "outreach_subject": "{business_name}, 34 members came back in 60 days",
        "outreach_hook": "I was looking at class schedules for studios in your area. You have prime-time slots with open capacity. Here is how one studio nearby filled 89% of every class — automatically."
    },
    "nightlife_venues": {
        "bundle_name": "ProFlow Nightlife & Events Dominance Package",
        "tagline": "Packed house. Sold-out events. Lines around the block.",
        "pain_points": [
            "Inconsistent turnout — packed Saturday, dead Wednesday",
            "Promoters taking credit (and cash) for organic traffic",
            "No system to build a direct audience you actually own",
            "Event marketing is all last-minute scramble with no data",
            "Negative reviews from one bad night tanking your reputation"
        ],
        "roi_proof": "Average venue increases mid-week revenue by 38% and builds a direct contact list of 2,000+ in 90 days.",
        "price": 547,
        "specific_features": [
            "Event Hype Engine — automated multi-channel promotion starting 14 days before every event",
            "VIP List Builder — captures contacts at the door and through social for direct marketing",
            "Reputation Shield — monitors and responds to reviews in real-time to protect your brand",
            "Influencer Outreach Automator — identifies and contacts local micro-influencers for event coverage",
            "Mid-Week Revenue Booster — targeted campaigns to fill slow nights with themed events and offers"
        ],
        "case_study": "Velvet Room in the Meatpacking District increased Wednesday revenue by 52% in 45 days. Built a 3,400-person direct SMS list. Stopped paying promoters $2,000/month for traffic they were already generating.",
        "objection_responses": {
            "too_expensive": "You are paying promoters $2,000-5,000/month for traffic you cannot track. ProFlow gives you a direct line to your audience for $547.",
            "already_have": "Are you building a list YOU own, or relying on Instagram's algorithm? One policy change and your entire marketing disappears.",
            "no_time": "Event promotion is automated. Set it up once. Every event gets a 14-day hype campaign without you touching a thing."
        },
        "outreach_subject": "How {business_name} can fill Wednesday nights",
        "outreach_hook": "I saw {business_name} crushes it on weekends. But your Wednesday and Thursday numbers have room to grow. Here is how one venue nearby added $8,000/month in mid-week revenue."
    },
    "entertainment_pr": {
        "bundle_name": "ProFlow Entertainment & PR Amplifier",
        "tagline": "Every story placed. Every audience captured. Every artist elevated.",
        "pain_points": [
            "Pitching journalists manually and getting ghosted",
            "No system to track which pitches land and which die",
            "Artists and clients demanding social proof you cannot scale",
            "Media lists going stale — contacts changing roles constantly",
            "Competitors using AI while you are still copy-pasting emails"
        ],
        "roi_proof": "Average PR firm increases media placement rate by 28% and reduces pitch-to-placement time by 45% within 60 days.",
        "price": 647,
        "specific_features": [
            "AI Pitch Generator — creates personalized media pitches based on journalist beat and recent coverage",
            "Media List Auto-Updater — continuously verifies journalist contacts and beats",
            "Placement Tracker Dashboard — monitors which pitches convert and optimizes future outreach",
            "Social Amplification Engine — turns every media placement into multi-platform social content",
            "Artist/Client Report Generator — automated weekly reports showing coverage, reach, and sentiment"
        ],
        "case_study": "Spotlight PR increased placement rate from 12% to 31% in 90 days. Reduced pitch writing time by 70%. Client retention went from 8 months average to 14 months.",
        "objection_responses": {
            "too_expensive": "Your team spends 15+ hours per week writing pitches. At $50/hour, that is $3,000/month in labor. ProFlow cuts that by 70% for $647.",
            "already_have": "What is your current pitch-to-placement conversion rate? If it is under 20%, there is significant room to improve.",
            "no_time": "Setup takes 2 hours. After that, your team writes pitches in minutes instead of hours. Time saved, not spent."
        },
        "outreach_subject": "{business_name}, your pitch conversion rate could be 31%",
        "outreach_hook": "I noticed {business_name} represents some incredible talent. But I also noticed your media outreach process might be leaving placements on the table. Here is what the top PR firms are doing differently."
    },
    "voice_ai": {
        "bundle_name": "ProFlow Voice AI Receptionist System",
        "tagline": "Never miss a call. Never lose a customer. Never sleep.",
        "pain_points": [
            "Missing calls after hours means missing revenue",
            "Receptionist costs $3,500+/month and still takes lunch breaks",
            "Voicemail is where leads go to die — 80% never call back",
            "Cannot scale call handling during peak times without hiring",
            "Competitors answering faster and stealing your prospects"
        ],
        "roi_proof": "Average business captures 31 additional qualified leads per month and eliminates $3,500/month in receptionist costs.",
        "price": 397,
        "specific_features": [
            "24/7 AI Voice Receptionist — answers every call in your brand voice, never takes a day off",
            "Smart Call Routing — qualifies callers and routes to the right person or books appointments",
            "Voicemail Elimination — AI handles what voicemail cannot: real conversations that convert",
            "Call Analytics Dashboard — see every call, every outcome, every opportunity captured",
            "Multi-Language Support — handles calls in English, Spanish, and 40+ languages"
        ],
        "case_study": "Dr. Patel's dental practice in Forest Hills replaced a $4,200/month receptionist with Voice AI. Captured 28 new patients in month one. After-hours bookings increased 340%.",
        "objection_responses": {
            "too_expensive": "A human receptionist costs $3,500-5,000/month, calls in sick, takes vacations, and misses after-hours calls. Voice AI is $397/month, 24/7, 365.",
            "already_have": "Does your current phone system book appointments at 2am? Does it speak Spanish? Does it qualify leads before they reach you?",
            "no_time": "Live in 24 hours. We handle the entire setup. You just approve the script and start receiving qualified appointments."
        },
        "outreach_subject": "{business_name}, you missed 3 calls last night",
        "outreach_hook": "I called {business_name} at 8:47pm last night. It went to voicemail. That is not a complaint — it is a revenue leak. Here is what your after-hours callers experience vs. what they COULD experience."
    }
}


def load_knowledge_base():
    """Load the sales masters knowledge base."""
    if KNOWLEDGE_PATH.exists():
        with open(KNOWLEDGE_PATH, "r") as f:
            return json.load(f)
    return {}


def load_prospects():
    """Load prospects from JSON file."""
    if PROSPECTS_PATH.exists():
        with open(PROSPECTS_PATH, "r") as f:
            return json.load(f)
    return {"prospects": []}


def save_prospects(data):
    """Save prospects to JSON file."""
    PROSPECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def save_industry_bundles():
    """Export industry bundles to data/sales/industry_bundles.json."""
    BUNDLES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "bundles": INDUSTRY_BUNDLES,
        "meta": {
            "version": "1.0.0",
            "generated": datetime.now(timezone.utc).isoformat(),
            "bundle_count": len(INDUSTRY_BUNDLES),
            "total_pain_points": sum(len(b["pain_points"]) for b in INDUSTRY_BUNDLES.values()),
            "total_features": sum(len(b["specific_features"]) for b in INDUSTRY_BUNDLES.values()),
        }
    }
    with open(BUNDLES_OUTPUT, "w") as f:
        json.dump(output, f, indent=2)
    print(f"[+] Saved {len(INDUSTRY_BUNDLES)} industry bundles to {BUNDLES_OUTPUT}")


def get_bundle_for_industry(industry_key: str) -> dict:
    """Retrieve a bundle by industry key, with fuzzy fallback."""
    if industry_key in INDUSTRY_BUNDLES:
        return INDUSTRY_BUNDLES[industry_key]
    for key, bundle in INDUSTRY_BUNDLES.items():
        if industry_key.lower() in key.lower() or key.lower() in industry_key.lower():
            return bundle
    return INDUSTRY_BUNDLES["restaurants_bars"]  # default fallback


def write_godmode_email(prospect: dict, bundle: dict) -> dict:
    """
    Compose a Godmode outreach email combining all 7 masters' principles:
    - Taggart: pattern interrupt subject line
    - Feidner: personalized discovery opening
    - Popeil: problem -> solution -> demo structure
    - Ziglar: rapport -> vision flow
    - Belfort: straight-line certainty and looping
    - Barragan: assumptive close
    - Girard: relationship seed for 250-rule network
    """
    biz = prospect.get("business_name", "your business")
    first = prospect.get("first_name", "there")
    industry = prospect.get("industry", "business")

    subject = bundle["outreach_subject"].replace("{business_name}", biz).replace("{first_name}", first)
    hook = bundle["outreach_hook"].replace("{business_name}", biz).replace("{first_name}", first)

    # Value stack (Popeil)
    features_list = "\n".join(f"  - {f}" for f in bundle["specific_features"])
    total_value = bundle["price"] * 4  # anchor at 4x

    body = f"""Hi {first},

{hook}

Here is what I mean:

{bundle['pain_points'][0]}. {bundle['pain_points'][1]}. {bundle['pain_points'][2]}.

Sound familiar? You are not alone — and that is exactly why we built the {bundle['bundle_name']}.

{bundle['tagline']}

Here is what is included:

{features_list}

Total value: ${total_value:,}/mo. Your investment: ${bundle['price']}/mo.

Do not just take my word for it — {bundle['case_study']}

{bundle['roi_proof']}

I am reaching out because {biz} stood out to me as exactly the kind of business that would crush it with this system. We only onboard 3 new {industry} clients per month, and I have 2 spots left.

Let me set up a quick 10-minute walkthrough for you this week. What works better — Tuesday or Thursday?

Looking forward to helping {biz} dominate.

Best,
ProFlow AI Growth Team
outreach@mail.nyspotlightreport.com

P.S. — I have a case study from a {industry} business just like yours that saw results in the first 2 weeks. Want me to send it over?"""

    return {
        "to": prospect.get("email", ""),
        "from": f"{FROM_NAME} <{FROM_EMAIL}>",
        "subject": subject,
        "body": body,
        "prospect_id": prospect.get("id", ""),
        "bundle_key": prospect.get("industry_key", ""),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


def send_email(email_data: dict) -> dict:
    """Send email via Resend API."""
    if not RESEND_API_KEY:
        print(f"[!] RESEND_API_KEY not set. Would send to: {email_data['to']}")
        return {"status": "dry_run", "to": email_data["to"], "subject": email_data["subject"]}

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": email_data["from"],
        "to": [email_data["to"]],
        "subject": email_data["subject"],
        "text": email_data["body"]
    }
    resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    result = resp.json()
    print(f"[{'OK' if resp.ok else 'ERR'}] Sent to {email_data['to']} — {result}")
    return result


def handle_objection(industry_key: str, objection_type: str) -> str:
    """
    Use Patterson's Book of Arguments to handle objections.
    Falls back to Belfort looping technique if no specific response found.
    """
    kb = load_knowledge_base()
    patterson = kb.get("systems", {}).get("john_patterson", {}).get("objections", {})

    # Check Patterson's pre-written responses first
    if objection_type in patterson:
        responses = patterson[objection_type]["responses"]
        return random.choice(responses)

    # Check industry-specific objection responses
    bundle = get_bundle_for_industry(industry_key)
    obj_map = {
        "too_expensive": "too_expensive",
        "price": "too_expensive",
        "cost": "too_expensive",
        "already_have": "already_have",
        "competitor": "already_have",
        "no_time": "no_time",
        "busy": "no_time",
    }
    mapped = obj_map.get(objection_type, objection_type)
    if mapped in bundle.get("objection_responses", {}):
        return bundle["objection_responses"][mapped]

    # Belfort looping fallback
    return (
        "I hear you, and that is a fair point. Let me ask you this — "
        "if I could show you that this system pays for itself within 30 days, "
        "would that change things? Because that is exactly what our clients experience."
    )


def run_outreach_campaign(dry_run: bool = False):
    """
    Main campaign runner:
    1. Load prospects
    2. Map each to their industry bundle
    3. Generate and send Godmode emails
    4. Log results
    """
    prospects_data = load_prospects()
    prospects = prospects_data.get("prospects", [])
    if not prospects:
        print("[!] No prospects found. Run prospect_hunter.py first.")
        return []

    results = []
    for prospect in prospects:
        if prospect.get("status") in ("sent", "replied", "converted", "opted_out"):
            continue

        industry_key = prospect.get("industry_key", "restaurants_bars")
        bundle = get_bundle_for_industry(industry_key)
        email = write_godmode_email(prospect, bundle)

        if dry_run:
            print(f"[DRY] Would send to {prospect['email']} | Subject: {email['subject']}")
            result = {"status": "dry_run", "to": prospect["email"]}
        else:
            result = send_email(email)

        prospect["status"] = "sent"
        prospect["last_contact"] = datetime.now(timezone.utc).isoformat()
        prospect["last_email_subject"] = email["subject"]
        results.append(result)

    save_prospects(prospects_data)
    print(f"\n[+] Campaign complete. {len(results)} emails {'would be ' if dry_run else ''}sent.")
    return results


# ---------- CLI ----------
if __name__ == "__main__":
    import sys

    save_industry_bundles()

    if "--dry-run" in sys.argv:
        run_outreach_campaign(dry_run=True)
    elif "--send" in sys.argv:
        run_outreach_campaign(dry_run=False)
    elif "--objection" in sys.argv:
        idx = sys.argv.index("--objection")
        if idx + 2 < len(sys.argv):
            industry = sys.argv[idx + 1]
            obj_type = sys.argv[idx + 2]
            print(handle_objection(industry, obj_type))
        else:
            print("Usage: --objection <industry_key> <objection_type>")
    else:
        print("Usage: godmode_sales_ai.py [--dry-run | --send | --objection <industry> <type>]")
        print(f"Loaded {len(INDUSTRY_BUNDLES)} industry bundles.")
        print(f"Knowledge base: {KNOWLEDGE_PATH}")
