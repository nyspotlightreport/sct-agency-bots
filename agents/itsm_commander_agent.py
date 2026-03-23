"""
ITSM Commander Agent — Phase 4
Central command for all IT service management.
Triages tickets, enforces SLAs, coordinates resolutions, escalates critical issues.
Revenue unlock: $997-1,997/mo per enterprise client.
"""
import os, json, logging, datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ITSM] %(message)s")
log = logging.getLogger("itsm")

SUPABASE_URL  = os.environ.get("SUPABASE_URL","")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
HUBSPOT_KEY   = os.environ.get("HUBSPOT_API_KEY","")

import urllib.request, urllib.error

def supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}",
               "Content-Type":"application/json","Prefer":"return=representation"}
    req = urllib.request.Request(url,data=payload,method=method,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code} {e.read()[:100]}")
        return None

def ai(prompt, system="You are an expert IT support manager."):
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":600,
                        "system":system,"messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,headers={
        "Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def push(title, msg, priority=0):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER,
                       "title":title,"message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req,timeout=10)
    except Exception:  # noqa: bare-except

        pass
def check_sla_breaches():
    """Find tickets past their SLA due date and escalate."""
    now = datetime.datetime.utcnow().isoformat()
    overdue = supa("GET","tickets",
        f"?status=in.(open,in_progress)&due_at=lt.{now}&sla_breached=eq.false&select=*") or []
    for t in overdue:
        # Mark as breached
        supa("PATCH","tickets",
             {"sla_breached":True,"updated_at":now},
             query=f"?id=eq.{t['id']}")
        # Log SLA event
        supa("POST","sla_events",{
            "ticket_id":t["id"],"event_type":"breached",
            "meta":{"priority":t["priority"],"age_hrs":round(
                (datetime.datetime.utcnow()-datetime.datetime.fromisoformat(
                    t["created_at"].replace("Z",""))).total_seconds()/3600,1)}
        })
        # Escalate to Chairman
        priority_map = {"critical":2,"high":1,"medium":0,"low":-1}
        p = priority_map.get(t.get("priority","medium"),0)
        push(f"🚨 SLA BREACH #{t.get('ticket_number','')}",
             f"{t['title'][:60]}\nPriority: {t['priority']}\nClient: {t.get('portal_user_id','?')[:8]}",
             priority=p)
        log.warning(f"SLA BREACH: #{t.get('ticket_number','')} — {t['title'][:50]}")

    # Warn on tickets approaching SLA (25% time remaining)
    in_2hrs = (datetime.datetime.utcnow()+datetime.timedelta(hours=2)).isoformat()
    approaching = supa("GET","tickets",
        f"?status=in.(open,in_progress)&due_at=lt.{in_2hrs}&due_at=gt.{now}&sla_breached=eq.false&select=*") or []
    for t in approaching:
        existing = supa("GET","sla_events",
            f"?ticket_id=eq.{t['id']}&event_type=eq.breach_warning&select=id&limit=1") or []
        if not existing:
            supa("POST","sla_events",{"ticket_id":t["id"],"event_type":"breach_warning"})
            push(f"⚠️ SLA Warning #{t.get('ticket_number','')}",
                 f"{t['title'][:60]}\nDue: {t.get('due_at','?')[:16]}")

    log.info(f"SLA check: {len(overdue)} breached, {len(approaching)} approaching")

def auto_triage_new_tickets():
    """AI-triage any open tickets with no first response yet."""
    cutoff = (datetime.datetime.utcnow()-datetime.timedelta(hours=1)).isoformat()
    new_tickets = supa("GET","tickets",
        f"?status=eq.open&first_response_at=is.null&created_at=gt.{cutoff}&select=*") or []
    for t in new_tickets:
        # Generate AI response
        reply = ai(
            f"Write a helpful, professional first response to this support ticket. "
            f"Acknowledge receipt, give an initial assessment, and set expectations. "
            f"Max 3 sentences. Signed 'NYSR Support Team'.\n"
            f"Ticket: {t['title']}\nDetails: {(t.get('description','') or '')[:300]}"
        )
        if reply:
            now = datetime.datetime.utcnow().isoformat()
            supa("POST","ticket_messages",{
                "ticket_id":t["id"],"author_type":"ai",
                "author_name":"NYSR Support AI","body":reply.strip()
            })
            supa("PATCH","tickets",
                 {"first_response_at":now,"status":"in_progress"},
                 query=f"?id=eq.{t['id']}")
            log.info(f"Auto-responded to ticket #{t.get('ticket_number','')} — {t['title'][:40]}")

def daily_itsm_report():
    """Generate and push daily ITSM metrics."""
    today = datetime.date.today().isoformat()
    open_t    = supa("GET","tickets","?status=eq.open&select=id") or []
    progress  = supa("GET","tickets","?status=eq.in_progress&select=id") or []
    resolved  = supa("GET","tickets",f"?status=eq.resolved&resolved_at=gte.{today}T00:00:00&select=id") or []
    breached  = supa("GET","tickets","?sla_breached=eq.true&status=neq.closed&select=id") or []
    critical  = supa("GET","tickets","?priority=eq.critical&status=in.(open,in_progress)&select=id") or []
    clients   = supa("GET","portal_users","?active=eq.true&select=id") or []
    revenue   = supa("GET","portal_users","?active=eq.true&select=plan_mrr") or []
    mrr       = sum(float(u.get("plan_mrr",0)) for u in revenue)

    report = (
        f"🎫 ITSM Report {today}\n"
        f"Clients: {len(clients)} | MRR: ${mrr:.0f}\n"
        f"Open: {len(open_t)} | In-Progress: {len(progress)}\n"
        f"Resolved Today: {len(resolved)}\n"
        f"SLA Breached: {len(breached)} | Critical Open: {len(critical)}"
    )
    log.info(report)
    priority = 1 if breached or critical else 0
    push("🎫 ITSM Daily Report", report, priority=priority)
    return report

def close_resolved_tickets():
    """Auto-close resolved tickets older than 3 days with no reply."""
    cutoff = (datetime.datetime.utcnow()-datetime.timedelta(days=3)).isoformat()
    old = supa("GET","tickets",f"?status=eq.resolved&updated_at=lt.{cutoff}&select=id,ticket_number") or []
    now = datetime.datetime.utcnow().isoformat()
    for t in old:
        supa("PATCH","tickets",{"status":"closed"},query=f"?id=eq.{t['id']}")
        log.info(f"Auto-closed ticket #{t.get('ticket_number','')} (no activity 3d)")

def run():
    log.info("=== ITSM Commander Agent ===")
    auto_triage_new_tickets()
    check_sla_breaches()
    close_resolved_tickets()
    daily_itsm_report()
    log.info("=== Done ===")

if __name__ == "__main__":
    run()
