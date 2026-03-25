#!/usr/bin/env python3
"""
agents/apollo_scale_agent.py — Apollo Scale Lead Agent
Pulls fresh leads from Apollo.io API targeting NYC/LI small business owners.
Deduplicates against existing Supabase contacts and inserts new leads.
"""
import os, json, logging, time
from datetime import datetime, timezone
import urllib.request as urlreq
import urllib.parse

log = logging.getLogger("apollo_scale")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [APOLLO] %(message)s")

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

SEARCH_CONFIG = {
    "person_titles": [
        "Owner", "Founder", "CEO", "President",
        "Managing Director", "Principal", "Partner"
    ],
    "person_locations": [
        "New York, New York, United States",
        "Brooklyn, New York, United States",
        "Queens, New York, United States",
        "Long Island, New York, United States",
        "Manhattan, New York, United States"
    ],
    "organization_num_employees_ranges": ["1,50"],
    "per_page": 50,
    "page": 1,
}

TARGET_INDUSTRIES = [
    "restaurants", "health and wellness", "real estate",
    "legal services", "beauty and personal care", "fitness",
    "retail", "professional services", "medical practice",
    "dental practice", "accounting"
]


def apollo_search(page=1):
    """Search Apollo people API for leads matching our ICP"""
    if not APOLLO_API_KEY:
        log.error("APOLLO_API_KEY not set")
        return []

    url = "https://api.apollo.io/v1/mixed_people/search"
    payload = {
        **SEARCH_CONFIG,
        "page": page,
        "api_key": APOLLO_API_KEY
    }

    try:
        data = json.dumps(payload).encode()
        req = urlreq.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        })
        with urlreq.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())

        people = result.get("people", [])
        log.info("Apollo returned %d people (page %d)", len(people), page)
        return people
    except Exception as e:
        log.error("Apollo search failed: %s", e)
        return []


def get_existing_emails():
    """Fetch all existing contact emails from Supabase for dedup"""
    if not SUPA_URL:
        return set()
    try:
        emails = set()
        offset = 0
        batch_size = 1000
        while True:
            url = f"{SUPA_URL}/rest/v1/contacts?select=email&offset={offset}&limit={batch_size}"
            req = urlreq.Request(url, headers={
                "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"
            })
            with urlreq.urlopen(req, timeout=15) as r:
                rows = json.loads(r.read())
            if not rows:
                break
            for row in rows:
                if row.get("email"):
                    emails.add(row["email"].lower())
            offset += batch_size
            if len(rows) < batch_size:
                break
        log.info("Loaded %d existing emails for dedup", len(emails))
        return emails
    except Exception as e:
        log.warning("Failed to load existing emails: %s", e)
        return set()


def insert_lead(lead_data):
    """Insert a new lead into Supabase contacts table"""
    if not SUPA_URL:
        return False
    try:
        payload = json.dumps(lead_data).encode()
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/contacts",
            data=payload,
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            method="POST"
        )
        urlreq.urlopen(req, timeout=10)
        return True
    except Exception as e:
        log.warning("Insert failed for %s: %s", lead_data.get("email", "?"), e)
        return False


def extract_lead_data(person):
    """Extract structured lead data from Apollo person record"""
    org = person.get("organization", {}) or {}
    return {
        "full_name": person.get("name", ""),
        "email": (person.get("email") or "").lower(),
        "phone": person.get("phone_numbers", [{}])[0].get("sanitized_number", "") if person.get("phone_numbers") else "",
        "company": org.get("name", ""),
        "title": person.get("title", ""),
        "linkedin_url": person.get("linkedin_url", ""),
        "city": person.get("city", ""),
        "state": person.get("state", ""),
        "industry": org.get("industry", ""),
        "company_size": org.get("estimated_num_employees", 0),
        "source": "apollo",
        "nurture_stage": "new",
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    log.info("=== Apollo Scale Agent starting ===")
    now = datetime.now(timezone.utc)

    if not APOLLO_API_KEY:
        log.error("APOLLO_API_KEY not set — aborting")
        return

    # Load existing emails for dedup
    existing_emails = get_existing_emails()

    added = 0
    skipped_dupe = 0
    skipped_no_email = 0
    errors = 0

    # Search up to 2 pages (100 leads max per run)
    for page in range(1, 3):
        people = apollo_search(page=page)
        if not people:
            break

        for person in people:
            lead = extract_lead_data(person)

            if not lead["email"]:
                skipped_no_email += 1
                continue

            if lead["email"] in existing_emails:
                skipped_dupe += 1
                continue

            if insert_lead(lead):
                added += 1
                existing_emails.add(lead["email"])  # Prevent intra-batch dupes
                log.info("Added: %s (%s) at %s", lead["full_name"], lead["title"], lead["company"])
            else:
                errors += 1

        # Rate limit between pages
        if page < 2:
            time.sleep(2)

    log.info("=== Apollo Scale Agent complete ===")
    log.info("Results: %d added, %d dupes skipped, %d no email, %d errors",
             added, skipped_dupe, skipped_no_email, errors)


if __name__ == "__main__":
    main()
