#!/usr/bin/env python3
"""
bots/reddit_password_grant_bot.py
Reddit uses password grant flow for script apps — no browser required.
Generates fresh token using username + password + client credentials.
Completely autonomous. No OAuth redirect. No user interaction ever needed.
"""
import os, json, logging, base64, urllib.request, urllib.error
log = logging.getLogger("reddit_auth")
logging.basicConfig(level=logging.INFO)

REDDIT_CLIENT_ID     = os.environ.get("REDDIT_CLIENT_ID","")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET","")
REDDIT_USERNAME      = os.environ.get("REDDIT_USERNAME","")
REDDIT_PASSWORD      = os.environ.get("REDDIT_PASSWORD","")
GH_PAT               = os.environ.get("GH_PAT","")
REPO                 = "nyspotlightreport/sct-agency-bots"

def get_reddit_token():
    """Password grant — zero browser interaction required for script apps."""
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        log.warning("Reddit credentials not set. Visit nyspotlightreport.com/tokens/ to configure.")
        return None

    # Base64 encode client credentials
    creds = base64.b64encode(f"{REDDIT_CLIENT_ID}:{REDDIT_CLIENT_SECRET}".encode()).decode()

    data = urllib.parse.urlencode({
        "grant_type": "password",
        "username":   REDDIT_USERNAME,
        "password":   REDDIT_PASSWORD,
        "scope":      "read submit identity"
    }).encode()

    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "Authorization": f"Basic {creds}",
            "User-Agent":    "NYSR:AutoBot:v1.0 (by /u/" + REDDIT_USERNAME + ")",
            "Content-Type":  "application/x-www-form-urlencoded"
        }
    )
    try:
        import urllib.parse
        with urllib.request.urlopen(req, timeout=15) as r:
            token_data = json.loads(r.read())
            access_token = token_data.get("access_token","")
            if access_token:
                log.info(f"Reddit token obtained — expires in {token_data.get('expires_in',0)}s")
                return access_token
            else:
                log.error(f"Reddit token failed: {token_data}")
                return None
    except Exception as e:
        log.error(f"Reddit auth error: {e}")
        return None

def save_to_github(token):
    """Save fresh Reddit token to GitHub Secrets."""
    if not GH_PAT or not token: return False
    
    # Get public key
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
        headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            key_data = json.loads(r.read())
    except: return False

    key_id = key_data.get("key_id","")
    encoded = base64.b64encode(token.encode()).decode()

    req2 = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/secrets/REDDIT_ACCESS_TOKEN",
        data=json.dumps({"encrypted_value": encoded, "key_id": key_id}).encode(),
        method="PUT",
        headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=10) as r:
            log.info(f"Reddit token saved to GitHub Secrets: {r.status}")
            return r.status in [201, 204]
    except: return False

if __name__ == "__main__":
    import urllib.parse
    token = get_reddit_token()
    if token:
        save_to_github(token)
        log.info("Reddit: fully automated. Password grant. No browser. No OAuth. Token refreshes on every run.")
    else:
        log.warning("Reddit: configure credentials at nyspotlightreport.com/tokens/ first")
