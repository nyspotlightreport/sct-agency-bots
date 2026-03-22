#!/usr/bin/env python3
"""
bots/token_auto_refresh_bot.py
Never let an OAuth token expire.
Monitors all tokens, auto-refreshes when possible, alerts when manual action needed.
Runs every 6 hours.
"""
import os, json, logging, datetime, urllib.request, urllib.error
log = logging.getLogger("token_refresh")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [TOKEN] %(message)s")

SUPA             = os.environ.get("SUPABASE_URL","")
KEY              = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
GH_TOKEN         = os.environ.get("GH_PAT","")
PUSH_API         = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER        = os.environ.get("PUSHOVER_USER_KEY","")
LI_CLIENT_ID     = os.environ.get("LINKEDIN_CLIENT_ID","")
LI_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET","")
LI_REFRESH_TOKEN = os.environ.get("LINKEDIN_REFRESH_TOKEN","")
now              = datetime.datetime.utcnow()

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def update_github_secret(secret_name: str, secret_value: str) -> bool:
    """Update a GitHub secret via API."""
    if not GH_TOKEN: return False
    from base64 import b64encode
    H = {"Authorization":f"token {GH_TOKEN}","Content-Type":"application/json",
         "Accept":"application/vnd.github.v3+json"}
    REPO = "nyspotlightreport/sct-agency-bots"

    # Get public key for encryption
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",headers=H)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            key_data = json.loads(r.read())
    except: return False

    try:
        from nacl import encoding, public as nacl_pub
        pk = nacl_pub.PublicKey(key_data["key"].encode(), encoding.Base64Encoder())
        encrypted = b64encode(nacl_pub.SealedBox(pk).encrypt(secret_value.encode())).decode()
    except ImportError:
        log.warning("PyNaCl not available — cannot encrypt secret")
        return False

    payload = json.dumps({"encrypted_value":encrypted,"key_id":key_data["key_id"]}).encode()
    req2 = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}",
        data=payload, method="PUT", headers=H)
    try:
        with urllib.request.urlopen(req2, timeout=15) as r:
            return r.status in [201, 204]
    except: return False

def refresh_linkedin():
    """Refresh LinkedIn access token using refresh token."""
    if not LI_CLIENT_ID or not LI_CLIENT_SECRET or not LI_REFRESH_TOKEN:
        log.warning("LinkedIn credentials not available for refresh")
        supa("PATCH","oauth_tokens",{
            "status":"needs_manual_auth",
            "error_message":"Missing CLIENT_ID, CLIENT_SECRET, or REFRESH_TOKEN"
        },"?service=eq.linkedin")
        return False

    data = urllib.parse.urlencode({
        "grant_type":"refresh_token",
        "refresh_token":LI_REFRESH_TOKEN,
        "client_id":LI_CLIENT_ID,
        "client_secret":LI_CLIENT_SECRET
    }).encode()

    req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken",
        data=data, headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        import urllib.parse
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            new_token   = resp.get("access_token","")
            new_refresh = resp.get("refresh_token", LI_REFRESH_TOKEN)
            expires_in  = resp.get("expires_in", 5184000)  # 60 days default

            if new_token:
                # Update GitHub secrets
                update_github_secret("LINKEDIN_ACCESS_TOKEN", new_token)
                if new_refresh != LI_REFRESH_TOKEN:
                    update_github_secret("LINKEDIN_REFRESH_TOKEN", new_refresh)

                # Update DB record
                new_expiry = (now + datetime.timedelta(seconds=expires_in)).isoformat()
                new_refresh_at = (now + datetime.timedelta(seconds=expires_in-1296000)).isoformat()  # 15 days before expiry
                supa("PATCH","oauth_tokens",{
                    "status":"active","expires_at":new_expiry,
                    "refresh_at":new_refresh_at,"last_refreshed":now.isoformat(),
                    "refresh_count__add":1,"error_message":None
                },"?service=eq.linkedin")

                log.info("LinkedIn token refreshed successfully")
                return True
            return False
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        log.error(f"LinkedIn refresh failed: {e.code} — {error[:100]}")
        supa("PATCH","oauth_tokens",{"status":"refresh_failed","error_message":error[:200]},
             "?service=eq.linkedin")
        return False

def check_and_refresh_all():
    tokens = supa("GET","oauth_tokens","","?select=*") or []
    refreshed = 0; alerts = 0

    for token in (tokens if isinstance(tokens,list) else []):
        service  = token.get("service","")
        status   = token.get("status","")
        expires  = token.get("expires_at")
        refresh  = token.get("refresh_at")

        if not expires: continue

        try:
            exp_dt     = datetime.datetime.fromisoformat(expires.replace("Z","+00:00"))
            refresh_dt = datetime.datetime.fromisoformat(refresh.replace("Z","+00:00")) if refresh else exp_dt - datetime.timedelta(days=15)
            now_aware  = now.replace(tzinfo=datetime.timezone.utc)
            exp_aware  = exp_dt.replace(tzinfo=datetime.timezone.utc) if exp_dt.tzinfo is None else exp_dt
            ref_aware  = refresh_dt.replace(tzinfo=datetime.timezone.utc) if refresh_dt.tzinfo is None else refresh_dt

            days_to_exp = (exp_aware - now_aware).days

            if now_aware >= exp_aware:
                # Token expired
                supa("PATCH","oauth_tokens",{"status":"expired"},"?service=eq."+service)
                if PUSH_API and PUSH_USER:
                    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
                        "title":f"🚨 {service.upper()} TOKEN EXPIRED",
                        "message":f"{service} token expired. Automations failing. Re-authenticate at /tokens/",
                        "priority":1}).encode()
                    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                        data=data, headers={"Content-Type":"application/json"})
                    try: urllib.request.urlopen(req, timeout=10)
                    except: pass
                alerts += 1

            elif now_aware >= ref_aware:
                # Time to refresh
                log.info(f"Refreshing {service} token ({days_to_exp} days until expiry)...")
                if service == "linkedin":
                    if refresh_linkedin(): refreshed += 1
                else:
                    # For services without auto-refresh, alert Sean
                    if days_to_exp <= 3 and PUSH_API and PUSH_USER:
                        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
                            "title":f"⚠️ {service.upper()} token expiring",
                            "message":f"{service} expires in {days_to_exp} days. Visit /tokens/ to re-authenticate.",
                            "priority":0}).encode()
                        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                            data=data, headers={"Content-Type":"application/json"})
                        try: urllib.request.urlopen(req, timeout=10)
                        except: pass

        except Exception as e:
            log.warning(f"Token check {service}: {e}")

    log.info(f"Token check complete: {refreshed} refreshed | {alerts} expired alerts")
    return {"refreshed":refreshed,"alerts":alerts}

if __name__ == "__main__": check_and_refresh_all()
