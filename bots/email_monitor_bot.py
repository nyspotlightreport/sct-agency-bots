#!/usr/bin/env python3
import os, json, logging, imaplib, email as emaillib, urllib.request
log = logging.getLogger("monitor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

GMAIL_USER  = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS","")
SUPA_URL    = os.environ.get("SUPABASE_URL","")
SUPA_KEY    = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API    = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER   = os.environ.get("PUSHOVER_USER_KEY","")
AFF_EMAIL   = "seanb041992+affiliates@gmail.com"
SWEEP_EMAIL = "seanb041992+sweep@gmail.com"

WIN_KWORDS      = ['congratulations','you won','winner','prize claim','you have been selected','award']
APPROVAL_KWORDS = ['approved','welcome to our affiliate','accepted','affiliate account','commission link','your affiliate']
PROGRAMS = ['hubspot','ahrefs','shopify','gohighlevel','convertkit','clickfunnels','notion',
            'kinsta','wpengine','elevenlabs','semrush','canva','jasper','surfer','make','zapier']

def pushover(title, msg, priority=0):
    if not PUSH_API: return
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,
        "message":msg,"priority":priority,"sound":"cashregister"}).encode()
    try: urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data,headers={"Content-Type":"application/json"}),timeout=10)
    except: pass

def run():
    if not GMAIL_PASS: log.warning("No GMAIL_APP_PASS"); return
    wins=[];approvals=[]
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_USER, GMAIL_PASS)
        imap.select("INBOX")
        for alias,label in [(AFF_EMAIL,"AFF"),(SWEEP_EMAIL,"SWEEP")]:
            _, msgs = imap.search(None, f'TO "{alias}" SINCE "15-Mar-2026"')
            ids = msgs[0].split() if msgs[0] else []
            log.info(f"{label}: {len(ids)} emails to {alias}")
            for mid in ids[-30:]:
                _, data = imap.fetch(mid, "(RFC822)")
                if not data or not data[0]: continue
                msg = emaillib.message_from_bytes(data[0][1])
                sender  = str(msg.get("From","")).lower()
                subject = str(msg.get("Subject","")).lower()
                txt = sender + " " + subject
                if any(k in txt for k in WIN_KWORDS):
                    wins.append(f"{label}: {subject[:60]}")
                if label=="AFF" and any(k in txt for k in APPROVAL_KWORDS):
                    approvals.append(f"{subject[:60]} from {sender[:40]}")
                    for p in PROGRAMS:
                        if p in sender or p in subject:
                            if SUPA_URL:
                                req2 = urllib.request.Request(
                                    f"{SUPA_URL}/rest/v1/affiliate_programs?program_key=eq.{p}",
                                    data=json.dumps({"status":"approved"}).encode(), method="PATCH",
                                    headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                                             "Content-Type":"application/json","Prefer":"return=minimal"})
                                try: urllib.request.urlopen(req2, timeout=10)
                                except: pass
                            break
        imap.logout()
    except Exception as e: log.error(f"IMAP: {e}")
    for w in wins: pushover("WIN — CHECK NOW", w, priority=1)
    if approvals: pushover(f"{len(approvals)} Affiliate(s) Approved!", "\n".join(approvals[:5]), priority=0)
    log.info(f"Done: {len(wins)} wins, {len(approvals)} approvals")

if __name__ == "__main__": run()

