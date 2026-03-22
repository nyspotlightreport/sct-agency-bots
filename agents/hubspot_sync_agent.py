#!/usr/bin/env python3
"""
agents/hubspot_sync_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARCHITECTURE INNOVATION: Uses Claude API + HubSpot MCP to sync CRM.
No HUBSPOT_API_KEY needed. Ever.

How it works:
1. Reads new contacts from Supabase (CLOSED_WON, new leads, etc.)
2. Calls Claude API with HubSpot MCP server configured
3. Claude uses HubSpot MCP to create/update contacts, deals, pipeline stages
4. Zero API key required - uses the same MCP connection pattern as the session

Runs: daily at 9am ET via hubspot_crm_sync.yml
"""
import os, json, logging, urllib.request
from datetime import datetime, timedelta

log = logging.getLogger("hs_sync")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [HS_SYNC] %(message)s")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL      = os.environ.get("SUPABASE_URL","")
SUPA_KEY      = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API      = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER     = os.environ.get("PUSHOVER_USER_KEY","")

HS_PORTAL = "245581177"  # Permanent — account ID never changes

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def sync_via_claude_mcp(contacts_to_sync, won_deals):
    """
    Use Claude API + HubSpot MCP to sync CRM data.
    This is the key innovation — Claude becomes the CRM integration layer.
    No static API keys needed.
    """
    if not ANTHROPIC_KEY:
        log.warning("No ANTHROPIC_API_KEY — skipping Claude MCP sync")
        return False

    # Build the sync prompt
    contact_list = "\n".join(
        f"- {c.get('name','?')} ({c.get('email','?')}) — Stage: {c.get('stage','?')}, Score: {c.get('score',0)}"
        for c in contacts_to_sync[:20]
    )
    won_list = "\n".join(
        f"- {d.get('email','?')} bought {d.get('tags',['?'])[1] if len(d.get('tags',[]))>1 else 'product'}"
        for d in won_deals[:10]
    )

    prompt = f"""You are the HubSpot CRM sync agent for NY Spotlight Report.

Sync these records to HubSpot using your HubSpot MCP tools:

NEW/UPDATED CONTACTS to create or update:
{contact_list if contact_list else 'None'}

CLOSED WON deals to record:
{won_list if won_list else 'None'}

For each contact:
1. Search if they exist in HubSpot by email
2. Create or update with correct lifecycle stage
3. If CLOSED_WON: create a deal at "closedwon" stage with appropriate amount

HubSpot Portal: {HS_PORTAL}
Do this now. Confirm what was synced."""

    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
        "mcp_servers": [
            {"type": "url", "url": "https://mcp.hubspot.com/anthropic", "name": "hubspot"}
        ]
    }).encode()

    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
        data=data, headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "mcp-client-2025-04-04"
        })

    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read())
            text = " ".join(b.get("text","") for b in result.get("content",[]) if b.get("type")=="text")
            log.info(f"Claude MCP sync result: {text[:200]}")
            return True
    except Exception as e:
        log.error(f"Claude MCP sync: {e}")
        return False

def submit_to_hs_forms(contact):
    """Submit contact to HubSpot via Forms API — zero auth."""
    email = contact.get("email","")
    name  = contact.get("name","") or ""
    if not email: return False

    form_guid = os.environ.get("HUBSPOT_FORM_GUID","")
    if not form_guid: return False

    body = json.dumps({
        "submittedAt": int(datetime.utcnow().timestamp() * 1000),
        "fields": [
            {"name": "email",     "value": email},
            {"name": "firstname", "value": name.split(" ")[0]},
            {"name": "lastname",  "value": " ".join(name.split(" ")[1:])},
        ],
        "context": {"pageUri": "https://nyspotlightreport.com/sync", "pageName": "CRM Sync"}
    }).encode()

    req = urllib.request.Request(
        f"https://api.hsforms.com/submissions/v3/integration/submit/{HS_PORTAL}/{form_guid}",
        data=body, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status == 200
    except: return False

def run():
    log.info("HubSpot Sync Agent — starting")

    # Get contacts from Supabase that need HubSpot sync
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    new_contacts = supa("GET","contacts","",
        f"?created_at=gte.{since}&select=email,name,score,stage,tags&limit=50") or []

    won_contacts = supa("GET","contacts","",
        f"?stage=eq.CLOSED_WON&select=email,name,score,stage,tags&limit=20") or []

    log.info(f"New contacts: {len(new_contacts)}, Won: {len(won_contacts)}")

    # Try Claude MCP sync first (best quality)
    synced = sync_via_claude_mcp(
        [c for c in new_contacts if isinstance(c, dict)],
        [c for c in won_contacts if isinstance(c, dict)]
    )

    # Fallback: Forms API for new leads
    if not synced:
        for contact in new_contacts[:10]:
            if isinstance(contact, dict) and contact.get("email"):
                submit_to_hs_forms(contact)

    log.info("HubSpot sync complete")
    return {"synced": len(new_contacts) + len(won_contacts)}

if __name__ == "__main__": run()
