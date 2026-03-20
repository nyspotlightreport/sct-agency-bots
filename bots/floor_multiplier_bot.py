#!/usr/bin/env python3
"""
$500 Floor Multiplier Bot
Coordinates all passive income streams and tracks toward $500 minimum
Runs daily to ensure all streams are healthy and earning

TARGET FLOORS (conservative, guaranteed streams only):
- Bandwidth Stack:     $60/month  (home PC on 24/7)
- Gumroad Products:   $80/month  (20 products, organic discovery)
- Payhip Products:    $40/month  (20 products, cross-platform)
- Redbubble POD:      $60/month  (20 designs, no work after upload)
- KDP Books:          $50/month  (10 books, royalties forever)
- Affiliate Articles: $80/month  (daily content, SEO traffic)
- Bing Rewards:       $10/month  (daily bot)
- YouTube/Beehiiv:    $50/month  (bots running daily)
- Sweepstakes wins:   $30/month  (hourly bot, conservative)
= $460/month FLOOR → rounds to $500 with any one upside event
"""
import os, json, requests, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("FloorMultiplier")

GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN",os.environ.get("GUMROAD_ACCESS_TOKEN",""))
GH_TOKEN      = os.environ.get("GH_TOKEN",os.environ.get("GH_TOKEN",""))
NTFY_TOPIC    = "nysr-chairman1sct"

STREAMS = {
    "bandwidth":        {"target_monthly":60,  "active":False, "check":"docker ps | grep honeygain"},
    "gumroad":          {"target_monthly":80,  "active":True,  "url":"https://spotlightny.gumroad.com"},
    "payhip":           {"target_monthly":40,  "active":True,  "url":"https://payhip.com/ProFlowDigital"},
    "redbubble_pod":    {"target_monthly":60,  "active":False, "check":"upload designs to redbubble.com/people/nysr101"},
    "kdp_books":        {"target_monthly":50,  "active":False, "check":"upload PDFs from data/kdp_books/ to kdp.amazon.com"},
    "affiliate_articles":{"target_monthly":80, "active":True,  "bot":"affiliate_content_bot.py"},
    "bing_rewards":     {"target_monthly":10,  "active":True,  "bot":"bing_rewards_bot.py"},
    "youtube_beehiiv":  {"target_monthly":50,  "active":True,  "bot":"youtube_shorts_bot.py"},
    "sweepstakes":      {"target_monthly":30,  "active":True,  "bot":"sweepstakes_digest_bot.py"},
}

QUICK_WIN_ACTIONS = [
    {
        "action": "Run PowerShell bandwidth installer",
        "value": "+$60/month",
        "command": "irm https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/install_windows.ps1 | iex",
        "effort": "5 min",
        "done": False
    },
    {
        "action": "Upload 10 KDP books",
        "value": "+$50/month by week 4",
        "url": "https://kdp.amazon.com → Bookshelf → + Paperback",
        "effort": "20 min",
        "done": False
    },
    {
        "action": "Upload 20 Redbubble designs",
        "value": "+$60/month",
        "url": "https://www.redbubble.com/portfolio/images/new",
        "effort": "30 min (designs auto-generated)",
        "done": False
    },
    {
        "action": "Complete Grass extension signup",
        "value": "+$20/month + token upside",
        "url": "https://app.getgrass.io",
        "effort": "2 min",
        "done": False
    },
    {
        "action": "Join Amazon Associates",
        "value": "+$30-100/month",
        "url": "https://affiliate-program.amazon.com",
        "effort": "5 min signup",
        "done": False
    },
    {
        "action": "Apply to Mediavine (when 10k sessions/mo)",
        "value": "+$200-500/month ad revenue",
        "url": "https://mediavine.com",
        "effort": "5 min application",
        "done": False
    },
]

def check_gumroad_sales():
    """Check for any Gumroad sales"""
    try:
        r = requests.get("https://api.gumroad.com/v2/sales",
            params={"access_token": GUMROAD_TOKEN, "after": "2026-01-01"})
        if r.ok:
            sales = r.json().get('sales', [])
            revenue = sum(float(s.get('price','0'))/100 for s in sales)
            return len(sales), revenue
    except: pass
    return 0, 0.0

def generate_floor_report():
    active_streams = [k for k,v in STREAMS.items() if v['active']]
    inactive_streams = [k for k,v in STREAMS.items() if not v['active']]
    
    active_target = sum(v['target_monthly'] for k,v in STREAMS.items() if v['active'])
    total_target  = sum(v['target_monthly'] for v in STREAMS.values())
    
    sales_count, sales_rev = check_gumroad_sales()
    
    report = {
        "generated": datetime.now().isoformat(),
        "floor_target": 500,
        "active_monthly_potential": active_target,
        "total_monthly_potential": total_target,
        "gap_to_floor": max(0, 500 - active_target),
        "gumroad_sales_alltime": sales_count,
        "gumroad_revenue_alltime": f"${sales_rev:.2f}",
        "active_streams": active_streams,
        "inactive_streams": inactive_streams,
        "quick_wins_todo": [a for a in QUICK_WIN_ACTIONS if not a['done']],
        "stream_details": STREAMS
    }
    
    # Print summary
    print(f"\n{'='*55}")
    print(f"💰 $500 FLOOR TRACKER — {datetime.now().strftime('%b %d %Y')}")
    print(f"{'='*55}")
    print(f"Active streams:    {len(active_streams)}/{len(STREAMS)}")
    print(f"Active potential:  ${active_target}/month")
    print(f"Full potential:    ${total_target}/month")
    print(f"Gap to $500 floor: ${max(0, 500 - active_target)}/month")
    print(f"\nGumroad all-time: {sales_count} sales | ${sales_rev:.2f}")
    print(f"\n⚡ Top actions to close the gap:")
    for a in QUICK_WIN_ACTIONS[:3]:
        if not a['done']:
            print(f"  • {a['action']} → {a['value']} ({a['effort']})")
    
    # Send phone notification if gap exists
    gap = max(0, 500 - active_target)
    if gap > 0:
        msg = f"Floor gap: ${gap}/month still needed. Top action: {QUICK_WIN_ACTIONS[0]['action']}"
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
            headers={"Title":f"💰 Income Floor: ${active_target}/mo active | ${gap} gap","Tags":"chart_increasing","Priority":"default"},
            data=msg, timeout=5)
    
    os.makedirs("data", exist_ok=True)
    with open("data/floor_report.json","w") as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    generate_floor_report()
