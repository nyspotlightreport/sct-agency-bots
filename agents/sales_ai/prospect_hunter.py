"""
Prospect Hunter — Template Prospect Lists for 5 Verticals
Generates realistic NYC/LI business prospects with deduplication.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

PROSPECTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sales" / "prospects.json"

# ---------- TEMPLATE PROSPECT LISTS (5 Verticals x 5 Prospects) ----------
TEMPLATE_PROSPECTS = {
    "restaurants_bars": [
        {"first_name": "Marco", "last_name": "Vitale", "business_name": "Vitale's Ristorante", "email": "marco@vitalesristorante.com", "phone": "718-555-0142", "location": "Williamsburg, Brooklyn", "industry": "restaurant"},
        {"first_name": "Diana", "last_name": "Chen", "business_name": "Jade Dragon Kitchen", "email": "diana@jadedragonkitchen.com", "phone": "212-555-0287", "location": "Flushing, Queens", "industry": "restaurant"},
        {"first_name": "Roberto", "last_name": "Mendez", "business_name": "El Fogon Latin Grill", "email": "roberto@elfogongrill.com", "phone": "347-555-0193", "location": "Jackson Heights, Queens", "industry": "restaurant"},
        {"first_name": "Sarah", "last_name": "O'Brien", "business_name": "The Rustic Table", "email": "sarah@therustictable.com", "phone": "516-555-0321", "location": "Huntington, Long Island", "industry": "restaurant"},
        {"first_name": "Kenji", "last_name": "Takahashi", "business_name": "Umami House NYC", "email": "kenji@umamihousenyc.com", "phone": "212-555-0456", "location": "East Village, Manhattan", "industry": "restaurant"},
    ],
    "salons_spas": [
        {"first_name": "Valentina", "last_name": "Rossi", "business_name": "Luxe Glow Salon", "email": "valentina@luxeglowsalon.com", "phone": "718-555-0178", "location": "Park Slope, Brooklyn", "industry": "salon"},
        {"first_name": "Tamika", "last_name": "Williams", "business_name": "Crown & Glory Hair Studio", "email": "tamika@crownandgloryhair.com", "phone": "347-555-0234", "location": "Bed-Stuy, Brooklyn", "industry": "salon"},
        {"first_name": "Yuki", "last_name": "Tanaka", "business_name": "Serenity Spa & Wellness", "email": "yuki@serenityspanyc.com", "phone": "212-555-0567", "location": "Midtown, Manhattan", "industry": "spa"},
        {"first_name": "Priya", "last_name": "Sharma", "business_name": "Radiance Beauty Lounge", "email": "priya@radiancebeautylounge.com", "phone": "516-555-0412", "location": "Garden City, Long Island", "industry": "salon"},
        {"first_name": "Nicole", "last_name": "Fontaine", "business_name": "The Blowout Bar", "email": "nicole@theblowoutbar.com", "phone": "718-555-0389", "location": "Astoria, Queens", "industry": "salon"},
    ],
    "real_estate": [
        {"first_name": "Michael", "last_name": "Torres", "business_name": "Torres Realty Group", "email": "michael@torresrealtygroup.com", "phone": "516-555-0198", "location": "Long Beach, Long Island", "industry": "real estate"},
        {"first_name": "Jennifer", "last_name": "Blackwell", "business_name": "Blackwell Estates", "email": "jennifer@blackwellestates.com", "phone": "718-555-0267", "location": "Brooklyn Heights, Brooklyn", "industry": "real estate"},
        {"first_name": "David", "last_name": "Ostrowski", "business_name": "Ostrowski & Partners Real Estate", "email": "david@ostrowskirealestate.com", "phone": "212-555-0334", "location": "Upper East Side, Manhattan", "industry": "real estate"},
        {"first_name": "Angela", "last_name": "Reeves", "business_name": "Reeves Home Group", "email": "angela@reeveshomegroup.com", "phone": "631-555-0445", "location": "Babylon, Long Island", "industry": "real estate"},
        {"first_name": "Carlos", "last_name": "Vega", "business_name": "Vega Urban Properties", "email": "carlos@vegaurbanproperties.com", "phone": "347-555-0512", "location": "Astoria, Queens", "industry": "real estate"},
    ],
    "law_firms": [
        {"first_name": "Patricia", "last_name": "Martinez", "business_name": "Martinez & Associates", "email": "patricia@martinezlawny.com", "phone": "718-555-0156", "location": "Jackson Heights, Queens", "industry": "law firm"},
        {"first_name": "Anthony", "last_name": "Russo", "business_name": "Russo Legal Group", "email": "anthony@russolegalgroup.com", "phone": "212-555-0223", "location": "Financial District, Manhattan", "industry": "law firm"},
        {"first_name": "Samantha", "last_name": "Goldstein", "business_name": "Goldstein Family Law", "email": "samantha@goldsteinfamilylaw.com", "phone": "516-555-0378", "location": "Great Neck, Long Island", "industry": "law firm"},
        {"first_name": "Raymond", "last_name": "Park", "business_name": "Park & Kim Attorneys", "email": "raymond@parkkimlaw.com", "phone": "718-555-0434", "location": "Flushing, Queens", "industry": "law firm"},
        {"first_name": "Denise", "last_name": "Thompson", "business_name": "Thompson Injury Law", "email": "denise@thompsoninjurylaw.com", "phone": "347-555-0567", "location": "Downtown Brooklyn", "industry": "law firm"},
    ],
    "fitness_studios": [
        {"first_name": "Jason", "last_name": "Rivera", "business_name": "FitBox Studios", "email": "jason@fitboxstudios.com", "phone": "718-555-0189", "location": "Astoria, Queens", "industry": "fitness studio"},
        {"first_name": "Lauren", "last_name": "Mitchell", "business_name": "Elevate Fitness NYC", "email": "lauren@elevatefitnyc.com", "phone": "212-555-0256", "location": "Chelsea, Manhattan", "industry": "fitness studio"},
        {"first_name": "Omar", "last_name": "Hassan", "business_name": "Iron Mind CrossFit", "email": "omar@ironmindcrossfit.com", "phone": "347-555-0323", "location": "Bushwick, Brooklyn", "industry": "fitness studio"},
        {"first_name": "Brittany", "last_name": "Cole", "business_name": "Pure Barre Long Island", "email": "brittany@purebarreli.com", "phone": "516-555-0489", "location": "Manhasset, Long Island", "industry": "fitness studio"},
        {"first_name": "Andre", "last_name": "Jackson", "business_name": "Beast Mode Gym", "email": "andre@beastmodegym.com", "phone": "718-555-0534", "location": "East New York, Brooklyn", "industry": "fitness studio"},
    ],
}


def generate_prospect_id(email: str) -> str:
    """Generate a deterministic ID from email for deduplication."""
    return hashlib.md5(email.lower().encode()).hexdigest()[:12]


def load_prospects() -> dict:
    """Load existing prospects."""
    if PROSPECTS_PATH.exists():
        with open(PROSPECTS_PATH, "r") as f:
            return json.load(f)
    return {"prospects": [], "meta": {"created": datetime.now(timezone.utc).isoformat()}}


def save_prospects(data: dict):
    """Save prospects to disk."""
    PROSPECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def build_prospect_batch(verticals: list[str] | None = None) -> list[dict]:
    """
    Build a batch of prospects from templates.
    Deduplicates against existing prospects.json.
    """
    existing = load_prospects()
    existing_emails = {p["email"].lower() for p in existing.get("prospects", [])}

    if verticals is None:
        verticals = list(TEMPLATE_PROSPECTS.keys())

    new_prospects = []
    for vertical in verticals:
        templates = TEMPLATE_PROSPECTS.get(vertical, [])
        industry_key_map = {
            "restaurants_bars": "restaurants_bars",
            "salons_spas": "salons_spas",
            "real_estate": "real_estate",
            "law_firms": "law_firms",
            "fitness_studios": "fitness_studios",
        }
        industry_key = industry_key_map.get(vertical, vertical)

        for template in templates:
            if template["email"].lower() in existing_emails:
                print(f"[SKIP] Already exists: {template['email']}")
                continue

            prospect = {
                "id": generate_prospect_id(template["email"]),
                "first_name": template["first_name"],
                "last_name": template["last_name"],
                "business_name": template["business_name"],
                "email": template["email"],
                "phone": template["phone"],
                "location": template["location"],
                "industry": template["industry"],
                "industry_key": industry_key,
                "status": "new",
                "followup_step": 0,
                "last_contact": None,
                "last_email_subject": None,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "source": "template_batch",
            }
            new_prospects.append(prospect)
            existing_emails.add(template["email"].lower())

    return new_prospects


def run(verticals: list[str] | None = None, dry_run: bool = False):
    """Main runner: build batch, deduplicate, save."""
    batch = build_prospect_batch(verticals)

    if not batch:
        print("[!] No new prospects to add (all duplicates or empty templates).")
        return 0

    if dry_run:
        print(f"[DRY] Would add {len(batch)} new prospects:")
        for p in batch:
            print(f"  - {p['business_name']} ({p['email']}) [{p['industry_key']}]")
        return len(batch)

    existing = load_prospects()
    existing["prospects"].extend(batch)
    existing["meta"] = existing.get("meta", {})
    existing["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    existing["meta"]["total_prospects"] = len(existing["prospects"])
    save_prospects(existing)

    print(f"[+] Added {len(batch)} new prospects. Total: {len(existing['prospects'])}")
    return len(batch)


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
