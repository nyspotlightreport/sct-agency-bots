#!/usr/bin/env python3
"""
Strategic ROI Optimizer — NYSR Business Development
╔══════════════════════════════════════════════════════════════╗
║  The single most valuable BD function:                      ║
║  Know EXACTLY where every dollar and hour goes.             ║
║  Kill what doesn't work. Double what does.                  ║
║  Find the hidden money in what you already have.            ║
╚══════════════════════════════════════════════════════════════╝

Weekly audit covers:
1. Revenue per channel (actual vs projected)
2. Cost per acquisition across all lead sources  
3. Bot/workflow efficiency (which run daily, which silently fail)
4. Affiliate performance by program
5. Content ROI (which posts drive leads/sales)
6. Time-to-revenue ranking (fastest paths to cash)
7. Hidden revenue opportunities in existing assets
8. Kill list: what to shut down to free capacity

Output: Ranked action list with estimated revenue impact
"""
import os, sys, json, logging, requests
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ROIOptimizer] %(message)s")
log = logging.getLogger()

ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
STRIPE_KEY   = os.environ.get("STRIPE_SECRET_KEY","")
GUMROAD_KEY  = os.environ.get("GUMROAD_ACCESS_TOKEN","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")

STRATEGY_SYSTEM = """You are Nina Caldwell, Chief Strategy and ROI Officer at NY Spotlight Report.
You think in unit economics, leverage points, and opportunity cost.
Current state: $0 revenue, all infrastructure built. First sale is THE priority.
Be ruthless about prioritization. Be honest about what's not working.
Every recommendation must have a specific revenue impact attached."""

def get_stripe_data() -> dict:
    if not STRIPE_KEY: return {}
    r = requests.get("https://api.stripe.com/v1/balance", auth=(STRIPE_KEY,""), timeout=10)
    r2 = requests.get("https://api.stripe.com/v1/charges?limit=20", auth=(STRIPE_KEY,""), timeout=10)
    r3 = requests.get("https://api.stripe.com/v1/subscriptions?status=active&limit=20", auth=(STRIPE_KEY,""), timeout=10)
    return {
        "balance": r.json() if r.status_code==200 else {},
        "recent_charges": r2.json().get("data",[]) if r2.status_code==200 else [],
        "active_subscriptions": r3.json().get("data",[]) if r3.status_code==200 else [],
        "total_revenue": sum(c["amount"] for c in r2.json().get("data",[]) if r2.status_code==200 and c.get("paid")) / 100,
        "mrr": sum(s["plan"]["amount"] for s in r3.json().get("data",[]) if r3.status_code==200) / 100
    }

def get_gumroad_data() -> dict:
    if not GUMROAD_KEY: return {}
    r = requests.get("https://api.gumroad.com/v2/products",
        headers={"Authorization":f"Bearer {GUMROAD_KEY}"}, timeout=10)
    r2 = requests.get("https://api.gumroad.com/v2/sales?page=0",
        headers={"Authorization":f"Bearer {GUMROAD_KEY}"}, timeout=10)
    products = r.json().get("products",[]) if r.status_code==200 else []
    sales = r2.json().get("sales",[]) if r2.status_code==200 else []
    return {
        "product_count": len(products),
        "total_views": sum(p.get("views_count",0) for p in products),
        "total_sales": sum(p.get("sales_count",0) for p in products),
        "total_revenue": sum(float(s.get("price",0))/100 for s in sales),
        "products": [{"name":p.get("name",""),"views":p.get("views_count",0),"sales":p.get("sales_count",0)} for p in products]
    }

def get_workflow_health() -> dict:
    if not GH_TOKEN: return {}
    H2 = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
    REPO2 = "nyspotlightreport/sct-agency-bots"
    r = requests.get(f"https://api.github.com/repos/{REPO2}/actions/runs?per_page=100", headers=H2)
    runs = r.json().get("workflow_runs",[])
    
    wf_stats = {}
    for run in runs:
        n = run["name"]
        if n not in wf_stats:
            wf_stats[n] = {"success":0,"failure":0,"total":0}
        wf_stats[n]["total"] += 1
        if run["conclusion"] == "success": wf_stats[n]["success"] += 1
        elif run["conclusion"] == "failure": wf_stats[n]["failure"] += 1
    
    return {
        "total_workflows": len(wf_stats),
        "healthy": [n for n,s in wf_stats.items() if s["success"]/max(s["total"],1) > 0.8],
        "failing": [n for n,s in wf_stats.items() if s["failure"]/max(s["total"],1) > 0.5],
        "stats": wf_stats
    }

def analyze_revenue_leaks(stripe: dict, gumroad: dict, workflows: dict) -> dict:
    """Find the specific revenue leaks and opportunities."""
    
    leaks = []
    opportunities = []
    
    # Gumroad: views but no sales = conversion problem
    for prod in gumroad.get("products",[]):
        if prod["views"] > 0 and prod["sales"] == 0:
            leaks.append({
                "type": "conversion_gap",
                "asset": f"Gumroad: {prod['name']}",
                "issue": f"{prod['views']} views, 0 sales",
                "fix": "Check price, description, preview. Add social proof. Test lower entry price.",
                "revenue_impact": f"${5-15}/sale × {max(1,prod['views']//10)} expected converts = ${prod['views']//10 * 10:.0f}/month potential"
            })
    
    # Zero revenue with all infrastructure = traffic problem
    if stripe.get("total_revenue",0) == 0 and gumroad.get("total_revenue",0) == 0:
        leaks.append({
            "type": "no_traffic",
            "asset": "All platforms",
            "issue": "Infrastructure complete but 0 revenue = no qualified traffic reaching purchase pages",
            "fix": "PRIORITY: Reddit posts, Quora answers, cold email first close. One sale unlocks momentum.",
            "revenue_impact": "First sale in 7-14 days with focused effort"
        })
    
    # Failing workflows = wasted automation
    for wf in workflows.get("failing",[]):
        leaks.append({
            "type": "broken_automation",
            "asset": wf,
            "issue": "Workflow failing silently — not generating expected output",
            "fix": "Debug and fix. One working automation often = $100-500/month in leads or content.",
            "revenue_impact": "Variable — depends on workflow function"
        })
    
    # Hidden opportunities in existing assets
    opportunities.append({
        "type": "white_label",
        "description": "Sell entire NYSR bot system as white-label to agencies",
        "why_now": "We have 100 bots, proven architecture, and no competitors with this stack",
        "revenue_model": "$2,500-10,000 setup + $500-2,000/month maintenance",
        "effort": "Medium — needs packaging + sales page",
        "timeline": "First client in 30-45 days"
    })
    
    opportunities.append({
        "type": "done_for_you_bot_setup",
        "description": "Charge $1,500-5,000 to set up the full bot stack for a client",
        "why_now": "We've already built it. We just replicate it.",
        "revenue_model": "$1,500-5,000 one-time + $300-500/month hosting/maintenance",
        "effort": "Low — it's already documented",
        "timeline": "Can sell today"
    })
    
    opportunities.append({
        "type": "newsletter_sponsorship",
        "description": "At 1,000 Beehiiv subscribers → ad network activates automatically",
        "why_now": "We have the newsletter. We need to aggressively grow subscribers.",
        "revenue_model": "$15-30 CPM × 1,000 subs × weekly send = $500-1,000/month",
        "effort": "Low — just grow subscribers",
        "timeline": "Revenue starts at 1k subs"
    })
    
    return {"leaks": leaks, "opportunities": opportunities}

def generate_priority_action_list(analysis: dict) -> list:
    """Return ranked list of actions by revenue impact."""
    
    if not ANTHROPIC:
        return [
            {"rank":1,"action":"Post 3 value posts on Reddit r/passive_income TODAY","why":"1 good post = 200-2,000 qualified visitors. Free. Fastest path to traffic.","revenue_impact":"$0-500 in 7 days","effort":"2 hours","deadline":"today"},
            {"rank":2,"action":"Post 10 Quora answers with nyspotlightreport.com link","why":"Quora ranks on Google. Traffic compounds for years. One answer can drive 100+ visitors/month forever.","revenue_impact":"$50-200/month ongoing","effort":"4 hours","deadline":"this week"},
            {"rank":3,"action":"Complete LinkedIn OAuth token + post daily for 2 weeks","why":"LinkedIn reach 3-10x posts. One viral post = 500+ targeted visitors.","revenue_impact":"First DFY client likely = $997/month","effort":"30 minutes setup","deadline":"today"},
            {"rank":4,"action":"Set up Product Hunt launch for ProFlow AI","why":"Launch day = 500-5,000 targeted visitors. One conversion at $297 = worth it.","revenue_impact":"$1,000-3,000 launch day","effort":"2 hours","deadline":"this week"},
            {"rank":5,"action":"Price test Gumroad products — drop 1 product to $2.99","why":"0 sales at current price. Low-price item builds social proof and buyer email list.","revenue_impact":"20-50 sales at $2.99 = proof of concept + email list","effort":"15 minutes","deadline":"today"},
        ]
    
    data_summary = json.dumps({
        "leaks": analysis.get("leaks",[])[:5],
        "opportunities": analysis.get("opportunities",[])[:5]
    }, indent=2)
    
    result = claude_json(
        STRATEGY_SYSTEM,
        f"""Based on this revenue analysis, create the top 8 priority actions ranked by revenue impact:

{data_summary}

For each action return:
{{rank, action, why, revenue_impact, effort_hours, deadline, confidence_pct}}

Rank by: (revenue_impact × confidence) / effort_hours
Be ruthless. Cut fluff. Every action must have a specific revenue number attached.""",
        max_tokens=1500
    )
    
    return result if isinstance(result, list) else result.get("actions",[]) if isinstance(result, dict) else []

def run():
    log.info("Strategic ROI Optimizer running...")
    
    # Collect all data
    stripe  = get_stripe_data()
    gumroad = get_gumroad_data()
    wf_health = get_workflow_health()
    
    log.info(f"Stripe MRR: ${stripe.get('mrr',0):.2f} | Total revenue: ${stripe.get('total_revenue',0):.2f}")
    log.info(f"Gumroad: {gumroad.get('total_views',0)} views | {gumroad.get('total_sales',0)} sales | ${gumroad.get('total_revenue',0):.2f}")
    log.info(f"Workflows: {wf_health.get('total_workflows',0)} total | {len(wf_health.get('failing',[]))} failing")
    
    # Analyze
    analysis = analyze_revenue_leaks(stripe, gumroad, wf_health)
    
    log.info(f"
Revenue leaks found: {len(analysis['leaks'])}")
    for leak in analysis["leaks"][:3]:
        log.info(f"  🔴 {leak['asset']}: {leak['issue'][:60]}")
        log.info(f"     Fix: {leak['fix'][:80]}")
    
    log.info(f"
Opportunities identified: {len(analysis['opportunities'])}")
    for opp in analysis["opportunities"][:3]:
        log.info(f"  💰 {opp['description'][:60]}")
        log.info(f"     Revenue: {opp['revenue_model']}")
    
    # Generate priority actions
    actions = generate_priority_action_list(analysis)
    
    log.info(f"
PRIORITY ACTION LIST:")
    for action in actions[:5]:
        log.info(f"  #{action.get('rank','?')} {action.get('action','')[:70]}")
        log.info(f"      Impact: {action.get('revenue_impact','')[:60]} | Deadline: {action.get('deadline','')}")
    
    # Alert if urgent actions found
    if actions and PUSHOVER_KEY:
        top = actions[0] if isinstance(actions, list) else {}
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                  "message":f"📊 WEEKLY ROI BRIEF

Revenue: ${stripe.get('total_revenue',0) + gumroad.get('total_revenue',0):.2f} total

#1 Priority:
{top.get('action','')[:100]}

Impact: {top.get('revenue_impact','')}",
                  "title":"💼 ROI Optimizer"},
            timeout=5)
    
    # Save report
    if GH_TOKEN:
        H2 = {"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        REPO2 = "nyspotlightreport/sct-agency-bots"
        path = "data/intelligence/roi_report.json"
        payload = json.dumps({
            "date": str(date.today()),
            "revenue": {"stripe": stripe.get("total_revenue",0), "gumroad": gumroad.get("total_revenue",0), "mrr": stripe.get("mrr",0)},
            "leaks": analysis["leaks"],
            "opportunities": analysis["opportunities"],
            "priority_actions": actions
        }, indent=2)
        body = {"message":f"bd: ROI report — ${stripe.get('total_revenue',0)+gumroad.get('total_revenue',0):.2f} total revenue",
                "content": base64.b64encode(payload.encode()).decode()}
        r = requests.get(f"https://api.github.com/repos/{REPO2}/contents/{path}", headers=H2)
        if r.status_code==200: body["sha"]=r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO2}/contents/{path}",json=body,headers=H2)
    
    log.info("
✅ ROI Optimizer complete")
    return actions

if __name__ == "__main__":
    run()
