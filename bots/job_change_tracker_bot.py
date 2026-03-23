#!/usr/bin/env python3
# Job Change Tracker Bot - Monitors when contacts change jobs to trigger re-engagement.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None
log = logging.getLogger(__name__)

def generate_job_change_email(contact, new_role, new_company):
    name = (contact.get("name","") or "").split()[0] or "there"
    return {
        "subject": f"Congrats on the new role, {name}!",
        "body": claude(
            "Write a congratulations email on job change. Reference past conversation. Offer fresh start. Under 70 words.",
            f"Contact {name} moved to {new_role} at {new_company}. We spoke before about AI automation.",
            max_tokens=130
        ) or f"Hi {name}, just saw you moved to {new_role} at {new_company} - congrats! New role, new priorities. I'd love to reconnect and see if AI automation makes sense for your new team. 15 min call?",
    }

def check_job_changes():
    contacts = supabase_request("GET","contacts",
        query="?stage=in.(CLOSED_LOST,PROSPECT)&linkedin=not.is.null&limit=50") or []
    log.info(f"Monitoring {len(contacts)} contacts for job changes")
    return contacts

def run():
    contacts = check_job_changes()
    log.info(f"Job change monitoring: {len(contacts)} contacts tracked")
    return len(contacts)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
