"""
Wiki Agent — Phase 2
AI-powered internal wiki. Auto-generates docs from code, SOPs, FAQs.
Closes Confluence gap. Powers /wiki/ on nyspotlightreport.com.
"""
import os, json, logging, datetime, re
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WIKI] %(message)s")
log = logging.getLogger("wiki")

SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN      = os.environ.get("GH_PAT", "")

import urllib.request, urllib.error

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json", "Prefer": "return=representation"}
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code}")
        return None

def ai(prompt: str, system: str = "You are a technical documentation writer for NYSR Agency.") -> str:
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": 1500,
                        "system": system,
                        "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={
        "Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"AI call failed: {e}")
        return ""

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    return s[:80]

def upsert_page(title: str, content: str, category_slug: str, tags: list = None, author: str = "agency"):
    slug = slugify(title)
    cats = supa("GET", "wiki_categories", query=f"?slug=eq.{category_slug}&select=id&limit=1") or []
    cat_id = cats[0]["id"] if cats else None
    existing = supa("GET", "wiki_pages", query=f"?slug=eq.{slug}&select=id,version&limit=1") or []
    if existing:
        page = existing[0]
        new_ver = page.get("version", 1) + 1
        supa("PATCH", "wiki_pages",
             {"content": content, "version": new_ver, "updated_at": datetime.datetime.utcnow().isoformat()},
             query=f"?id=eq.{page['id']}")
        supa("POST", "wiki_revisions", {"page_id": page["id"], "content": content,
                                         "version": new_ver, "change_note": "Auto-updated by wiki agent"})
        log.info(f"Updated wiki page: {title} (v{new_ver})")
    else:
        supa("POST", "wiki_pages", {"title": title, "slug": slug, "content": content,
                                     "category_id": cat_id, "tags": tags or [], "author": author, "status": "published"})
        log.info(f"Created wiki page: {title}")

def generate_getting_started():
    content = ai(
        "Write a comprehensive 'Getting Started with NYSR AI Agency' wiki page. "
        "Cover: what the system does, the 6 phases, current Phase 1 capabilities (email journeys, SEO, "
        "social scheduling, A/B tests, health scores), how to access dashboards at nyspotlightreport.com, "
        "and how to trigger the cashflow emergency workflow. Write in clean markdown with headers and bullet points. "
        "Tone: professional, clear, practical. Target audience: the Chairman (Sean) or onboarded client."
    )
    if content:
        upsert_page("Getting Started with NYSR AI Agency", content, "getting-started",
                    tags=["onboarding", "overview", "agency"])

def generate_bot_catalog():
    content = ai(
        "Write a 'Bot & Agent Catalog' wiki page for NYSR Agency. "
        "List all major bots and agents organized by department: Sales (11 bots), "
        "Engineering (8 bots), Marketing (social scheduler, SEO audit, conversion optimizer), "
        "Operations (customer health score, email journey builder, knowledge base). "
        "For each bot: name, one-line description, trigger method (scheduled/manual/event), "
        "and what revenue outcome it drives. Use a markdown table format per department."
    )
    if content:
        upsert_page("Bot & Agent Catalog", content, "ai-automation",
                    tags=["bots", "agents", "catalog", "automation"])

def generate_offer_playbook():
    content = ai(
        "Write a 'Sales Offer Playbook' wiki page for NYSR Agency. "
        "Document these 4 offers with full detail: "
        "1) ProFlow AI $97/mo - features, target customer, objections, close script. "
        "2) ProFlow Growth $297/mo - features, upsell path, ROI promise. "
        "3) DFY Setup $1,497 - deliverables, timeline, guarantee. "
        "4) DFY Agency $4,997 - full scope, what's included, client outcome. "
        "Also include the 5 journey sequences: Cold→Warm→Hot→Customer→Win-Back. "
        "Write in clean markdown. Tone: confident, results-focused."
    )
    if content:
        upsert_page("Sales Offer Playbook", content, "sales-revenue",
                    tags=["offers", "sales", "pricing", "proflow"])

def generate_tech_architecture():
    content = ai(
        "Write a 'System Architecture' wiki page for NYSR Agency tech stack. Cover: "
        "1) Infrastructure: Netlify (site+functions), GitHub Actions (88 workflows), Supabase (CRM+data), VPS 204.48.29.16 "
        "2) Languages/frameworks: Python bots, Node.js Netlify functions, GitHub Actions YAML "
        "3) External APIs: Anthropic Claude, Apollo Pro, HubSpot, Stripe, Ahrefs, ElevenLabs, Pushover "
        "4) Data flow: how leads flow from site→Supabase→HubSpot→journey→close "
        "5) Deployment: git push triggers Netlify deploy, GitHub Actions run on schedule "
        "Write technical but accessible markdown. Include a system flow diagram in ASCII art."
    )
    if content:
        upsert_page("System Architecture", content, "technical-docs",
                    tags=["architecture", "infrastructure", "tech-stack"])

def generate_cashflow_sop():
    content = ai(
        "Write a 'Cashflow Emergency SOP' wiki page. "
        "Document exactly how to trigger the cashflow_emergency.yml GitHub Actions workflow. "
        "List all 7 jobs it fires in parallel, what each does, expected outputs, "
        "and how to verify success. Also include the Phase 1 daily revenue levers checklist: "
        "email journeys firing, social posting, A/B tests running, SEO opportunities being created, "
        "health scores being calculated, Tawk.to chat capturing leads. "
        "Include troubleshooting steps for each component. Clean markdown with checkboxes."
    )
    if content:
        upsert_page("Cashflow Emergency SOP", content, "sops",
                    tags=["cashflow", "emergency", "workflow", "sop"])

def generate_faq():
    content = ai(
        "Write a comprehensive FAQ wiki page for NYSR Agency / NY Spotlight Report. "
        "Cover these question categories with 4-5 questions each: "
        "1) About the AI system (what it does, how it works) "
        "2) Pricing & offers (ProFlow AI vs Growth, DFY options) "
        "3) Getting started (how fast, what's included, setup time) "
        "4) Technical (integrations, data security, uptime) "
        "5) Results & ROI (typical outcomes, timeline, guarantees) "
        "Write conversational Q&A markdown. Tone: confident, honest, client-facing."
    )
    if content:
        upsert_page("Frequently Asked Questions", content, "faqs",
                    tags=["faq", "questions", "support"])

def auto_document_new_bots():
    """Scan GitHub for recently added bots and auto-document them."""
    if not GH_TOKEN: return
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/nyspotlightreport/sct-agency-bots/commits?path=bots&per_page=5",
            headers={"Authorization": f"token {GH_TOKEN}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            commits = json.loads(r.read())
        for commit in commits[:2]:
            sha = commit["sha"]
            req2 = urllib.request.Request(
                f"https://api.github.com/repos/nyspotlightreport/sct-agency-bots/commits/{sha}",
                headers={"Authorization": f"token {GH_TOKEN}"})
            with urllib.request.urlopen(req2, timeout=15) as r2:
                detail = json.loads(r2.read())
            for f in detail.get("files", []):
                if f["filename"].startswith("bots/") and f["status"] == "added":
                    bot_name = f["filename"].replace("bots/", "").replace("_bot.py", "").replace("_", " ").title()
                    existing = supa("GET", "wiki_pages", query=f"?title=like.*{bot_name[:20]}*&select=id&limit=1") or []
                    if not existing:
                        doc = ai(f"Write a brief wiki page documenting the '{bot_name}' bot for NYSR Agency. "
                                  f"Include: purpose, how it works, what triggers it, what it outputs, "
                                  f"and what revenue/business impact it drives. 200-300 words, clean markdown.")
                        if doc:
                            upsert_page(f"{bot_name} Bot", doc, "ai-automation", tags=["bot", "automation"])
    except Exception as e:
        log.warning(f"Auto-doc failed: {e}")

def run():
    log.info("=== Wiki Agent Running ===")
    generate_getting_started()
    generate_bot_catalog()
    generate_offer_playbook()
    generate_tech_architecture()
    generate_cashflow_sop()
    generate_faq()
    auto_document_new_bots()
    total = supa("GET", "wiki_pages", query="?select=id&status=eq.published") or []
    log.info(f"Wiki: {len(total)} published pages total")
    log.info("=== Wiki Agent Done ===")

if __name__ == "__main__":
    run()
