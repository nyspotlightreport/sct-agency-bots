#!/usr/bin/env python3
# Pipeline Cleaner Bot - Removes stale leads, deduplicates, enforces data quality.
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":"Pipeline Cleaner","message":msg}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except Exception:  # noqa: bare-except

        pass
def find_stale_leads(days=30):
    cutoff = (datetime.utcnow()-timedelta(days=days)).isoformat()
    return supabase_request("GET","contacts",query=f"?stage=eq.LEAD&created_at=lt.{cutoff}&limit=100") or []

def find_stale_prospects(days=14):
    cutoff = (datetime.utcnow()-timedelta(days=days)).isoformat()
    return supabase_request("GET","contacts",query=f"?stage=eq.PROSPECT&last_updated=lt.{cutoff}&limit=100") or []

def archive_stale(contacts, reason="stale"):
    count = 0
    for c in contacts:
        result = supabase_request("PATCH","contacts",data={"stage":"CLOSED_LOST","stage_reason":reason},query=f"?id=eq.{c.get('id','')}")
        if result: count += 1
    return count

def deduplicate_emails():
    contacts = supabase_request("GET","contacts",query="?select=id,email&limit=500") or []
    seen = {}
    dupes = []
    for c in contacts:
        email = c.get("email","")
        if email in seen:
            dupes.append(c.get("id"))
        else:
            seen[email] = c.get("id")
    return dupes

def run():
    stale_leads = find_stale_leads(30)
    stale_prospects = find_stale_prospects(14)
    archived_l = archive_stale(stale_leads, "stale_lead_30d")
    archived_p = archive_stale(stale_prospects, "stale_prospect_14d")
    dupes = deduplicate_emails()
    msg = f"Pipeline clean: archived {archived_l} leads, {archived_p} prospects. Found {len(dupes)} duplicates."
    log.info(msg)
    notify(msg)
    return {"archived_leads":archived_l,"archived_prospects":archived_p,"duplicates":len(dupes)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
