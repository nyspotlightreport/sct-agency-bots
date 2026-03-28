# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
Zero-Resistance Sales Engine — NYSR
Lead identified → Closed in minimum touches. Maximum velocity.

ZERO-RESISTANCE PRINCIPLES:
1. Remove every friction point before the prospect hits it
2. Pre-handle objections in the approach, not the reply
3. Make saying YES easier than saying NO
4. Never sell features — sell the exact outcome they want
5. Use their own language back at them
6. Create urgency from their situation, not artificial pressure
7. The sequence adapts to their behavior in real time

VELOCITY PROTOCOL:
  HOT lead (score 75+) → same-day outreach → 4-touch close in 10 days
  WARM lead (score 55+) → 24hr outreach → 7-touch close in 21 days
  COLD lead (score 35+) → 48hr outreach → nurture sequence, 60 days
  
SELF-CORRECTION:
  After every 50 sends → analyze performance → update templates
  After every closed deal → extract what worked → amplify it
  After every lost deal → extract objection → pre-handle it
"""
import os, sys, json, logging, requests, base64, smtplib, time
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ZeroResistanceSales] %(message)s")
log = logging.getLogger()

ANTHROPIC  = os.environ.get("ANTHROPIC_API_KEY","")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY","")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_USER = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_PASS = os.environ.get("GMAIL_APP_PASS","")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY","")
GH_TOKEN   = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H       = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
REPO       = "nyspotlightreport/sct-agency-bots"

CLOSER_VOICE = """You are Sloane Pierce, the highest-converting sales agent at NY Spotlight Report.
You close 23% of outreach — 4x industry average. Your secret: you sound like a peer, not a salesperson.

Your rules:
- NEVER use these words: "excited", "leverage", "synergy", "reach out", "touch base", "circle back"
- NEVER start with "I" — always start with them
- NEVER pitch the product — pitch the outcome they get
- ALWAYS include ONE specific number relevant to their situation
- Messages under 80 words convert 3x better than long ones
- Subject lines that create curiosity beat subject lines that explain
- Always make the next step feel tiny (15 min call, not "demo")"""

# ── ICP DATABASE WITH BUYING PSYCHOLOGY ──────────────────────────
ICP_PROFILES = {
    "content_exhausted_founder": {
        "trigger_words": ["content", "marketing", "social media", "blog", "newsletter", "posting"],
        "core_pain": "Spending 15+ hours/week on content that doesn't compound",
        "desired_outcome": "Content that runs itself and actually grows the business",
        "psychological_driver": "Time freedom + proof that it works at their scale",
        "price_anchor": "$97-297/mo (ProFlow) vs $2k-4k/mo current spend",
        "best_hook": "What if your content team cost $70/month and never missed a deadline?",
        "objection_pre_handle": "I know you've probably tried AI tools. This is different — it's an entire system, not a tool.",
        "close_mechanism": "free_plan_then_upgrade",
        "urgency": "Every week you delay, you're spending another $X on your current setup"
    },
    "agency_scaling_pain": {
        "trigger_words": ["agency", "clients", "scaling", "team", "hire", "overhead", "margin"],
        "core_pain": "Content costs eating margin, can't scale without hiring",
        "desired_outcome": "Deliver more to more clients without adding headcount",
        "psychological_driver": "Profit margin + ability to take on more clients",
        "price_anchor": "$997-2497/mo vs $5k-15k/mo current content overhead",
        "best_hook": "How are you handling content for clients as you scale — still hiring for each one?",
        "objection_pre_handle": "Client quality concerns are valid. Every output scores 8.5+ before it ships.",
        "close_mechanism": "roi_calculator_then_proposal",
        "urgency": "Every new client you take on without this is another margin problem"
    },
    "solopreneur_overwhelmed": {
        "trigger_words": ["solo", "one person", "overwhelmed", "everything myself", "wearing all hats"],
        "core_pain": "Doing everything alone, content is the first thing dropped",
        "desired_outcome": "A system that handles marketing so they can focus on product/service",
        "psychological_driver": "Simplicity + reliability + not having to think about it",
        "price_anchor": "$97/mo (ProFlow Starter) vs the cost of inconsistency",
        "best_hook": "What's the one thing you keep putting off because you don't have time?",
        "objection_pre_handle": "You don't need to manage it — that's the point. Setup takes 48 hours.",
        "close_mechanism": "low_barrier_trial",
        "urgency": "Inconsistent presence is actively costing you deals you never even see"
    }
}

# ── INTELLIGENT LEAD ENRICHMENT ────────────────────────────────────

def enrich_and_score_lead(prospect: dict) -> dict:
    """Score 0-100 across 5 dimensions. Assign ICP. Set velocity."""
    title   = str(prospect.get("title","")).lower()
    company = str(prospect.get("company","") or prospect.get("organization",""))
    bio     = str(prospect.get("bio","") or prospect.get("headline","") or "").lower()
    email   = str(prospect.get("email",""))
    
    scores = {"fit":50, "authority":50, "intent":50, "timing":50, "access":50}
    signals = []
    
    # FIT — does this match our ICP?
    if any(x in title for x in ["founder","ceo","owner","president","partner"]): scores["fit"]+=20; signals.append("decision_maker")
    if any(x in title+bio for x in ["content","marketing","growth","digital","creative"]): scores["fit"]+=15; signals.append("relevant_function")
    if any(x in bio for x in ["ai","automation","bot","saas","software"]): scores["fit"]+=10; signals.append("ai_interest")
    
    # AUTHORITY — can they actually buy?
    if any(x in title for x in ["founder","ceo","owner","director","vp","head of"]): scores["authority"]+=20; signals.append("budget_authority")
    if any(x in title for x in ["manager","coordinator","specialist","analyst"]): scores["authority"]-=10
    
    # INTENT — signals they need what we sell
    if any(x in bio for x in ["content","blog","newsletter","social","marketing","growth"]): scores["intent"]+=20; signals.append("content_focus")
    if any(x in bio for x in ["scaling","growing","hiring","building","launch"]): scores["intent"]+=15; signals.append("growth_mode")
    
    # TIMING — are they ready now?
    if any(x in bio for x in ["recently","just","new","starting","launched","building"]): scores["timing"]+=15; signals.append("recent_activity")
    
    # ACCESS — can we reach them?
    if email and "@gmail" not in email and "@yahoo" not in email: scores["access"]+=20; signals.append("business_email")
    if prospect.get("linkedin_url"): scores["access"]+=10; signals.append("linkedin_present")
    
    # Normalize
    for k in scores: scores[k] = max(0, min(100, scores[k]))
    overall = round(sum(scores.values())/5, 1)
    
    # Assign ICP
    icp = "content_exhausted_founder"
    if any(x in title+bio for x in ["agency","consultant","freelance","studio"]): icp = "agency_scaling_pain"
    elif any(x in bio for x in ["solo","one person","side project","bootstrap"]): icp = "solopreneur_overwhelmed"
    
    tier = "HOT" if overall>=72 else "WARM" if overall>=55 else "COLD"
    velocity = "same_day" if tier=="HOT" else "24_hours" if tier=="WARM" else "48_hours"
    
    return {
        **prospect,
        "lead_score": overall,
        "score_breakdown": scores,
        "tier": tier,
        "signals": signals,
        "assigned_icp": icp,
        "outreach_velocity": velocity,
        "scored_at": datetime.now().isoformat()
    }

# ── ZERO-RESISTANCE MESSAGE GENERATOR ─────────────────────────────

def generate_zero_resistance_sequence(lead: dict) -> dict:
    """
    Generate a personalized sequence that pre-handles every objection
    before it's raised. Uses their exact language from bio/title.
    """
    icp_key  = lead.get("assigned_icp","content_exhausted_founder")
    icp      = ICP_PROFILES[icp_key]
    tier     = lead.get("tier","WARM")
    name     = lead.get("first_name","") or lead.get("name","").split()[0] if lead.get("name") else "there"
    title    = lead.get("title","")
    company  = lead.get("company","") or lead.get("organization","")
    bio      = lead.get("bio","") or lead.get("headline","")
    
    # Number of touches based on tier
    touch_count = 4 if tier=="HOT" else 7 if tier=="WARM" else 5
    
    if ANTHROPIC:
        return claude_json(
            CLOSER_VOICE,
            f"""Create a {touch_count}-touch zero-resistance sales sequence.

PROSPECT:
  Name: {name}
  Title: {title}
  Company: {company}
  Bio: {bio[:200]}
  Lead tier: {tier}
  ICP: {icp_key}
  Core pain: {icp["core_pain"]}
  What they want: {icp["desired_outcome"]}
  Psychological driver: {icp["psychological_driver"]}
  Best hook: {icp["best_hook"]}
  Pre-handled objection: {icp["objection_pre_handle"]}
  Price anchor: {icp["price_anchor"]}

SEQUENCE RULES:
- Day 1 email: curiosity hook, under 75 words, NO pitch, ends with one question
- Day 3 LinkedIn: connection note under 200 chars, peer-to-peer
- Day 5 email: specific case study with numbers matching their situation, under 100 words
- Day 8 email (WARM/HOT): direct ask for 15-min call, make yes feel tiny
- Day 14 email: ROI calculation specific to THEIR company size/type
- Day 21 email: urgency from THEIR situation (not artificial), breakup framing
- (HOT only) Day 2: LinkedIn DM within 24hrs of connection

For each touch, include:
- subject (for emails) — must create curiosity, not reveal too much
- body — use THEIR words from bio, reference their company/title
- goal — single micro-commitment you want
- if_they_reply_with_interest — instant next step message
- if_no_response — what triggers next touch

Return valid JSON:
{{
  "lead_id": "{lead.get("id", lead.get("email","unknown"))}",
  "tier": "{tier}",
  "icp": "{icp_key}",
  "recommended_product": "proflow_starter|proflow_growth|dfy_agency",
  "estimated_close_days": number,
  "sequence": [
    {{
      "touch": 1,
      "day": 1,
      "channel": "email",
      "subject": "subject line",
      "body": "full personalized message",
      "goal": "single micro-commitment",
      "if_interested_reply": "instant follow message",
      "ab_subject_b": "alternative subject to test"
    }}
  ],
  "prehandled_objections": {{
    "too_expensive": "specific response for this prospect",
    "not_right_now": "response",
    "we_have_someone": "response",
    "send_me_info": "response that moves forward",
    "how_is_this_different": "response specific to their situation"
  }},
  "close_script": "word-for-word close for when they show interest",
  "urgency_trigger": "their-situation-specific reason to act now"
}}""",
            max_tokens=2500
        ) or _fallback_sequence(lead, icp, name, company, title)
    
    return _fallback_sequence(lead, icp, name, company, title)

def _fallback_sequence(lead, icp, name, company, title):
    tier = lead.get("tier","WARM")
    return {
        "lead_id": lead.get("email","unknown"),
        "tier": tier,
        "icp": lead.get("assigned_icp","content_exhausted_founder"),
        "recommended_product": "proflow_starter",
        "estimated_close_days": 10 if tier=="HOT" else 21,
        "sequence": [
            {
                "touch": 1, "day": 1, "channel": "email",
                "subject": f"Your content operation, {name}",
                "body": f"Hi {name},\n\n{title}s I talk to are usually spending $2k-4k/month on content — writers, tools, social managers. Output still inconsistent.\n\nWe replaced all of it for $70/month. 63 AI bots, publishes daily.\n\nWorth a look? nyspotlightreport.com/proflow/\n\n— SC Thomas",
                "goal": "click or reply",
                "if_interested_reply": f"Great — what does {company}'s current content spend look like? I can run the numbers for you.",
                "ab_subject_b": f"{company}'s content costs"
            },
            {
                "touch": 2, "day": 5, "channel": "email",
                "subject": "From $4,200 to $187/month (our numbers)",
                "body": f"Hi {name},\n\nOur operation before: $4,200/month. Writer, VA, social manager, tools.\nOur operation now: $187/month. 63 bots, publishes 7x/week.\n\nSame output. Better consistency. Zero management.\n\nIs {company} dealing with the same cost creep?\n\n— SC",
                "goal": "get a reply confirming the pain",
                "if_interested_reply": "I'll send you the full breakdown — what's your current content spend monthly?"
            },
            {
                "touch": 3, "day": 10, "channel": "email",
                "subject": "15 minutes?",
                "body": f"Hi {name},\n\nDirectly: I think we can cut {company}'s content costs 80% and make output more consistent. 15-min call to show you?\n\ncalendly.com/nyspotlightreport\n\n— SC",
                "goal": "book the call"
            },
            {
                "touch": 4, "day": 21, "channel": "email",
                "subject": "Closing the loop",
                "body": f"Hi {name},\n\nLast note — if content cost and consistency aren't a problem, totally understood.\n\nIf they ever are: nyspotlightreport.com/proflow/\n\nAll the best,\n— SC Thomas",
                "goal": "close or get clear no"
            }
        ],
        "prehandled_objections": {
            "too_expensive": f"You're currently spending more than $97/month in time alone. This replaces that.",
            "not_right_now": "What would need to change for timing to be right — budget cycle, headcount, something else?",
            "send_me_info": "Sending the overview. One question first: what's the biggest content bottleneck at {company} right now?",
            "how_is_this_different": "Every AI 'tool' writes one thing. This is 63 bots running an entire operation — publishing, scheduling, outreach, SEO — all connected."
        },
        "close_script": f"Based on what you've told me about {company}, the ROI is {int(lead.get('lead_score',60))}x in year one. Want me to send a proposal with your specific numbers?",
        "urgency_trigger": f"Every month you delay is another month at your current content cost. At {icp['price_anchor']}, the payback period is under 30 days."
    }

# ── EMAIL SENDER ───────────────────────────────────────────────────

def send_outreach_email(to_email: str, subject: str, body: str, name: str = "") -> bool:
    """Send a personalized outreach email and log it."""
# AG-HARD-DISABLED-GMAIL-ZERO:     if not GMAIL_PASS or not to_email:
        log.warning(f"  Email not sent — missing credentials or address")
        return False
    try:
        msg = MIMEMultipart("alternative")
# AG-HARD-DISABLED-GMAIL-ZERO:         msg["From"]    = f"SC Thomas <{GMAIL_USER}>"
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP_SSL("[GMAIL-SMTP-REDACTED]", 465) as s:
# AG-NUCLEAR-GMAIL-ZERO-20260328:             s.login(GMAIL_USER, GMAIL_PASS)
# AG-HARD-DISABLED-GMAIL-ZERO:             s.send_message(msg)
        log.info(f"  ✅ Sent to {name} <{to_email}>: {subject}")
        _log_outreach(to_email, subject, body)
        return True
    except Exception as e:
        log.error(f"  Email failed: {e}")
        return False

def _log_outreach(email, subject, body):
    path = "data/sales/outreach_log.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    log_data = []
    if r.status_code == 200:
        try: log_data = json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    log_data.insert(0, {"email":email,"subject":subject,"sent_at":datetime.now().isoformat(),"status":"sent"})
    log_data = log_data[:1000]
    body_data = {"message":f"sales: outreach logged {email[:20]}","content":base64.b64encode(json.dumps(log_data,indent=2).encode()).decode()}
    if r.status_code == 200: body_data["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body_data, headers=GH_H)

# ── APOLLO PROSPECT PULL ───────────────────────────────────────────

def pull_hot_prospects_from_apollo(count: int = 50) -> list:
    """Pull qualified prospects from Apollo. Score and rank them."""
    if not APOLLO_KEY:
        log.warning("No Apollo key — using cached prospects")
        return _load_cached_prospects()
    
    # Search for ICP-matching prospects
    searches = [
        {"person_titles":["founder","ceo","owner"],"q_keywords":"content marketing","per_page":25},
        {"person_titles":["marketing director","head of marketing","vp marketing"],"q_keywords":"","per_page":25},
        {"person_titles":["agency owner","agency founder"],"q_keywords":"content","per_page":25},
    ]
    
    all_prospects = []
    for search in searches:
        r = requests.post("https://api.apollo.io/v1/mixed_people/search",
            headers={"Content-Type":"application/json","Cache-Control":"no-cache"},
            json={**search,"api_key":APOLLO_KEY},
            timeout=15, verify=False)
        if r.status_code == 200:
            people = r.json().get("people",[])
            all_prospects.extend(people)
            log.info(f"  Apollo returned {len(people)} prospects for: {search.get('person_titles',[''])[0]}")
    
    # Score all
    scored = [enrich_and_score_lead(p) for p in all_prospects if p.get("email")]
    scored.sort(key=lambda x: x.get("lead_score",0), reverse=True)
    
    # Cache them
    hot = [p for p in scored if p.get("tier") in ["HOT","WARM"]][:count]
    _cache_prospects(hot)
    return hot

def _load_cached_prospects():
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/prospect_cache.json", headers=GH_H)
    if r.status_code == 200:
        try: return json.loads(base64.b64decode(r.json()["content"]).decode())[:20]
        except Exception:  # noqa: bare-except

            pass
    return []

def _cache_prospects(prospects: list):
    path = "data/sales/prospect_cache.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    existing = []
    if r.status_code == 200:
        try: existing = json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    # Merge, deduplicate by email
    all_p = {p.get("email",""):p for p in existing+prospects if p.get("email")}
    merged = sorted(all_p.values(), key=lambda x: x.get("lead_score",0), reverse=True)[:500]
    body = {"message":f"sales: prospect cache updated {len(merged)} leads",
            "content":base64.b64encode(json.dumps(merged,indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)

# ── DAILY SALES RUN ────────────────────────────────────────────────

def run():
    log.info("Zero-Resistance Sales Engine starting...")
    today_stats = {"prospects_pulled":0,"sequences_generated":0,"emails_sent":0,"errors":[]}
    
    # Pull fresh prospects
    log.info("Pulling hot prospects from Apollo...")
    prospects = pull_hot_prospects_from_apollo(30)
    today_stats["prospects_pulled"] = len(prospects)
    log.info(f"  {len(prospects)} qualified prospects")
    
    # Process top prospects
    hot   = [p for p in prospects if p.get("tier")=="HOT"][:5]
    warm  = [p for p in prospects if p.get("tier")=="WARM"][:10]
    to_contact = hot + warm
    log.info(f"  HOT: {len(hot)} | WARM: {len(warm)}")
    
    for lead in to_contact:
        try:
            # Generate zero-resistance sequence
            seq = generate_zero_resistance_sequence(lead)
            today_stats["sequences_generated"] += 1
            
            # Send touch 1 immediately
            if seq.get("sequence") and lead.get("email"):
                touch1 = seq["sequence"][0]
                if touch1.get("channel") == "email":
                    sent = send_outreach_email(
                        lead["email"],
                        touch1["subject"],
                        touch1["body"],
                        lead.get("first_name","")
                    )
                    if sent: today_stats["emails_sent"] += 1
                    time.sleep(45)  # Rate limiting — professional pacing
        except Exception as e:
            today_stats["errors"].append(str(e)[:100])
    
    # Save today's stats
    _save_daily_stats(today_stats)
    log.info(f"✅ Sales run complete: {today_stats['emails_sent']} emails sent")

def _save_daily_stats(stats):
    path = "data/sales/daily_stats.json"
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    existing = []
    if r.status_code == 200:
        try: existing = json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    existing.insert(0, {**stats, "date": str(date.today())})
    existing = existing[:90]
    body = {"message":f"sales: daily stats {date.today()}","content":base64.b64encode(json.dumps(existing,indent=2).encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)

if __name__ == "__main__":
    run()
