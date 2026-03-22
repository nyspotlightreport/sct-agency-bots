#!/usr/bin/env python3
import os, json, urllib.request, urllib.parse
AV_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
if not AV_KEY:
    print("ALPHA_VANTAGE_API_KEY not set yet - add it to GitHub Secrets")
    exit(0)
params = {"function": "GLOBAL_QUOTE", "symbol": "AAPL", "apikey": AV_KEY}
url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(params)
with urllib.request.urlopen(url, timeout=15) as r:
    d = json.loads(r.read())
q = d.get("Global Quote", {})
if q:
    price = q.get("05. price", "?")
    pct   = q.get("10. change percent", "?")
    print(f"ALPHA VANTAGE LIVE: AAPL ${price} ({pct})")
    print("AV_KEY_STATUS=WORKING")
else:
    info = d.get("Information", d.get("Note", str(d)[:200]))
    print(f"AV Response: {info}")
