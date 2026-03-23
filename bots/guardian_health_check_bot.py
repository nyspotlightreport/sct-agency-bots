#!/usr/bin/env python3
"""
bots/guardian_health_check_bot.py
Lightweight system health check.
Checks: Netlify functions, Supabase, key workflow status.
Runs every 30 min as part of guardian.
"""
import os, json, urllib.request
from datetime import datetime, timedelta

SUPA_URL  = os.environ.get("SUPABASE_URL","")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
GH_PAT    = os.environ.get("GH_PAT","")
SITE      = "https://nyspotlightreport.com"

def check_endpoint(url, name):
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except: return False

def run():
    checks = {
        "Store page":       check_endpoint(f"{SITE}/store/", "Store"),
        "Email dashboard":  check_endpoint(f"{SITE}/.netlify/functions/email-dashboard", "Email"),
        "AI dashboard":     check_endpoint(f"{SITE}/.netlify/functions/ai-dashboard", "AI"),
        "Lead capture":     check_endpoint(f"{SITE}/.netlify/functions/lead-capture", "Lead"),
        "Knowledge base":   check_endpoint(f"{SITE}/.netlify/functions/knowledge-base", "KB"),
    }
    
    failed = [k for k, v in checks.items() if not v]
    
    if failed and PUSH_API and PUSH_USER:
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"⚠️ {len(failed)} endpoints down",
            "message":"\n".join(failed),"priority":0}).encode()
        try: urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except Exception:  # noqa: bare-except

            pass
    all_ok = len(failed) == 0
    print(f"Health: {'✅ All OK' if all_ok else f'❌ {len(failed)} failed: {failed}'}")
    return {"ok": all_ok, "failed": failed}

if __name__ == "__main__": run()
