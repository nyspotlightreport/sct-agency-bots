#!/usr/bin/env python3
"""
bots/email_morning_digest_bot.py
Sends Sean a clean morning digest of what Priya handled overnight.
One Pushover. All the info. Nothing to do.
"""
import os, json, logging, urllib.request
from datetime import datetime, timedelta
log = logging.getLogger("digest"); logging.basicConfig(level=logging.INFO)

SUPA_URL  = os.environ.get("SUPABASE_URL","")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

def supa(method, table, data=None, query=""):
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def run():
    # Stats from last 24 hours
    since = (datetime.utcnow()-timedelta(hours=24)).isoformat()
    emails = supa("GET","email_inbox","",f"?processed_at=gte.{since}&select=category,priority_score,from_email,subject,ai_summary,forwarded") or []
    if not isinstance(emails,list): emails=[]

    total     = len(emails)
    revenue   = [e for e in emails if e.get("category")=="REVENUE"]
    urgent    = [e for e in emails if e.get("category") in ["URGENT","LEGAL"]]
    important = [e for e in emails if e.get("forwarded") and e.get("category") not in ["REVENUE","URGENT","LEGAL"]]
    killed    = [e for e in emails if e.get("category") in ["NEWSLETTER","AUTO","SPAM"]]

    lines = [
        f"📬 Email Intelligence — {datetime.utcnow().strftime('%b %d')}",
        f"Priya handled {total} emails overnight.",
        "",
    ]
    
    if revenue:
        lines.append(f"💰 {len(revenue)} REVENUE email(s) — in your priority inbox")
        for e in revenue[:3]:
            lines.append(f"  • {e.get('from_email','?').split('@')[0]}: {e.get('ai_summary','')[:60]}")
        lines.append("")
    
    if urgent:
        lines.append(f"🚨 {len(urgent)} URGENT — in your priority inbox")
        for e in urgent[:2]:
            lines.append(f"  • {e.get('ai_summary','')[:70]}")
        lines.append("")
    
    if important:
        lines.append(f"📌 {len(important)} important others forwarded")
    
    lines.append(f"🗑️ {len(killed)} newsletters/auto emails killed")
    lines.append("")
    lines.append(f"✅ Check {os.environ.get('PRIORITY_EMAIL','your priority inbox')} for anything needing attention.")

    msg = "\n".join(lines)
    log.info(msg)

    if PUSH_API and PUSH_USER:
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"📬 Priya: {total} emails handled",
            "message":msg,"priority":0}).encode()
        req2 = urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data, headers={"Content-Type":"application/json"})
        try: urllib.request.urlopen(req2, timeout=10)
        except Exception:  # noqa: bare-except

            pass
    # Save digest
    supa("POST","email_digest",{
        "digest_date": datetime.utcnow().date().isoformat(),
        "period": "morning",
        "total_emails": total,
        "revenue_emails": len(revenue),
        "urgent_emails": len(urgent),
        "newsletters_killed": len(killed),
        "summary_html": msg,
        "pushover_sent": True
    })

if __name__ == "__main__": run()
