#!/usr/bin/env python3
import os, json, urllib.request, urllib.error, gzip

KEY = os.getenv("PUBLER_API_KEY","").strip()
if not KEY:
    print("ERROR: PUBLER_API_KEY not set")
    exit(1)

# Show key format (masked) for diagnostics
masked = KEY[:4] + "..." + KEY[-4:] if len(KEY) > 8 else "TOO_SHORT"
print(f"Key format check: length={len(KEY)} preview={masked}")

# Test /workspaces
def publer_get(path):
    req = urllib.request.Request(
        f"https://app.publer.com/api/v1{path}",
        headers={
            "Authorization": f"Bearer-API {KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            try: return json.loads(gzip.decompress(raw))
            except: return json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: body = gzip.decompress(raw).decode()
        except: body = raw.decode('utf-8','replace')
        print(f"HTTP {e.code}: {body[:200]}")
        return None

data = publer_get("/workspaces")
if data:
    print("=== PUBLER WORKSPACES ===")
    if isinstance(data, list):
        for ws in data:
            print(f"ID: {ws.get('id')} | Name: {ws.get('name')} | Role: {ws.get('role')}")
        if data:
            print(f"\nPRIMARY_WORKSPACE_ID={data[0].get('id')}")
    else:
        print(json.dumps(data, indent=2)[:300])
