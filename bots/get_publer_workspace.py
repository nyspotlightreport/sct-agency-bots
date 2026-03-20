#!/usr/bin/env python3
"""One-shot: fetch Publer workspace ID and print it clearly"""
import os, json, urllib.request, urllib.error

KEY = os.getenv("PUBLER_API_KEY","")
if not KEY:
    print("ERROR: No PUBLER_API_KEY set")
    exit(1)

req = urllib.request.Request(
    "https://app.publer.com/api/v1/workspaces",
    headers={"Authorization": f"Bearer-API {KEY}",
             "Content-Type": "application/json",
             "Accept": "*/*"}
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    print("=== PUBLER WORKSPACES ===")
    if isinstance(data, list):
        for ws in data:
            print(f"ID: {ws.get('id')} | Name: {ws.get('name')} | Role: {ws.get('role')}")
        print(f"\nPRIMARY_WORKSPACE_ID={data[0].get('id') if data else 'NONE'}")
    else:
        print(json.dumps(data, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:300]}")
except Exception as e:
    print(f"Error: {e}")
