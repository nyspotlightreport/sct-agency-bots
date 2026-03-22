#!/usr/bin/env python3
"""
bots/sweepstakes_email_parser_bot.py
Parses sweepstakes digest emails that Priya receives.
Extracts: title, entry URL, prize value.
Populates: sweepstakes_queue table.
Runs after Priya classifies and stores the email body.
"""
import os, json, re, logging, urllib.request
from datetime import datetime

log = logging.getLogger("sweep_parser")
logging.basicConfig(level=logging.INFO)

SUPA_URL = os.environ.get("SUPABASE_URL","")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

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

def claude_extract(email_body):
    """Use Claude to extract structured sweepstakes data from email body."""
    if not ANTHROPIC: return []
    prompt = f"""Extract sweepstakes from this email body. Return ONLY valid JSON array.

EMAIL BODY:
{email_body[:3000]}

Extract each sweepstakes as:
{{"title":"...", "url":"...", "prize_desc":"...", "prize_value":1000}}

prize_value = estimated dollar amount (integer). If not stated, use 0.
Include only entries with actual entry URLs.
Return JSON array only. No other text."""

    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":1000,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())["content"][0]["text"].strip()
            result = result.strip('`').strip()
            if result.startswith('json'): result = result[4:]
            return json.loads(result)
    except Exception as e:
        log.warning(f"Claude extract: {e}")
        return []

def fallback_extract(email_body):
    """Regex fallback for URL+prize extraction."""
    entries = []
    # Find URLs
    urls = re.findall(r'https?://[^\s\'"<>\)]{20,}', email_body)
    # Find prize values near URLs
    for url in urls[:30]:
        if any(skip in url.lower() for skip in ['unsubscribe','pixel','track','google','mail']):
            continue
        idx = email_body.find(url[:40])
        context = email_body[max(0,idx-200):idx+200]
        prize_match = re.search(r'\$([0-9,]{2,})', context)
        prize_val = int(prize_match.group(1).replace(',','')) if prize_match else 0
        title_match = re.search(r'([A-Z][^.\n]{10,80})', context)
        title = title_match.group(1)[:100] if title_match else url.split('/')[2]
        entries.append({"title":title,"url":url,"prize_value":min(prize_val,9999999),"prize_desc":""})
    return entries

def run():
    log.info("Sweepstakes Email Parser — extracting from recent emails")
    
    # Get recent sweepstakes digest emails from inbox
    recent = supa("GET","email_inbox","",
        "?subject=ilike.*sweepstakes*&select=id,body_text,subject,received_at&order=received_at.desc&limit=5") or []
    
    # Also try "digest" in subject
    recent2 = supa("GET","email_inbox","",
        "?subject=ilike.*digest*&select=id,body_text,subject,received_at&order=received_at.desc&limit=3") or []
    
    all_emails = list(recent if isinstance(recent,list) else []) + list(recent2 if isinstance(recent2,list) else [])
    
    if not all_emails:
        log.info("No sweepstakes digest emails found. Waiting for Priya to classify them.")
        return
    
    total_queued = 0
    
    for email_rec in all_emails:
        body = email_rec.get("body_text","") or ""
        email_id = email_rec.get("id","")
        
        if not body:
            continue
        
        log.info(f"Parsing: {email_rec.get('subject','?')[:60]}")
        
        # Extract entries
        entries = claude_extract(body) if ANTHROPIC else fallback_extract(body)
        if not entries:
            entries = fallback_extract(body)
        
        for entry in entries[:25]:
            url = entry.get("url","")
            if not url: continue
            
            # Check if already queued
            existing = supa("GET","sweepstakes_queue","",f"?url=eq.{urllib.parse.quote(url)[:200]}&select=id")
            if existing and isinstance(existing,list) and existing:
                continue  # Already in queue
            
            supa("POST","sweepstakes_queue",{
                "title":        (entry.get("title","") or url.split('/')[2])[:200],
                "url":          url,
                "source":       "priya_email_parser",
                "prize_value":  min(int(entry.get("prize_value",0) or 0), 9999999),
                "prize_desc":   (entry.get("prize_desc","") or "")[:300],
                "status":       "pending",
                "source_email_id": email_id or None
            })
            total_queued += 1
        
        log.info(f"  Queued {len(entries)} entries from this email")
    
    log.info(f"Total newly queued: {total_queued}")
    return total_queued

if __name__ == "__main__":
    import urllib.parse
    run()
