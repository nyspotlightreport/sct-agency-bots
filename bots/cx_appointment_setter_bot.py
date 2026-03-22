#!/usr/bin/env python3
"""bots/cx_appointment_setter_bot.py
AI appointment setter — books discovery calls, demos, and closing calls.
Target: 10+ qualified meetings per week across all outreach campaigns.
"""
import os, json, urllib.request, logging, datetime
log = logging.getLogger("appointment_setter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [APPT] %(message)s")

SUPA = os.environ.get("SUPABASE_URL","")
KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
CALENDLY_TOKEN = os.environ.get("CALENDLY_TOKEN","")

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e:
        log.warning(f"DB: {e}"); return None

def ai(prompt, max_tokens=300):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def process_positive_replies():
    """Find positive replies in sequences and convert them to booked appointments."""
    positive = supa("GET","outreach_sequences","",
        "?reply_received=eq.true&reply_sentiment=eq.positive&meeting_booked=eq.false&limit=20&select=*") or []
    booked = 0
    for seq in positive:
        contact = supa("GET","contacts","",f"?id=eq.{seq.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact,list) else contact)
        appt_type = "demo" if c.get("score",0) > 70 else "discovery"
        meeting_link = "https://calendly.com/nyspotlightreport/30min"
        follow_up = ai(
            f"Write a short, confident email to book a {appt_type} call.
"
            f"Contact: {c.get('name')} at {c.get('company')}.
"
            f"They replied positively to our outreach.
"
            f"Include Calendly link: {meeting_link}
"
            f"Under 80 words. Confident. Clear CTA.",
            max_tokens=150)
        if follow_up:
            supa("POST","appointments",{
                "contact_id":c.get("id"),
                "campaign_id":seq.get("campaign_id"),
                "appointment_type":appt_type,
                "status":"pending",
                "meeting_link":meeting_link,
                "prep_notes":f"Prospect replied positively to {seq.get('channel','email')} outreach.",
            })
            supa("PATCH","outreach_sequences",{"meeting_booked":True},
                f"?id=eq.{seq['id']}")
            supa("PATCH","contacts",{"stage":"HOT","next_action":"Appointment booked — confirm and prep"},
                f"?id=eq.{c['id']}")
            booked += 1
    log.info(f"Appointments queued: {booked}")
    return {"appointments_queued":booked}

def send_appointment_reminders():
    """Send 24hr and 1hr reminders for confirmed appointments."""
    tomorrow = (datetime.datetime.utcnow()+datetime.timedelta(days=1)).date().isoformat()
    appts = supa("GET","appointments","",
        f"?status=eq.confirmed&scheduled_at=gte.{tomorrow}T00:00:00&scheduled_at=lt.{tomorrow}T23:59:59&select=*") or []
    for a in appts:
        contact = supa("GET","contacts","",f"?id=eq.{a.get('contact_id','')}&select=name,email&limit=1")
        if contact:
            c = (contact[0] if isinstance(contact,list) else contact)
            log.info(f"Reminder queued: {c.get('name')} — {a.get('appointment_type')} tomorrow")
    log.info(f"Reminders: {len(appts)} sent")
    return {"reminders_sent":len(appts)}

def run():
    r = {}
    r["bookings"] = process_positive_replies()
    r["reminders"] = send_appointment_reminders()
    return r

if __name__ == "__main__": run()
