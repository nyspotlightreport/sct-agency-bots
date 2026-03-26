#!/usr/bin/env python3
"""
PR Firm Outreach Agent
Sends personalized editorial coverage pitches to NYC entertainment PR firms
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PR-Outreach] %(message)s")
logger = logging.getLogger(__name__)

# -- Configuration --
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_ADDRESS = "S.C. Thomas <outreach@mail.nyspotlightreport.com>"
REPLY_TO = "editor-in-chief@nyspotlightreport.com"

# -- 20 NYC Entertainment PR Firms --
PR_FIRMS = [
    {"firm": "42West", "contact": "Amanda Silverman", "email": "info@42west.net"},
    {"firm": "Sunshine Sachs Morgan & Lylis", "contact": "Shawn Sachs", "email": "inquiries@sunshinesachs.com"},
    {"firm": "Rogers & Cowan PMK", "contact": "Leslie Sloane", "email": "info@rogersandcowanpmk.com"},
    {"firm": "Shore Fire Media", "contact": "Marilyn Laverty", "email": "info@shorefire.com"},
    {"firm": "Narrative PR", "contact": "Dan Weiss", "email": "hello@narrativepr.com"},
    {"firm": "Lede Company", "contact": "Amanda Silverman", "email": "info@ledecompany.com"},
    {"firm": "BWR Public Relations", "contact": "Dan Klores", "email": "info@bfrpr.com"},
    {"firm": "Falco Ink", "contact": "Jill Fritzo", "email": "info@falcoink.com"},
    {"firm": "ID Public Relations", "contact": "Kelly Brady", "email": "info@idpr.com"},
    {"firm": "Platform PR", "contact": "Sophie Peck", "email": "hello@platformpr.com"},
    {"firm": "The Lede Company", "contact": "Ali Mack", "email": "press@ledecompany.com"},
    {"firm": "DKC Public Relations", "contact": "Sean Cassidy", "email": "info@dkcnews.com"},
    {"firm": "Kovert Creative", "contact": "Chelsea Burcz", "email": "hello@kovertcreative.com"},
    {"firm": "M18 Entertainment", "contact": "Matthew Lesher", "email": "info@m18pr.com"},
    {"firm": "PMK-BNC", "contact": "Chris Robichaud", "email": "press@pmkbnc.com"},
    {"firm": "Slate PR", "contact": "Andy Gelb", "email": "info@slate-pr.com"},
    {"firm": "Press Play PR", "contact": "Elisa Gollin", "email": "hello@pressplaypr.com"},
    {"firm": "Frank PR NYC", "contact": "Frank Costello", "email": "info@frankprnyc.com"},
    {"firm": "Brigade Talent + Brand", "contact": "Brandon Chesbro", "email": "hello@brigadetalent.com"},
    {"firm": "Full Picture", "contact": "Desiree Gruber", "email": "info@fullpicture.com"},
]


def build_pitch_email(firm: dict) -> dict:
    """Generate a personalized editorial coverage pitch for a PR firm."""
    subject = f"Editorial Feature Opportunity -- NY Spotlight Report x {firm['firm']}"
    html_body = f"""
    <div style="font-family: Georgia, serif; max-width: 640px; margin: 0 auto; color: #1a1a1a;">
        <p>Dear {firm['contact']},</p>

        <p>I'm <strong>S.C. Thomas</strong>, Editor-in-Chief of <em>NY Spotlight Report</em>
        &mdash; a digital editorial publication covering New York's entertainment, culture,
        and nightlife scene.</p>

        <p>We're expanding our 2026 editorial calendar and actively seeking partnerships
        with leading PR firms to feature your clients in our coverage. Our audience consists
        of NYC culture enthusiasts, event-goers, and industry decision-makers.</p>

        <h3 style="color: #b8860b;">What We Offer</h3>
        <ul>
            <li><strong>Full editorial features</strong> &mdash; 1,200+ word profiles with
            professional photography</li>
            <li><strong>Event coverage &amp; reviews</strong> &mdash; red carpets, premieres,
            pop-ups, and openings</li>
            <li><strong>Spotlight interviews</strong> &mdash; long-form Q&amp;A pieces with
            talent and creatives</li>
            <li><strong>Newsletter amplification</strong> &mdash; featured placement in our
            weekly digest to 10K+ subscribers</li>
            <li><strong>Social cross-promotion</strong> &mdash; coordinated launch across our
            social channels</li>
        </ul>

        <p>We'd love to discuss how <strong>{firm['firm']}</strong> and NY Spotlight Report
        can collaborate on upcoming features. Would you have 15 minutes this week for a
        quick call?</p>

        <p style="margin-top: 24px;">
            Best regards,<br/>
            <strong>S.C. Thomas</strong><br/>
            Editor-in-Chief, NY Spotlight Report<br/>
            <a href="https://nyspotlightreport.com">nyspotlightreport.com</a><br/>
            <a href="mailto:editor-in-chief@nyspotlightreport.com">editor-in-chief@nyspotlightreport.com</a>
        </p>
    </div>
    """
    return {
        "from": FROM_ADDRESS,
        "to": [firm["email"]],
        "reply_to": REPLY_TO,
        "subject": subject,
        "html": html_body,
    }


def send_pitches(dry_run: bool = False) -> list:
    """Send editorial pitches to all PR firms. Returns list of results."""
    if not RESEND_API_KEY:
        raise EnvironmentError("RESEND_API_KEY environment variable is required")

    resend.api_key = RESEND_API_KEY
    results = []

    for firm in PR_FIRMS:
        email_payload = build_pitch_email(firm)
        if dry_run:
            logger.info(f"[DRY RUN] Would send to {firm['firm']} ({firm['email']})")
            results.append({"firm": firm["firm"], "status": "dry_run"})
            continue

        try:
            response = resend.Emails.send(email_payload)
            logger.info(f"Sent pitch to {firm['firm']} -> {response.get('id', 'ok')}")
            results.append({
                "firm": firm["firm"],
                "email": firm["email"],
                "status": "sent",
                "resend_id": response.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"Failed to send to {firm['firm']}: {e}")
            results.append({
                "firm": firm["firm"],
                "email": firm["email"],
                "status": "failed",
                "error": str(e),
            })

    # Persist results
    log_path = os.path.join(os.path.dirname(__file__), "..", "data", "sales", "pr_outreach_log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results logged to {log_path}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PR Firm Outreach Agent")
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending")
    args = parser.parse_args()
    send_pitches(dry_run=args.dry_run)
