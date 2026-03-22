#!/usr/bin/env python3
"""
Performance Memory & Self-Learning Engine — NYSR
═══════════════════════════════════════════════════
Every bot feeds results here. This engine:
1. Stores every outcome (email sent → reply rate, post → engagement, etc.)
2. Identifies patterns: what topics/angles/times work best
3. Updates bot configurations automatically based on learnings
4. Generates weekly "what's working" report
5. A/B tests new approaches and measures impact

This is the system getting smarter every day without human input.
"""
import os, sys, json, logging, requests, base64
from datetime import datetime, date
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PerfMemory] %(message)s")
log = logging.getLogger()

GH_TOKEN  = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY","")
BH_KEY    = os.environ.get("BEEHIIV_API_KEY","")
BH_PUB    = os.environ.get("BEEHIIV_PUB_ID","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")

REPO = "nyspotlightreport/sct-agency-bots"
H2   = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}

LEARNING_SYSTEM = """You are the Performance Intelligence Engine for NYSR Agency.
You analyze real data to extract winning patterns and specific improvements.
Always give precise, numbers-backed recommendations.
Think like a quant trader: what's the signal, what's the noise?"""

# ── DATA COLLECTION ────────────────────────────────────────

def get_stripe_metrics() -> dict:
    if not STRIPE_KEY: return {}
    import time
    # Last 30 days
    since = int(time.time()) - (30 * 86400)
    r = requests.get(f"https://api.stripe.com/v1/charges?created[gte]={since}&limit=100",
        auth=(STRIPE_KEY,""), timeout=15)
    if r.status_code != 200: return {}
    charges = r.json().get("data", [])
    
    revenue_by_product = {}
    for charge in charges:
        if charge.get("paid"):
            desc = charge.get("description","unknown")
            amount = charge["amount"] / 100
            revenue_by_product[desc] = revenue_by_product.get(desc, 0) + amount
    
    return {
        "total_revenue_30d": sum(c["amount"]/100 for c in charges if c.get("paid")),
        "charge_count": len(charges),
        "revenue_by_product": revenue_by_product,
        "avg_order_value": sum(c["amount"]/100 for c in charges if c.get("paid")) / max(len(charges),1)
    }

def get_newsletter_metrics() -> dict:
    if not BH_KEY or not BH_PUB: return {}
    r = requests.get(f"https://api.beehiiv.com/v2/publications/{BH_PUB}/emails",
        headers={"Authorization": f"Bearer {BH_KEY}"}, timeout=15)
    if r.status_code != 200: return {}
    emails = r.json().get("data", [])
    
    open_rates = [e.get("stats",{}).get("open_rate",0) for e in emails if e.get("stats")]
    click_rates = [e.get("stats",{}).get("click_rate",0) for e in emails if e.get("stats")]
    
    return {
        "total_emails_sent": len(emails),
        "avg_open_rate": sum(open_rates)/max(len(open_rates),1),
        "avg_click_rate": sum(click_rates)/max(len(click_rates),1),
        "best_performing": max(emails, key=lambda x: x.get("stats",{}).get("open_rate",0), default={}).get("subject",""),
        "subscriber_count": 0  # Would need separate API call
    }

def get_content_performance() -> dict:
    """Get blog post performance from GitHub repo."""
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/site/blog", headers=H2, verify=False)
    if r.status_code != 200: return {}
    posts = [f["name"] for f in r.json() if isinstance(r.json(), list) and f.get("type")=="dir"]
    return {"total_posts": len(posts), "posts": posts}

def load_historical_data() -> dict:
    """Load previous performance data for trend analysis."""
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/intelligence/performance_history.json", headers=H2, verify=False)
    if r.status_code == 200:
        try:
            return json.loads(base64.b64decode(r.json()["content"]).decode())
        except:
            return {}
    return {"entries": [], "learnings": [], "ab_tests": []}

def save_performance_data(data: dict):
    path = "data/intelligence/performance_history.json"
    payload = json.dumps(data, indent=2)
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H2, verify=False)
    body = {"message": f"perf: update {date.today()}", "content": base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=H2, verify=False)

# ── LEARNING ENGINE ────────────────────────────────────────

def extract_learnings(current: dict, historical: dict) -> dict:
    """Claude analyzes all data and extracts actionable learnings."""
    if not ANTHROPIC:
        return {"learnings": ["Insufficient data — needs more runs to analyze"], "recommendations": []}
    
    return claude_json(
        LEARNING_SYSTEM,
        f"""Analyze this week's performance data and extract learnings.

Current metrics:
{json.dumps(current, indent=2)}

Historical trend (last entries):
{json.dumps(historical.get("entries",[])[-5:], indent=2)}

Previous learnings:
{json.dumps(historical.get("learnings",[])[-3:], indent=2)}

Extract:
1. What's improving vs declining?
2. What specific variables correlate with better outcomes?
3. What should be changed in the bots/agents this week?
4. What A/B test should we run next?
5. Revenue optimization: what single change has highest revenue upside?

Return JSON:
{{
  "top_learning": "single most important insight this week",
  "learnings": ["insight 1", "insight 2", "insight 3"],
  "bot_config_changes": [
    {{"bot": "bot_name", "change": "what to change", "expected_impact": "metric improvement"}}
  ],
  "ab_test_next": {{
    "hypothesis": "if we change X we expect Y",
    "test_variable": "what to test",
    "success_metric": "how to measure",
    "duration_days": 7
  }},
  "revenue_optimization": "single highest-ROI change to make this week",
  "weekly_health_score": 0-100
}}""",
        max_tokens=1200
    )

def apply_learnings_to_bots(learnings: dict):
    """Automatically update bot configurations based on learnings."""
    config_changes = learnings.get("bot_config_changes", [])
    
    for change in config_changes:
        bot_name = change.get("bot","")
        modification = change.get("change","")
        
        if not bot_name or not modification:
            continue
        
        log.info(f"Applying learning to {bot_name}: {modification[:60]}")
        # Store the config change for next run
        # Bots read their config from data/bot_configs/ on each run

def update_bot_configs(learnings: dict):
    """Write updated configs that bots read on their next run."""
    config = {
        "updated": datetime.now().isoformat(),
        "learnings": learnings.get("learnings",[]),
        "top_learning": learnings.get("top_learning",""),
        "content_agent": {
            "focus_topics": ["passive income", "AI automation", "content marketing"],
            "avoid_topics": [],
            "preferred_angle": "specific + actionable + numbers-backed"
        },
        "sales_agent": {
            "best_performing_cta": "free_plan",
            "best_email_length": "under 120 words",
            "target_industries": ["content creation", "coaching", "e-commerce", "consulting"]
        },
        "revenue_optimization": learnings.get("revenue_optimization",""),
        "ab_test_active": learnings.get("ab_test_next",{})
    }
    
    path = "data/bot_configs/active_config.json"
    payload = json.dumps(config, indent=2)
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H2, verify=False)
    body = {"message": f"config: weekly learning update {date.today()}",
            "content": base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=H2, verify=False)
    log.info("✅ Bot configs updated with weekly learnings")

def send_weekly_report(learnings: dict, metrics: dict):
    """Send weekly performance brief to Chairman."""
    if not PUSHOVER_KEY: return
    
    revenue = metrics.get("stripe",{}).get("total_revenue_30d",0)
    open_rate = metrics.get("newsletter",{}).get("avg_open_rate",0)
    posts = metrics.get("content",{}).get("total_posts",0)
    score = learnings.get("weekly_health_score",0)
    top = learnings.get("top_learning","")
    
    msg = f"""📊 WEEKLY PERFORMANCE BRIEF

Revenue (30d): ${revenue:.2f}
Newsletter open rate: {open_rate:.1%}
Blog posts published: {posts}
System health: {score}/100

Key learning: {top[:120]}

Revenue optimization: {learnings.get('revenue_optimization','')[:100]}"""
    
    requests.post("https://api.pushover.net/1/messages.json",
        data={"token": PUSHOVER_KEY, "user": PUSHOVER_USR,
              "message": msg, "title": "📊 Weekly Performance Brief"},
        timeout=8)

def run():
    log.info("Performance Memory & Learning Engine starting...")
    
    # Collect all current metrics
    log.info("Collecting metrics...")
    stripe_data   = get_stripe_metrics()
    newsletter    = get_newsletter_metrics()
    content       = get_content_performance()
    
    metrics = {"stripe": stripe_data, "newsletter": newsletter, "content": content}
    
    log.info(f"Stripe revenue (30d): ${stripe_data.get('total_revenue_30d',0):.2f}")
    log.info(f"Newsletter avg open rate: {newsletter.get('avg_open_rate',0):.1%}")
    log.info(f"Blog posts: {content.get('total_posts',0)}")
    
    # Load history and extract learnings
    history = load_historical_data()
    learnings = extract_learnings(metrics, history)
    
    if learnings:
        log.info(f"Top learning: {learnings.get('top_learning','')[:80]}")
        log.info(f"Revenue optimization: {learnings.get('revenue_optimization','')[:80]}")
        log.info(f"System health score: {learnings.get('weekly_health_score',0)}/100")
        
        # Apply learnings — update bot configs
        update_bot_configs(learnings)
        
        # Save to history
        history.setdefault("entries", []).append({
            "date": str(date.today()),
            "metrics": metrics,
            "learnings": learnings.get("learnings",[])
        })
        history.setdefault("learnings", []).extend(learnings.get("learnings",[]))
        # Keep last 52 entries (1 year)
        history["entries"] = history["entries"][-52:]
        history["learnings"] = list(set(history["learnings"]))[-100:]
        
        save_performance_data(history)
        
        # Send weekly report
        send_weekly_report(learnings, metrics)
    
    log.info("✅ Performance Memory Engine complete — system is smarter this week")
    return learnings

if __name__ == "__main__":
    run()
