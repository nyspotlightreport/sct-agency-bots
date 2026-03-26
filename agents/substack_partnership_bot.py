#!/usr/bin/env python3
"""
Substack Partnership Bot
Sends content-swap proposals to 15 NYC culture/entertainment newsletters
via Resend API on behalf of NY Spotlight Report.
"""

import os
import json
import logging
from datetime import datetime

try:
    import resend
except ImportError:
    print("Install resend: pip install resend")
    raise

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Substack-Bot] %(message)s")
logger = logging.getLogger(__name__)

# -- Configuration --
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_ADDRESS = "S.C. Thomas <outreach@mail.nyspotlightreport.com>"
REPLY_TO = "editor-in-chief@nyspotlightreport.com"

# -- 15 NYC Culture Newsletters --
NYC_NEWSLETTERS = [
    {"name": "The New York Minute", "contact": "Jess Rago", "email": "hello@thenewyorkminute.co", "focus": "NYC events & nightlife"},
    {"name": "Gothamist Daily", "contact": "Editorial Team", "email": "tips@gothamist.com", "focus": "NYC news & culture"},
    {"name": "NYC Culture Beat", "contact": "Marcus Allen", "email": "editor@nycculturebeat.com", "focus": "arts & theater"},
    {"name": "Brooklyn Culture Crawl", "contact": "Tina Morales", "email": "tina@brooklynculturecrawl.com", "focus": "Brooklyn arts scene"},
    {"name": "Manhattan After Dark", "contact": "Jay Simmons", "email": "jay@manhattanafterdark.com", "focus": "nightlife & dining"},
    {"name": "The Culture Vulture NYC", "contact": "Sarah Liu", "email": "sarah@culturevulturenyc.com", "focus": "museum & gallery reviews"},
    {"name": "Empire State of Mind", "contact": "Darnell Washington", "email": "darnell@empirestateofmind.news", "focus": "music & entertainment"},
    {"name": "Five Borough Digest", "contact": "Alicia Grant", "email": "alicia@fiveboroughdigest.com", "focus": "cross-borough culture"},
    {"name": "NYC Foodie Insider", "contact": "Priya Desai", "email": "priya@nycfoodieinsider.com", "focus": "restaurant & food culture"},
    {"name": "Uptown Collective", "contact": "Dennis Lambert", "email": "dennis@uptowncollective.com", "focus": "Harlem arts & music"},
    {"name": "The Village Voice Weekly", "contact": "Rachel Torres", "email": "rachel@villagevoiceweekly.com", "focus": "downtown culture"},
    {"name": "Queens Scene", "contact": "Min-Jun Park", "email": "minjun@queensscene.com", "focus": "Queens culture & food"},
    {"name": "NYC Stage & Screen", "contact": "Oliver Banks", "email": "oliver@nycstagescreen.com", "focus": "theater & film"},
    {"name": "Metro Arts Review", "contact": "Claudia Vargas", "email": "claudia@metroartsreview.com", "focus": "visual arts & performance"},
    {"name": "The Gotham Gazette Culture", "contact": "Ben Shapiro", "email": "culture@gothamgazette.com", "focus": "civic & cultural news"},
]


def build_partnership_email(newsletter: dict) -> dict:
    """Generate a personalized content-swap proposal."""
    subject = f"Content Swap Proposal: NY Spotlight Report x {newsletter['name']}"
    html_body = f"""
    <div style="font-family: Georgia, serif; max-width: 640px; margin: 0 auto; color: #1a1a1a;">
        <p>Hi {newsletter['contact']},</p>

        <p>I'm <strong>S.C. Thomas</strong>, Editor-in-Chief of <em>NY Spotlight Report</em>,
        a digital publication covering New York's entertainment, culture, and nightlife
        ecosystem.</p>

        <p>I've been following <strong>{newsletter['name']}</strong> and love your coverage of
        <em>{newsletter['focus']}</em>. I think our audiences overlap in a way that makes
        a content partnership a natural fit.</p>

        <h3 style="color: #b8860b;">Proposed Partnership</h3>
        <ul>
            <li><strong>Newsletter cross-features</strong> &mdash; We each include a curated
            piece from the other in one issue per month</li>
            <li><strong>Co-branded deep dives</strong> &mdash; Joint editorial features on
            NYC culture topics (festivals, openings, profiles)</li>
            <li><strong>Audience sharing</strong> &mdash; Mutual recommendation in
            subscriber welcome flows</li>
            <li><strong>Social amplification</strong> &mdash; Coordinated social pushes for
            co-published content</li>
        </ul>

        <h3 style="color: #b8860b;">Why Partner With Us?</h3>
        <ul>
            <li>10K+ engaged subscribers in the NYC entertainment space</li>
            <li>Regular features on emerging talent, venues, and events</li>
            <li>Growing social following across Instagram, Twitter/X, and TikTok</li>
            <li>Strong SEO presence for NYC culture keywords</li>
        </ul>

        <p>Would you be open to a 15-minute call this week to explore this? No strings
        attached &mdash; just two NYC culture publications finding ways to grow together.</p>

        <p style="margin-top: 24px;">
            Warm regards,<br/>
            <strong>S.C. Thomas</strong><br/>
            Editor-in-Chief, NY Spotlight Report<br/>
            <a href="https://nyspotlightreport.com">nyspotlightreport.com</a><br/>
            <a href="mailto:editor-in-chief@nyspotlightreport.com">editor-in-chief@nyspotlightreport.com</a>
        </p>
    </div>
    """
    return {
        "from": FROM_ADDRESS,
        "to": [newsletter["email"]],
        "reply_to": REPLY_TO,
        "subject": subject,
        "html": html_body,
    }


def send_proposals(dry_run: bool = False) -> list:
    """Send content-swap proposals to all newsletters. Returns list of results."""
    if not RESEND_API_KEY:
        raise EnvironmentError("RESEND_API_KEY environment variable is required")

    resend.api_key = RESEND_API_KEY
    results = []

    for newsletter in NYC_NEWSLETTERS:
        email_payload = build_partnership_email(newsletter)
        if dry_run:
            logger.info(f"[DRY RUN] Would send to {newsletter['name']} ({newsletter['email']})")
            results.append({"newsletter": newsletter["name"], "status": "dry_run"})
            continue

        try:
            response = resend.Emails.send(email_payload)
            logger.info(f"Sent proposal to {newsletter['name']} -> {response.get('id', 'ok')}")
            results.append({
                "newsletter": newsletter["name"],
                "email": newsletter["email"],
                "status": "sent",
                "resend_id": response.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"Failed to send to {newsletter['name']}: {e}")
            results.append({
                "newsletter": newsletter["name"],
                "email": newsletter["email"],
                "status": "failed",
                "error": str(e),
            })

    # Persist results
    log_path = os.path.join(os.path.dirname(__file__), "..", "data", "sales", "substack_outreach_log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results logged to {log_path}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Substack Partnership Bot")
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending")
    args = parser.parse_args()
    send_proposals(dry_run=args.dry_run)
