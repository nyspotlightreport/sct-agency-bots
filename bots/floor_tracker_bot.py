#!/usr/bin/env python3
"""
$500 Floor Tracker — checks income streams, sends phone notification
Runs daily at 7:30 AM UTC via GitHub Actions
"""
import os, requests, json
from datetime import datetime

NTFY_TOPIC = "nysr-chairman1sct"
GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN","")  # Never hardcode tokens
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY","")

INCOME_TARGETS = {
    "Gumroad digital products":    {"target": 120, "status": "active"},
    "Payhip digital products":     {"target": 40,  "status": "active"},
    "Affiliate articles (34 live)":{"target": 150, "status": "active"},
    "YouTube + Beehiiv bots":      {"target": 50,  "status": "active"},
    "Sweepstakes + Bing rewards":  {"target": 40,  "status": "active"},
    "Bandwidth stack (EarnApp)":   {"target": 60,  "status": "pending_setup"},
    "KDP 10 books":                {"target": 50,  "status": "pending_upload"},
    "Redbubble 20 designs":        {"target": 80,  "status": "pending_upload"},
    "Teepublic 20 designs":        {"target": 60,  "status": "pending_upload"},
}

def check_gumroad():
    try:
        r = requests.get("https://api.gumroad.com/v2/products",
            params={"access_token": GUMROAD_TOKEN}, timeout=10)
        if r.ok:
            prods = r.json().get("products",[])
            total_sales = sum(p.get("sales_count",0) for p in prods)
            return len(prods), total_sales
    except Exception:  # noqa: bare-except

        pass
    return 0, 0

def run():
    today = datetime.now().strftime("%B %d, %Y")
    
    # Check Gumroad
    gum_products, gum_sales = check_gumroad()
    
    active_monthly = sum(v["target"] for v in INCOME_TARGETS.values() if v["status"] == "active")
    pending_monthly = sum(v["target"] for v in INCOME_TARGETS.values() if v["status"].startswith("pending"))
    total_target = active_monthly + pending_monthly
    gap = total_target - active_monthly
    
    # Build notification
    active_streams = [k for k,v in INCOME_TARGETS.items() if v["status"] == "active"]
    pending_streams = [k for k,v in INCOME_TARGETS.items() if v["status"].startswith("pending")]
    
    msg = f"DAILY INCOME REPORT — {today}\n\n"
    msg += f"ACTIVE MONTHLY FLOOR: ${active_monthly}/month\n"
    msg += f"PENDING (needs setup): ${pending_monthly}/month\n"
    msg += f"TOTAL TARGET: ${total_target}/month\n"
    msg += f"GAP TO CLOSE: ${gap}/month\n\n"
    msg += f"Gumroad: {gum_products} products live | {gum_sales} total sales\n\n"
    msg += f"ACTIVE ({len(active_streams)} streams):\n"
    for s in active_streams:
        msg += f"  + {INCOME_TARGETS[s]['target']}/mo {s}\n"
    msg += f"\nPENDING ({len(pending_streams)} streams — run PowerShell commands):\n"
    for s in pending_streams:
        msg += f"  > ${INCOME_TARGETS[s]['target']}/mo {s}\n"
    
    print(msg)
    
    # Send phone notification
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=msg,
            headers={
                "Title": f"Income Floor: ${active_monthly}/mo active | ${gap} gap",
                "Tags": "money_with_wings,chart_with_upwards_trend",
                "Priority": "default"
            }, timeout=10)
        print("Phone notification sent!")
    except Exception as e:
        print(f"Notification error: {e}")

if __name__ == "__main__":
    run()
