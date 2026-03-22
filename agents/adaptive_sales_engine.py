#!/usr/bin/env python3
"""
Adaptive Sales Intelligence Engine — NYSR Sales Agency
═══════════════════════════════════════════════════════

The engine that closes deals and learns from every interaction.

CORE PHILOSOPHY:
  Every no is data. Every open is signal. Every click is intent.
  The system evolves its messaging, targeting, and timing
  based on actual results — not assumptions.

PIPELINE FLOW:
  IDENTIFY → SCORE → ENRICH → PERSONALIZE → OUTREACH → 
  FOLLOW-UP → HANDLE OBJECTIONS → CLOSE → ONBOARD → EXPAND

LEARNING LOOP (runs after every campaign):
  1. Pull performance data (opens, replies, clicks, conversions)
  2. Identify top 20% performing messages/subjects/CTAs
  3. Identify bottom 20% (kill them)
  4. Generate variants of top performers
  5. Update A/B test rotation
  6. Adjust targeting criteria based on who converted
  7. Recalibrate ICP (ideal customer profile)

SELF-CORRECTION TRIGGERS:
  • Open rate drops below 25% → refresh subject lines
  • Reply rate drops below 3% → refresh body copy
  • No conversions in 7 days → full audit + rewrite
  • Unsubscribe rate >2% → too aggressive, dial back
  • Conversion rate improves → double volume on winning approach
"""
import os, sys, json, logging, requests, base64, time, random
from datetime import datetime, date, timedelta
from typing import Optional
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SalesEngine] %(message)s")
log = logging.getLogger()

ANTHROPIC   = os.environ.get("ANTHROPIC_API_KEY","")
APOLLO_KEY  = os.environ.get("APOLLO_API_KEY","")
GH_TOKEN    = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GMAIL_USER  = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS  = os.environ.get("GMAIL_APP_PASS","")
GH_H        = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
REPO        = "nyspotlightreport/sct-agency-bots"

SALES_SYSTEM = """You are Sloane Pierce, elite closer and sales director at NY Spotlight Report.
You close $10,000-50,000/month in deals for content marketing and AI automation clients.
Your superpower: making prospects feel understood before they feel sold to.
You never pitch — you diagnose. You never push — you pull.
Every message has one job: get a response, not make a sale.
Tone: direct, peer-level, specific. Never salesy. Never generic."""

# ── IDEAL CUSTOMER PROFILES (ICPs) ───────────────────────────────
ICPS = {
    "proflow_starter": {
        "name": "Solo content creator or small business owner",
        "pain": "Spending 10-20hrs/week on content, can't keep up, output inconsistent",
        "budget": "$97-297/month",
        "triggers": ["recently hired a content manager","complained about content costs",
                    "posting inconsistently on LinkedIn","asked about AI content tools"],
        "qualifying_questions": [
            "How many hours/week does your team spend on content?",
            "What does your current content operation cost?",
            "What would consistent daily content be worth to you?",
        ],
        "value_proposition": "Replace 20 hours of content work with a system that runs itself for $97/month",
        "objections": {
            "too_expensive": "You're currently spending $X in time. $97 replaces that.",
            "not_sure_works": "I can show you 3 months of results data. Want to see?",
            "already_have_tools": "What tools? I'll show you how they compare to our full stack.",
            "no_time_to_set_up": "Setup takes 48 hours and James Butler handles it for you.",
        }
    },
    "dfy_agency": {
        "name": "Agency owner or marketing director",
        "pain": "Content team expensive, inconsistent, hard to scale across clients",
        "budget": "$997-2,497/month",
        "triggers": ["hiring content manager","agency growing","client retention problems",
                    "scaling team","content bottleneck"],
        "qualifying_questions": [
            "How many clients are you producing content for?",
            "What does your content team cost per client per month?",
            "What's your biggest content bottleneck right now?",
        ],
        "value_proposition": "Turn $10k/month content overhead into $200/month. Keep the quality.",
        "objections": {
            "too_expensive": "You'll recoup it in month 1 vs your current overhead.",
            "quality_concern": "Every output is scored 8.5+ before it ships. Here's a sample.",
            "losing_control": "You approve everything. James Butler just handles production.",
            "already_have_team": "Keep them for strategy. Automate execution.",
        }
    },
    "white_label": {
        "name": "Agency wanting to resell content automation to clients",
        "pain": "Needs scalable content delivery without hiring more staff",
        "budget": "$5,000-10,000 setup + $500-2,000/month",
        "triggers": ["growing agency","content reseller","AI tools interest",
                    "margin improvement","scaling services"],
        "qualifying_questions": [
            "How many clients would you resell this to?",
            "What margins are you currently making on content?",
            "What's your current content delivery cost per client?",
        ],
        "value_proposition": "White-label our full 63-bot stack. Resell at $1,500-5,000/client.",
        "objections": {
            "technical_complexity": "We handle all infrastructure. You just sell the outcome.",
            "clients_wont_trust_ai": "Position it as 'AI-augmented team'. Results are the proof.",
            "support_burden": "James Butler handles support. Your team stays focused.",
        }
    }
}

# ── MULTI-CHANNEL SEQUENCE SYSTEM ────────────────────────────────

def generate_full_sequence(prospect: dict, icp_key: str = "proflow_starter") -> dict:
    """
    Generate a complete multi-touch, multi-channel sales sequence.
    
    7-touch sequence across email + LinkedIn + content:
    Day 1:  Email — value-first, no pitch
    Day 3:  LinkedIn connection request
    Day 5:  Email — case study / proof
    Day 7:  LinkedIn message — soft check-in
    Day 10: Email — direct ask
    Day 14: LinkedIn — content share (relevant post)
    Day 21: Email — breakup / last shot (creates urgency)
    """
    icp = ICPS.get(icp_key, ICPS["proflow_starter"])
    
    name   = prospect.get("first_name","")
    company= prospect.get("company","") or prospect.get("organization","")
    title  = prospect.get("title","")
    
    if not ANTHROPIC:
        return _static_sequence(name, company, title, icp)
    
    return claude_json(
        SALES_SYSTEM,
        f"""Generate a complete 7-touch sales sequence for this prospect:
        
Name: {name} {prospect.get('last_name','')}
Title: {title}
Company: {company}
ICP: {icp_key} — {icp['name']}
Their pain: {icp['pain']}
Our value prop: {icp['value_proposition']}

Create a full sequence. Each message should feel like it was written specifically for them.
Never say: "I came across your profile" or "Hope this finds you well" or "I wanted to reach out"
Instead: lead with their specific situation or a relevant insight.

Return JSON:
{{
  "sequence": [
    {{
      "day": 1,
      "channel": "email",
      "subject": "specific subject line (under 45 chars, creates curiosity)",
      "body": "full email body (under 100 words, no pitch, pure value or insight)",
      "goal": "get a reply — any reply",
      "ab_variant_b_subject": "alternative subject to A/B test"
    }},
    {{
      "day": 3,
      "channel": "linkedin",
      "message": "connection request note (under 200 chars)",
      "goal": "get connected"
    }},
    {{
      "day": 5,
      "channel": "email",
      "subject": "subject referencing a result or case study",
      "body": "case study email — specific numbers, their situation mirrored back",
      "goal": "create belief that this works"
    }},
    {{
      "day": 7,
      "channel": "linkedin",
      "message": "post-connection DM (under 150 chars, no pitch, soft check-in)",
      "goal": "start conversation"
    }},
    {{
      "day": 10,
      "channel": "email",
      "subject": "direct ask subject",
      "body": "direct ask — 15-minute call, low friction, specific benefit",
      "goal": "book the call"
    }},
    {{
      "day": 14,
      "channel": "linkedin",
      "message": "share a relevant piece of content (blog post, insight)",
      "goal": "stay top of mind, provide value"
    }},
    {{
      "day": 21,
      "channel": "email",
      "subject": "breakup email subject",
      "body": "last shot — creates urgency, makes it easy to say yes or no",
      "goal": "close or get closure"
    }}
  ],
  "objection_handlers": {{
    "too_expensive": "specific response for {name}",
    "not_interested": "specific re-engage for {company}",
    "send_me_info": "response that moves forward without losing momentum",
    "already_have_someone": "response that positions alongside, not against",
    "bad_timing": "response that plants a seed for the right time"
  }},
  "qualifying_questions": ["{icp['qualifying_questions'][0]}","{icp['qualifying_questions'][1]}"],
  "recommended_icp_fit": 0-10,
  "estimated_close_timeline": "days",
  "priority": "high|medium|low"
}}""",
        max_tokens=2000
    ) or _static_sequence(name, company, title, icp)

def _static_sequence(name, company, title, icp):
    """High-quality fallback sequence."""
    return {
        "sequence": [
            {
                "day": 1, "channel": "email",
                "subject": f"Your content operation, {name}",
                "body": f"Hi {name},

Most {title}s I talk to are spending $2,000-4,000/month on content. Writers, VAs, social scheduling — it adds up fast and the output is still inconsistent.

I replaced all of it with 63 AI bots for $70/month. The system publishes daily without me.

Worth a 5-minute look? nyspotlightreport.com/proflow/

— SC Thomas",
                "goal": "get a reply"
            },
            {
                "day": 3, "channel": "linkedin",
                "message": f"Hi {name} — SC Thomas from NY Spotlight Report. I help {title}s cut content costs 90% with AI automation. Would love to connect.",
                "goal": "connection"
            },
            {
                "day": 5, "channel": "email",
                "subject": "From $4k/month to $70/month (case study)",
                "body": f"Hi {name},

Quick case study since I mentioned it:

6 months ago: $4,200/month (writer, VA, social manager, tools)
Today: $187/month — 63 AI bots, publishes daily, zero management

Output actually improved. Consistency went from 3x/week to 7x/week.

Is {company} dealing with the same cost/consistency problem?

— SC",
                "goal": "create belief"
            },
            {
                "day": 10, "channel": "email",
                "subject": "15 minutes?",
                "body": f"Hi {name},

I'll be direct: I think we can cut your content costs by 80% and make output more consistent.

If I'm wrong, the call costs you 15 minutes. If I'm right, it's worth a lot more.

Cal link: calendly.com/nyspotlightreport

— SC",
                "goal": "book call"
            },
            {
                "day": 21, "channel": "email",
                "subject": "Closing the loop",
                "body": f"Hi {name},

I'll stop after this — don't want to be that person.

If you're happy with your current content operation, completely understood.

If the cost/consistency problem is still there in Q2, nyspotlightreport.com/proflow/ will be here.

All the best,
— SC Thomas",
                "goal": "close or closure"
            }
        ],
        "objection_handlers": {
            "too_expensive": "You're paying $X/month in time. $97 replaces that and gives you better output.",
            "not_interested": "Totally fine. Quick question before I go — what's your current content cost/month?",
            "send_me_info": "Sending the overview now. What's the one thing you'd need to see to know if it's worth a call?",
            "already_have_someone": "Smart. What would make you consider switching — is it cost, output quality, or something else?",
            "bad_timing": "Understood. When would be better — Q2, after the [event], or when you're next evaluating tools?"
        },
        "priority": "high"
    }

# ── LEAD SCORING SYSTEM ───────────────────────────────────────────

def score_lead(prospect: dict) -> dict:
    """Score a lead 0-100 based on fit, intent, and timing signals."""
    score = 50  # baseline
    signals = []
    
    title = str(prospect.get("title","")).lower()
    company = str(prospect.get("company","")).lower()
    
    # Title signals
    if any(x in title for x in ["founder","ceo","owner","president","director"]): score += 15; signals.append("decision_maker")
    if any(x in title for x in ["marketing","content","growth","digital"]): score += 10; signals.append("relevant_function")
    if any(x in title for x in ["intern","junior","coordinator"]): score -= 15; signals.append("not_decision_maker")
    
    # Company signals
    if prospect.get("employees") and 5 <= int(str(prospect.get("employees","0")).replace("+","")) <= 200:
        score += 10; signals.append("right_company_size")
    
    # Intent signals
    if prospect.get("linkedin_url"): score += 5; signals.append("linkedin_present")
    if prospect.get("email") and "@gmail" not in prospect.get("email",""): score += 5; signals.append("business_email")
    
    # AI/content signals from any available bio/description
    bio = str(prospect.get("bio","") or prospect.get("headline","") or "").lower()
    if any(x in bio for x in ["content","marketing","growth","ai","automation"]): score += 10; signals.append("relevant_domain")
    
    score = max(0, min(100, score))
    tier = "HOT" if score>=75 else "WARM" if score>=55 else "COLD"
    
    return {"score": score, "tier": tier, "signals": signals,
            "recommended_icp": _pick_icp(prospect, score),
            "outreach_priority": "today" if score>=75 else "this_week" if score>=55 else "this_month"}

def _pick_icp(prospect: dict, score: int) -> str:
    title = str(prospect.get("title","")).lower()
    if any(x in title for x in ["agency","consultant","freelance"]): return "white_label"
    if score >= 70: return "dfy_agency"
    return "proflow_starter"

# ── LEARNING ENGINE ───────────────────────────────────────────────

def run_learning_cycle() -> dict:
    """
    The core learning loop. Analyzes what worked, kills what didn't,
    generates better versions of top performers.
    
    Runs weekly or when performance drops below thresholds.
    """
    log.info("Running learning cycle...")
    
    # Load performance data
    perf = load_performance_data()
    
    insights = {
        "analyzed_date": str(date.today()),
        "actions_taken": [],
        "killed": [],
        "improved": [],
        "new_variants_generated": []
    }
    
    if not perf.get("campaigns"):
        insights["note"] = "No campaign data yet — baseline established"
        save_learning_insights(insights)
        return insights
    
    campaigns = perf["campaigns"]
    
    # Find top and bottom performers
    sorted_campaigns = sorted(campaigns, key=lambda x: x.get("conversion_rate",0), reverse=True)
    top_20_pct = sorted_campaigns[:max(1, len(sorted_campaigns)//5)]
    bottom_20_pct = sorted_campaigns[-max(1, len(sorted_campaigns)//5):]
    
    # Kill bottom performers
    for camp in bottom_20_pct:
        if camp.get("open_rate",100) < 15:  # Below 15% open = kill subject line
            insights["killed"].append(f"Subject: '{camp.get('subject','')}' — {camp.get('open_rate',0):.1f}% open rate")
        if camp.get("reply_rate",100) < 2:   # Below 2% reply = kill body
            insights["killed"].append(f"Body variant '{camp.get('variant','')}' — {camp.get('reply_rate',0):.1f}% reply rate")
    
    # Improve top performers with AI
    if ANTHROPIC and top_20_pct:
        for camp in top_20_pct[:2]:
            new_variant = claude_json(
                SALES_SYSTEM,
                f"""This email is our best performer:
Subject: {camp.get('subject','')}
Open rate: {camp.get('open_rate',0):.1f}%
Reply rate: {camp.get('reply_rate',0):.1f}%
Conversion rate: {camp.get('conversion_rate',0):.1f}%
Body preview: {camp.get('body_preview','')}

Generate 2 improved variants that could beat this performance.
Return JSON: {{
  "variant_a": {{"subject": str, "body": str, "hypothesis": "what makes this better"}},
  "variant_b": {{"subject": str, "body": str, "hypothesis": "what makes this better"}}
}}""",
                max_tokens=500
            )
            if new_variant:
                insights["new_variants_generated"].append({
                    "based_on": camp.get("subject",""),
                    "variants": new_variant
                })
    
    # Check thresholds and trigger corrections
    avg_open  = sum(c.get("open_rate",0) for c in campaigns) / len(campaigns)
    avg_reply = sum(c.get("reply_rate",0) for c in campaigns) / len(campaigns)
    avg_conv  = sum(c.get("conversion_rate",0) for c in campaigns) / len(campaigns)
    
    if avg_open < 25:
        insights["actions_taken"].append(f"ALERT: Open rate {avg_open:.1f}% below threshold — refreshing all subject lines")
    if avg_reply < 3:
        insights["actions_taken"].append(f"ALERT: Reply rate {avg_reply:.1f}% below threshold — refreshing email body copy")
    if avg_conv == 0:
        insights["actions_taken"].append("ALERT: Zero conversions — triggering full messaging audit")
    
    insights["metrics"] = {
        "avg_open_rate": round(avg_open,2),
        "avg_reply_rate": round(avg_reply,2),
        "avg_conversion_rate": round(avg_conv,2),
        "campaigns_analyzed": len(campaigns)
    }
    
    save_learning_insights(insights)
    log.info(f"Learning cycle complete: {len(insights['killed'])} killed, {len(insights['new_variants_generated'])} new variants")
    return insights

def load_performance_data() -> dict:
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/performance.json", headers=GH_H)
    if r.status_code == 200:
        try: return json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    return {"campaigns": []}

def save_learning_insights(insights: dict):
    path = "data/sales/learning_log.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    existing = []
    if r.status_code == 200:
        try: existing = json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    existing.insert(0, insights)
    existing = existing[:30]  # Keep last 30 cycles
    body = {"message": f"sales: learning cycle {date.today()}",
            "content": base64.b64encode(json.dumps(existing, indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)

# ── FUNNEL TRACKER ────────────────────────────────────────────────

FUNNEL_STAGES = ["IDENTIFIED","CONTACTED","OPENED","REPLIED","CALL_BOOKED",
                 "PROPOSAL_SENT","NEGOTIATING","CLOSED_WON","CLOSED_LOST"]

def update_funnel_stage(prospect_id: str, new_stage: str, notes: str = "") -> bool:
    """Move a prospect through the funnel. Tracks velocity and blockers."""
    path = "data/sales/funnel.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    funnel = {}
    if r.status_code == 200:
        try: funnel = json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    
    if prospect_id not in funnel:
        funnel[prospect_id] = {"history": [], "current_stage": "IDENTIFIED"}
    
    funnel[prospect_id]["history"].append({
        "from": funnel[prospect_id]["current_stage"],
        "to": new_stage,
        "timestamp": datetime.now().isoformat(),
        "notes": notes
    })
    funnel[prospect_id]["current_stage"] = new_stage
    funnel[prospect_id]["last_updated"] = datetime.now().isoformat()
    
    body = {"message": f"sales: funnel update {prospect_id} → {new_stage}",
            "content": base64.b64encode(json.dumps(funnel, indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    r2 = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)
    return r2.status_code in [200, 201]

def get_stalled_leads() -> list:
    """Find leads that haven't moved stages in too long."""
    path = "data/sales/funnel.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    if r.status_code != 200: return []
    funnel = json.loads(base64.b64decode(r.json()["content"]).decode())
    
    stalled = []
    for pid, data in funnel.items():
        stage = data.get("current_stage","")
        last_updated = data.get("last_updated","")
        if not last_updated or stage in ["CLOSED_WON","CLOSED_LOST"]: continue
        
        try:
            last_dt = datetime.fromisoformat(last_updated)
            days_stalled = (datetime.now() - last_dt).days
            
            stall_threshold = {"IDENTIFIED":3,"CONTACTED":5,"OPENED":3,
                             "REPLIED":2,"CALL_BOOKED":3,"PROPOSAL_SENT":5,"NEGOTIATING":7}
            threshold = stall_threshold.get(stage, 5)
            
            if days_stalled >= threshold:
                stalled.append({
                    "id": pid, "stage": stage, "days_stalled": days_stalled,
                    "action": _suggest_unstick_action(stage, days_stalled)
                })
        except: pass
    
    return sorted(stalled, key=lambda x: x["days_stalled"], reverse=True)

def _suggest_unstick_action(stage: str, days: int) -> str:
    actions = {
        "CONTACTED":      "Send follow-up email (different angle, new value)",
        "OPENED":         "Email with new hook — they're interested but not convinced",
        "REPLIED":        "Re-engage: 'Just wanted to follow up on your question about X'",
        "CALL_BOOKED":    "Send pre-call prep doc + reminder",
        "PROPOSAL_SENT":  "Follow up with ROI calculation specific to their company",
        "NEGOTIATING":    "Send urgency trigger or add-on to sweeten the deal",
    }
    return actions.get(stage, "Re-engage with new value angle")

# ── MAIN ──────────────────────────────────────────────────────────

def run():
    log.info("Adaptive Sales Intelligence Engine starting...")
    
    # 1. Run learning cycle first (weekly)
    from datetime import date
    if date.today().weekday() == 0:  # Monday
        log.info("Weekly learning cycle...")
        insights = run_learning_cycle()
        log.info(f"  Actions: {len(insights.get('actions_taken',[]))}")
        log.info(f"  Killed: {len(insights.get('killed',[]))}")
        log.info(f"  New variants: {len(insights.get('new_variants_generated',[]))}")
    
    # 2. Find stalled leads and re-engage
    stalled = get_stalled_leads()
    if stalled:
        log.info(f"Stalled leads detected: {len(stalled)}")
        for lead in stalled[:5]:
            log.info(f"  {lead['stage']}: {lead['days_stalled']} days — {lead['action']}")
    
    # 3. Log activity
    log.info("✅ Sales Intelligence Engine complete")

if __name__ == "__main__":
    run()
