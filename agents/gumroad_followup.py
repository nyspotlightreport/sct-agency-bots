#!/usr/bin/env python3
"""
TRACK 5 - Gumroad Buyer Follow-Up Bot
Checks Gumroad API for new sales, sends welcome emails via Resend,
and queues follow-up emails in Supabase.
"""

import os, json, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "gumroad")
PROCESSED_FILE = os.path.join(DATA_DIR, "processed_sales.json")
FROM_EMAIL = os.getenv("FROM_EMAIL", "hello@myproflow.org")

# Follow-up schedule
FOLLOWUP_SCHEDULE = [
    {"day": 2,  "subject": "Quick tips for your new guide",               "template": "tips"},
    {"day": 5,  "subject": "Unlock even more NYC insider knowledge",      "template": "upsell"},
    {"day": 10, "subject": "Your NYC adventure - we would love feedback", "template": "feedback"},
    {"day": 14, "subject": "Exclusive offer: 20% off our latest guide",   "template": "discount"},
]

TEMPLATES = {
    "welcome": (
        "Hi {name},\n\n"
        "Thank you for purchasing \"{product_name}\"! We are thrilled to have you.\n\n"
        "Your download is ready here: {download_url}\n\n"
        "If you have any questions, just reply to this email.\n\n"
        "Enjoy exploring NYC!\n\n"
        "Best,\nS.C. Thomas\nNY Spotlight Report\n"
    ),
    "tips": (
        "Hi {name},\n\n"
        "Hope you are enjoying \"{product_name}\"! Here are a few quick tips:\n\n"
        "1. Start with the neighborhood guides - they have hidden gems locals love\n"
        "2. Check out the Best Times to Visit sections for each spot\n"
        "3. Save it to your phone for easy access while exploring\n\n"
        "Questions? Just reply to this email.\n\n"
        "Best,\nS.C. Thomas\nNY Spotlight Report\n"
    ),
    "upsell": (
        "Hi {name},\n\n"
        "Since you loved \"{product_name}\", you might also enjoy our other NYC guides:\n\n"
        "- The Ultimate NYC Nightlife Guide\n"
        "- Hidden Brooklyn: Insider Walking Tour\n"
        "- NYC Food Lover Companion\n\n"
        "Check them all out: https://nyspotlightreport.gumroad.com\n\n"
        "Best,\nS.C. Thomas\n"
    ),
    "feedback": (
        "Hi {name},\n\n"
        "It has been about a week since you got \"{product_name}\" - "
        "we would love to hear how it is going!\n\n"
        "Could you take 30 seconds to share your experience?\n\n"
        "Simply reply to this email with your thoughts.\n\n"
        "Thanks so much,\nS.C. Thomas\nNY Spotlight Report\n"
    ),
    "discount": (
        "Hi {name},\n\n"
        "As a thank you for being a valued reader, here is an exclusive "
        "20% off any of our NYC guides.\n\n"
        "Use code INSIDER20 at checkout: https://nyspotlightreport.gumroad.com\n\n"
        "This offer expires in 48 hours - do not miss out!\n\n"
        "Best,\nS.C. Thomas\nNY Spotlight Report\n"
    ),
}


def load_processed_sales():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    return set()


def save_processed_sales(processed_ids):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROCESSED_FILE, "w") as f:
        json.dump({
            "processed_ids": list(processed_ids),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)


def fetch_gumroad_sales():
    if not GUMROAD_ACCESS_TOKEN:
        print("[gumroad_followup] GUMROAD_ACCESS_TOKEN not set")
        return []
    try:
        resp = requests.get(
            "https://api.gumroad.com/v2/sales",
            params={"access_token": GUMROAD_ACCESS_TOKEN},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("sales", [])
        print("[gumroad_followup] API error: {}".format(data))
        return []
    except Exception as e:
        print("[gumroad_followup] Failed to fetch sales: {}".format(e))
        return []


def send_email(to, subject, body):
    if not RESEND_API_KEY:
        print("[gumroad_followup] RESEND_API_KEY not set - skipping send to {}".format(to))
        return False
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": "Bearer {}".format(RESEND_API_KEY)},
            json={"from": FROM_EMAIL, "to": [to], "subject": subject, "text": body},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            print("[gumroad_followup] Email sent to {}: {}".format(to, subject))
            return True
        print("[gumroad_followup] Email failed ({}): {}".format(resp.status_code, resp.text))
        return False
    except Exception as e:
        print("[gumroad_followup] Email error: {}".format(e))
        return False


def queue_followups_supabase(sale, buyer_email, buyer_name, product_name):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[gumroad_followup] Supabase not configured - skipping follow-up queue")
        return
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer {}".format(SUPABASE_KEY),
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    now = datetime.now(timezone.utc)
    for followup in FOLLOWUP_SCHEDULE:
        send_at = now + timedelta(days=followup["day"])
        template_key = followup["template"]
        body = TEMPLATES.get(template_key, "").format(
            name=buyer_name,
            product_name=product_name,
            download_url=sale.get("download_url", ""),
        )
        row = {
            "sale_id": sale.get("id", ""),
            "buyer_email": buyer_email,
            "buyer_name": buyer_name,
            "product_name": product_name,
            "subject": followup["subject"],
            "body": body,
            "send_at": send_at.isoformat(),
            "status": "queued",
            "template": template_key,
            "created_at": now.isoformat(),
        }
        try:
            resp = requests.post(
                "{}/rest/v1/follow_up_queue".format(SUPABASE_URL),
                headers=headers, json=row, timeout=15,
            )
            if resp.status_code in (200, 201, 204):
                print("[gumroad_followup] Queued Day {} follow-up for {}".format(
                    followup["day"], buyer_email))
            else:
                print("[gumroad_followup] Supabase error: {} {}".format(
                    resp.status_code, resp.text))
        except Exception as e:
            print("[gumroad_followup] Supabase queue error: {}".format(e))


def process_new_sales():
    """Main: check for new Gumroad sales and process them."""
    processed_ids = load_processed_sales()
    sales = fetch_gumroad_sales()
    stats = {"total_sales": len(sales), "new_sales": 0, "welcome_sent": 0, "followups_queued": 0}
    for sale in sales:
        sale_id = sale.get("id", "")
        if not sale_id or sale_id in processed_ids:
            continue
        stats["new_sales"] += 1
        buyer_email = sale.get("email", "")
        buyer_name = sale.get("full_name", buyer_email.split("@")[0] if buyer_email else "Friend")
        product_name = sale.get("product_name", "NYC Guide")
        download_url = sale.get("download_url", "")
        welcome_body = TEMPLATES["welcome"].format(
            name=buyer_name, product_name=product_name, download_url=download_url)
        if send_email(buyer_email,
                      "Welcome! Your copy of \"{}\" is ready".format(product_name),
                      welcome_body):
            stats["welcome_sent"] += 1
        queue_followups_supabase(sale, buyer_email, buyer_name, product_name)
        stats["followups_queued"] += len(FOLLOWUP_SCHEDULE)
        processed_ids.add(sale_id)
    save_processed_sales(processed_ids)
    print("\n[gumroad_followup] Stats: {}".format(json.dumps(stats, indent=2)))
    return stats


if __name__ == "__main__":
    print("=" * 60)
    print("TRACK 5 - Gumroad Buyer Follow-Up")
    print("=" * 60)
    process_new_sales()
