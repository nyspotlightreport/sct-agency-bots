#!/usr/bin/env python3
"""
Partnership Outreach Bot — NYSR Agency
Finds and contacts complementary businesses for:
- Revenue share partnerships ($500-2,000/referral)
- Newsletter ad swaps (grow subscribers fast)
- Bundle deals (combined product offerings)
- Affiliate partnerships (30% both ways)

Targets: newsletter operators, coaches, course creators,
         Beehiiv newsletters, SaaS tools, marketing tools.
"""
import os, requests, logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("PartnershipBot")

GMAIL_USER = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASS","")
BH_KEY     = os.environ.get("BEEHIIV_API_KEY","")

PARTNERSHIP_TARGETS = [
    # Newsletter partners (ad swap = mutual subscriber growth)
    {"type":"newsletter_swap",  "email":"hello@morningbrew.com",   "name":"Morning Brew",       "size":"4M"},
    {"type":"newsletter_swap",  "email":"contact@thehustle.co",    "name":"The Hustle",          "size":"2M"},
    # Tools with affiliate programs
    {"type":"affiliate_partner","email":"partners@beehiiv.com",    "name":"Beehiiv",             "commission":"50%"},
    {"type":"affiliate_partner","email":"affiliates@convertkit.com","name":"ConvertKit",          "commission":"30%"},
    # Coaching/course creators who need content systems
    {"type":"revenue_share",    "email":"info@buildyourlist.com",   "name":"List Building coaches","deal":"20% rev share"},
    {"type":"bundle_deal",      "email":"support@gumroad.com",      "name":"Gumroad ecosystem",  "deal":"product bundles"},
]

PARTNERSHIP_EMAILS = {
    "newsletter_swap": {
        "subject": "Newsletter collaboration idea — {partner_name} x NY Spotlight Report",
        "body": """Hi,

I run NY Spotlight Report, a newsletter on passive income, content automation, and entrepreneurship. Currently at {our_size} subscribers and growing at ~50/week.

I'd love to explore a newsletter swap — we feature your newsletter to our audience, you feature ours to yours. Typical swaps in our space drive 100-400 new subscribers per feature.

Our audience: entrepreneurs, side hustlers, and content creators (25-45 demographic, 60% US).

Would this be worth a quick conversation? Happy to share our engagement metrics.

— S.C. Thomas
NY Spotlight Report (nyspotlightreport.com)
{subscriber_count} subscribers | {open_rate}% open rate"""
    },
    "revenue_share": {
        "subject": "Revenue share opportunity — automated content for your clients",
        "body": """Hi,

Quick idea that might benefit both of our audiences.

I run ProFlow AI — an automated content system that publishes daily blogs, newsletters, and social media for entrepreneurs. Our clients typically see 3-5x content output within 30 days.

I'm looking for coaching/consulting businesses that serve entrepreneurs who struggle with content. The proposal:

- You refer clients to ProFlow AI
- You earn 30% recurring commission (average $89-599/month per client, for life)
- We handle onboarding, support, and delivery entirely
- Your clients get more content output than they could produce manually

This works well when you already advise clients on marketing/growth but don't offer content execution.

Worth a 15-minute call to see if there's a fit?

— S.C. Thomas | NY Spotlight Report
nyspotlightreport.com/proflow/"""
    },
}

def send_partnership_email(to, subject, body, partner_name):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    if not GMAIL_PASS:
        log.info(f"[DRAFT] Partnership email to {partner_name}: {subject}")
        return True
    msg = MIMEMultipart()
    msg["From"] = f"S.C. Thomas <{GMAIL_USER}>"
    msg["To"]   = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body,"plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        log.info(f"✅ Partnership email → {partner_name} ({to})")
        return True
    except Exception as e:
        log.error(f"❌ {partner_name}: {e}")
        return False

if __name__ == "__main__":
    log.info(f"Partnership targets: {len(PARTNERSHIP_TARGETS)}")
    for target in PARTNERSHIP_TARGETS[:3]:
        ptype = target["type"]
        if ptype in PARTNERSHIP_EMAILS:
            tmpl = PARTNERSHIP_EMAILS[ptype]
            subj = tmpl["subject"].format(partner_name=target["name"])
            body = tmpl["body"].format(
                partner_name=target["name"],
                our_size="5,000+",
                subscriber_count="5,000+",
                open_rate="42"
            )
            send_partnership_email(target["email"], subj, body, target["name"])
            time.sleep(3)
    log.info("Partnership outreach complete")
