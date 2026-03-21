#!/usr/bin/env python3
"""
Alex Mercer Orchestrator — NYSR Agency Master Brain
Powered by Claude. The CEO of the entire autonomous system.

Every morning this agent:
1. Analyzes yesterday's performance
2. Decides what content/outreach to prioritize today
3. Spawns all sub-agents with specific instructions
4. Monitors results and adapts

This is the system becoming self-aware of its own performance
and continuously improving without human input.
"""
import os, sys, json, logging, subprocess, requests
from datetime import datetime
sys.path.insert(0,".")
from agents.claude_core import claude, claude_json
logging.basicConfig(level=logging.INFO, format="%(asctime)s [AlexMercer] %(message)s")
log = logging.getLogger()

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
STRIPE_KEY    = os.environ.get("STRIPE_SECRET_KEY","")
PUSHOVER_KEY  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN","")

ALEX_PERSONA = """You are Alex Mercer, CEO of NY Spotlight Report's internal AI agency.
You are analytical, profit-first, and relentless about execution.
Your job: review performance data and give specific, actionable directives.
You never give generic advice. Every recommendation includes a specific number or metric."""

def get_performance_data() -> dict:
    """Pull yesterday's performance across all systems."""
    data = {"date": datetime.now().strftime("%Y-%m-%d"), "revenue": 0, "subs": 0}
    
    if STRIPE_KEY:
        import time
        yesterday_start = int(time.time()) - 86400
        r = requests.get(
            f"https://api.stripe.com/v1/charges?created[gte]={yesterday_start}&limit=100",
            auth=(STRIPE_KEY,""), timeout=15)
        if r.status_code == 200:
            charges = r.json().get("data",[])
            data["revenue"] = sum(c["amount"] for c in charges if c["paid"]) / 100
            data["stripe_charges"] = len(charges)
    
    return data

def analyze_and_direct(perf: dict) -> dict:
    """Alex Mercer analyzes performance and gives today's directives."""
    return claude_json(
        ALEX_PERSONA,
        f"""Review yesterday's performance and issue today's directives.

Performance data: {json.dumps(perf)}
Today: {datetime.now().strftime("%A, %B %d %Y")}

Based on this data, decide:
1. What should Content Agent focus on today? (topic direction, angle, platform emphasis)
2. What should Sales Agent do differently? (target industry, email angle, CTA type)
3. What trend should Trend Agent watch? (news categories, search terms)
4. Any experiments to run today?
5. Revenue forecast for this week based on trajectory

Return JSON with:
- content_directive: specific instruction for Content Agent today
- sales_directive: specific instruction for Sales Agent today
- trend_keywords: list of 3 trending topics to monitor
- experiment: one A/B test to run this week
- revenue_forecast_week: dollar estimate
- priority_action: the single most important thing to do today
- morning_briefing: 3-sentence summary for S.C. Thomas""",
        max_tokens=800
    )

def send_morning_briefing(directives: dict, perf: dict):
    """Send morning briefing to S.C. Thomas via push notification + email."""
    briefing = directives.get("morning_briefing","System running.")
    revenue  = perf.get("revenue", 0)
    forecast = directives.get("revenue_forecast_week", 0)
    priority = directives.get("priority_action","")
    
    msg = f"""📊 NYSR Morning Briefing
Revenue yesterday: ${revenue:.2f}
Week forecast: ${forecast}
Priority: {priority}

{briefing}"""
    
    if PUSHOVER_KEY:
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token": PUSHOVER_KEY, "user": PUSHOVER_USER,
                  "message": msg, "title": "NYSR Daily Brief"},
            timeout=10)
    log.info(f"Morning brief sent: ${revenue:.2f} yesterday")

def run():
    log.info("=== ALEX MERCER ORCHESTRATOR STARTING ===")
    log.info(f"Date: {datetime.now().strftime('%A %B %d %Y %H:%M')}")
    
    # 1. Pull performance
    perf = get_performance_data()
    log.info(f"Yesterday revenue: ${perf.get('revenue',0):.2f}")
    
    # 2. Get directives from Alex Mercer (Claude)
    directives = analyze_and_direct(perf)
    log.info(f"Priority today: {directives.get('priority_action','')}")
    
    # 3. Brief the Chairman
    send_morning_briefing(directives, perf)
    
    # 4. Save directives for sub-agents to read
    with open("/tmp/todays_directives.json","w") as f:
        json.dump(directives, f, indent=2)
    
    log.info("✅ Orchestrator complete — all agents will use today's directives")
    log.info(f"Revenue forecast this week: ${directives.get('revenue_forecast_week',0)}")

if __name__ == "__main__":
    run()
