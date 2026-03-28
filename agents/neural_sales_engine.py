# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
Neural Sales Engine — NYSR Elite Sales & Marketing
════════════════════════════════════════════════════════════════
The complete zero-to-cash pipeline. No dead time. No wasted leads.

PIPELINE FLOW:
  1. IDENTIFY    → Apollo search by ICP (Ideal Customer Profile)
  2. SCORE       → AI lead scoring 0-100, prioritize top 20%
  3. RESEARCH    → Gather company intel, pain points, recent news
  4. PERSONALIZE → Claude writes hyper-personal first line
  5. SEQUENCE    → 8-touch automated follow-up (email + LinkedIn)
  6. HANDLE      → AI reads replies, classifies, responds to objections
  7. CLOSE       → Payment link → Stripe → confirm → onboard
  8. UPSELL      → Post-purchase sequence for upgrades

LEARNING LOOP (runs weekly):
  - Tracks open rate, reply rate, close rate per template
  - Kills templates scoring below 10% open rate
  - A/B tests 2 variants per campaign
  - Adjusts ICP criteria based on who actually buys
  - Updates objection responses based on what overcomes them
  - Reports weekly: what worked, what didn't, what changed

TARGET PRODUCTS:
  ProFlow Starter  $97/mo  → small content teams, solopreneurs
  ProFlow Growth  $297/mo  → agencies, marketing managers
  ProFlow Agency  $497/mo  → agency owners, consultants
  DFY Essential   $997/mo  → companies wanting done-for-them
  DFY Growth    $1,997/mo  → high-growth companies
  Bot Setup      $1,500-5,000 one-time
  White Label   $5,000-10,000 setup + retainer
"""
import os, sys, json, logging, requests, base64, time, smtplib, hashlib
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === MEMORY ENGINE (auto-wired) ===
import sys as _sys
_sys.path.insert(0, '/opt/nysr')
try:
    from agent_memory_engine import read_memory as _read_memory, write_memory as _write_memory
    _agent_name = __file__.split('/')[-1].replace('.py','')
    _prior_memory = _read_memory(_agent_name)
except:
    _read_memory = lambda x: {}
    _write_memory = lambda x, y: None
    _prior_memory = {}
# === END MEMORY ENGINE ===


sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SalesEngine] %(message)s")
log = logging.getLogger()

# ── KEYS ──────────────────────────────────────────────────────
ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
APOLLO_KEY   = os.environ.get("APOLLO_API_KEY","")
HUBSPOT_KEY  = os.environ.get("HUBSPOT_API_KEY","")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_USER   = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS","")
STRIPE_KEY   = os.environ.get("STRIPE_SECRET_KEY","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
NTFY_CHANNEL = os.environ.get("NTFY_CHANNEL","nysr-chairman-alerts-xk9")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H         = {"Authorization": f"token {GH_TOKEN}", "Accept":"application/vnd.github+json"}
REPO         = "nyspotlightreport/sct-agency-bots"

SALES_SYSTEM = """You are Sloane Pierce, elite sales closer for NY Spotlight Report.
You sell $97-$10,000 automation services to entrepreneurs and marketing executives.
Voice: Confident, peer-level, never pushy. Lead with their pain. Show the math.
The sale is already justified — you're just helping them see that.
Never use: "I hope this finds you well", "touching base", "circling back", "synergy".
Always: specific numbers, their exact situation, one clear next step."""

# ── IDEAL CUSTOMER PROFILES ───────────────────────────────────
ICPS = [
    {
        "name": "Content Manager / Marketing Manager",
        "apollo_query": {"titles":["Content Manager","Marketing Manager","Head of Content",
                                   "Content Director","VP Marketing","CMO"],
                         "employee_count_min":10,"employee_count_max":500,
                         "keywords":["content marketing","digital marketing","social media"]},
        "pain": "spending too much on content creation and not getting consistent output",
        "product_fit": "ProFlow Growth ($297/mo)",
        "payment_link": "https://buy.stripe.com/9B600j87q9Yn5YDeDl24006",
        "value_prop": "Replace your content team overhead with 63 AI bots for $297/month",
    },
    {
        "name": "Agency Owner",
        "apollo_query": {"titles":["Agency Owner","Founder","CEO","Managing Director"],
                         "employee_count_min":1,"employee_count_max":50,
                         "keywords":["digital agency","content agency","marketing agency","SEO agency"]},
        "pain": "content delivery costs eating margin on every client",
        "product_fit": "DFY Essential ($997/mo) or White Label ($5,000)",
        "payment_link": "https://buy.stripe.com/4gMdR9evO1rRev97aT24008",
        "value_prop": "White-label our full AI stack to your clients. Keep 70% margin.",
    },
    {
        "name": "Solopreneur / Founder",
        "apollo_query": {"titles":["Founder","Solopreneur","Creator","Entrepreneur","Independent"],
                         "employee_count_min":1,"employee_count_max":5,
                         "keywords":["passive income","newsletter","content creator","indie hacker"]},
        "pain": "can't keep up with content while also running the business",
        "product_fit": "ProFlow Starter ($97/mo)",
        "payment_link": "https://buy.stripe.com/fZu3cv3Ra2vV0Ej8eX24005",
        "value_prop": "Set up your full content automation in 48 hours. $97/month.",
    },
    {
        "name": "E-commerce / DTC Brand",
        "apollo_query": {"titles":["Founder","CEO","Head of Marketing","Growth Lead"],
                         "employee_count_min":5,"employee_count_max":200,
                         "keywords":["ecommerce","DTC","Shopify","direct to consumer"]},
        "pain": "ad costs rising, organic content not scaling fast enough",
        "product_fit": "ProFlow Agency ($497/mo)",
        "payment_link": "https://buy.stripe.com/4gMdR987qeeD9aPgLt24007",
        "value_prop": "Full organic content operation for less than one paid ad day.",
    },
]

# ── EMAIL SEQUENCES ────────────────────────────────────────────
def generate_sequence(prospect: dict, icp: dict) -> list:
    """Generate an 8-touch personalized sequence using Claude."""
    
    name      = prospect.get("first_name","there")
    company   = prospect.get("organization",{}).get("name","") if isinstance(prospect.get("organization"),dict) else prospect.get("company","")
    title     = prospect.get("title","")
    pain      = icp.get("pain","")
    product   = icp.get("product_fit","ProFlow AI")
    value     = icp.get("value_prop","")
    pay_link  = icp.get("payment_link","https://nyspotlightreport.com/proflow/")
    
    if not ANTHROPIC:
        return _static_sequence(name, company, title, product, value, pay_link)
    
    result = claude_json(
        SALES_SYSTEM,
        f"""Create an 8-email sales sequence for this prospect:

Name: {name}
Title: {title}
Company: {company}
Their pain: {pain}
Our product fit: {product}
Value prop: {value}
Payment link: {pay_link}

Rules:
- Email 1 (Day 0): Ultra-short cold intro. One pain point. One question. Under 60 words.
- Email 2 (Day 3): Follow-up. Add social proof number. Under 50 words.
- Email 3 (Day 7): Different angle — the math/ROI. Under 70 words.
- Email 4 (Day 12): Case study teaser. Under 60 words.
- Email 5 (Day 18): "Did I get this wrong?" — challenge assumption. Under 50 words.
- Email 6 (Day 25): Hard value — specific cost comparison. Under 70 words.
- Email 7 (Day 32): Last outreach this month. Softest CTA. Under 40 words.
- Email 8 (Day 60): Re-engage after break. Fresh angle. Under 50 words.

For each email return: {{day, subject, body, cta_type}}
Return JSON array of 8 emails.""",
        max_tokens=2000
    )
    return result if isinstance(result, list) else _static_sequence(name, company, title, product, value, pay_link)

def _static_sequence(name, company, title, product, value, pay_link):
    return [
        {"day":0,  "subject":f"Content team costs at {company}",
         "body":f"""Hi {name},

Running content at {company} on {title} budget — curious what your monthly output costs including tools + headcount?

We automated ours entirely. Happy to share the setup.

— SC Thomas
NY Spotlight Report""",
         "cta_type":"curiosity"},
        {"day":3,  "subject":f"Re: Content team costs at {company}",
         "body":f"""Hi {name},

Following up — we replaced $4,200/month in content team costs with $70/month in automation. 63 bots running daily.

Worth 15 minutes to walk you through it?

— SC""",
         "cta_type":"proof"},
        {"day":7,  "subject":"The math on content automation",
         "body":f"""Hi {name},

Quick math: if your content operation costs $2k+/month, the ROI on automating it is under 45 days.

ProFlow AI: {value}

{pay_link}

— SC""",
         "cta_type":"roi"},
        {"day":12, "subject":"How Starter Story featured our system",
         "body":f"""Hi {name},

We've been getting press on this — Starter Story, Indie Hackers, HN front page.

The angle: sole operator running a full content agency with bots.

Case study: {pay_link}

— SC""",
         "cta_type":"social_proof"},
        {"day":18, "subject":"Did I get this wrong?",
         "body":f"""Hi {name},

I've been assuming content costs are your pain at {company} — maybe I'm wrong.

What's actually the bottleneck right now?

— SC""",
         "cta_type":"question"},
        {"day":25, "subject":"$4,000/month vs $97/month",
         "body":f"""Hi {name},

Industry average content team: $4,000-8,000/month.
ProFlow Starter: $97/month. Same output.

Hard to justify NOT trying it.

{pay_link}

— SC Thomas""",
         "cta_type":"comparison"},
        {"day":32, "subject":"Last note from me this month",
         "body":f"""Hi {name},

Last time reaching out for now. If content automation ever becomes a priority — nyspotlightreport.com

Wishing you the best,
— SC""",
         "cta_type":"breakup"},
        {"day":60, "subject":"Checking back in",
         "body":f"""Hi {name},

Hoping things are going well at {company}.

We've scaled a lot since I last reached out — worth a fresh look if you're still managing content manually.

{pay_link}

— SC""",
         "cta_type":"reengage"},
    ]

# ── LEAD SCORING ───────────────────────────────────────────────
def score_lead(prospect: dict, icp: dict) -> int:
    """Score prospect 0-100 based on fit signals."""
    score = 50  # base
    
    # Company size signals
    size = prospect.get("organization",{}).get("estimated_num_employees",0) if isinstance(prospect.get("organization"),dict) else 0
    if 10 <= size <= 200:   score += 20
    elif 200 < size <= 1000: score += 10
    elif size > 1000:        score -= 10
    elif size < 5:           score -= 5
    
    # Title seniority
    title = (prospect.get("title","") or "").lower()
    if any(x in title for x in ["cmo","vp","director","head of","chief"]): score += 15
    elif any(x in title for x in ["manager","lead","owner","founder"]): score += 10
    elif any(x in title for x in ["coordinator","specialist","assistant"]): score -= 5
    
    # Has email
    if prospect.get("email"): score += 10
    
    # LinkedIn presence
    if prospect.get("linkedin_url"): score += 5
    
    # Technology signals (uses tools like ours)
    techs = [t.get("name","").lower() for t in prospect.get("technologies",[]) if isinstance(t,dict)]
    if any(t in techs for t in ["hubspot","salesforce","mailchimp","active campaign"]): score += 5
    if any(t in techs for t in ["wordpress","webflow","squarespace"]): score += 5
    
    return min(100, max(0, score))

# ── OBJECTION HANDLER ──────────────────────────────────────────
OBJECTION_RESPONSES = {
    "too expensive": {
        "detect": ["expensive","pricey","cost","budget","afford","too much","pricing"],
        "response": lambda n: f"Totally understand, {n}. Let me put it in context: if you're spending $500/month on content and could get the same output for $97, the break-even is literally day 1. Want me to show you the exact math for your situation?",
    },
    "not interested": {
        "detect": ["not interested","no thanks","unsubscribe","remove me","take me off"],
        "response": lambda n: None,  # Unsubscribe gracefully
    },
    "not right now": {
        "detect": ["not right now","maybe later","not yet","busy","bad timing"],
        "response": lambda n: f"Completely fair, {n}. I'll check back in 60 days — things tend to be clearer then. One quick question before I go: what would need to change for this to be a priority?",
    },
    "already have solution": {
        "detect": ["already use","have a tool","using something","competitor"],
        "response": lambda n: f"Good to know, {n}. Quick question: what's it costing you monthly including all tools + any human time? I ask because most people are surprised when they add it all up. Happy to compare.",
    },
    "need to think": {
        "detect": ["think about","consider","discuss","check with","get back"],
        "response": lambda n: f"Of course, {n}. One thing that helps the decision: we offer a 30-day money-back guarantee, so the risk is entirely on us. What specific thing do you need to think through?",
    },
    "interested_positive": {
        "detect": ["interested","tell me more","sounds good","love this","want to","let's do","sign me up","how do"],
        "response": None,  # Trigger immediate close sequence
        "action": "CLOSE",
    },
    "demo_request": {
        "detect": ["demo","show me","walkthrough","see it","call","meeting"],
        "response": None,
        "action": "BOOK_CALL",
    },
}

def classify_reply(reply_text: str) -> str:
    """Classify an email reply into objection category."""
    text = reply_text.lower()
    
    for category, config in OBJECTION_RESPONSES.items():
        if any(kw in text for kw in config.get("detect",[])):
            return category
    
    return "unknown"

def handle_objection(reply: str, prospect: dict, objection_type: str) -> str:
    """Generate the perfect objection response."""
    name = prospect.get("first_name","there")
    config = OBJECTION_RESPONSES.get(objection_type,{})
    
    if config.get("action") == "CLOSE":
        # They're interested — send payment link immediately
        return generate_close_email(prospect)
    
    if config.get("action") == "BOOK_CALL":
        return f"""Hi {name},

Love it. Here's my calendar: calendly.com/sc-thomas/proflow-demo

15 minutes, no slides — just a live walkthrough of the system running.

— SC"""
    
    response_fn = config.get("response")
    if response_fn and callable(response_fn):
        base_response = response_fn(name)
        if not base_response:
            return ""  # Unsubscribe
        
        # Improve with Claude if available
        if ANTHROPIC:
            improved = claude(SALES_SYSTEM,
                f"""Prospect {name} replied to our sales email with: "{reply}"
This is a "{objection_type}" objection.
Base response: {base_response}
Make it better — more human, more specific, under 80 words. Keep the core argument.""",
                max_tokens=150)
            return improved if improved else base_response
        return base_response
    
    # Unknown — use Claude to craft a response
    if ANTHROPIC:
        return claude(SALES_SYSTEM,
            f"""Prospect {name} replied: "{reply}"
Write a perfect sales follow-up under 80 words. Don't be pushy.
Goal: keep the conversation going OR get them to click the payment link.""",
            max_tokens=120) or ""
    return ""

def generate_close_email(prospect: dict) -> str:
    """The close email — goes straight to payment link."""
    name    = prospect.get("first_name","there")
    company = prospect.get("organization",{}).get("name","") if isinstance(prospect.get("organization"),dict) else ""
    
    return f"""Hi {name},

Perfect timing. Here'''s the fastest way to get started:

🔗 ProFlow Starter ($97/month): https://buy.stripe.com/fZu3cv3Ra2vV0Ej8eX24005
🔗 ProFlow Growth ($297/month): https://buy.stripe.com/9B600j87q9Yn5YDeDl24006  
🔗 DFY Done-For-You ($997/month): https://buy.stripe.com/4gMdR9evO1rRev97aT24008

All plans include 30-day money-back guarantee.

After payment, you'''ll receive the full setup guide within 2 hours.

Which tier fits {company if company else "your situation"} best?

— SC Thomas
NY Spotlight Report"""

# ── CRM FUNCTIONS ──────────────────────────────────────────────
def get_or_create_hubspot_contact(prospect: dict) -> str:
    """Get or create HubSpot contact, return contact ID."""
    if not HUBSPOT_KEY: return ""
    
    email = prospect.get("email","")
    if not email: return ""
    
    hs_h = {"Authorization": f"Bearer {HUBSPOT_KEY}", "Content-Type":"application/json"}
    
    # Check if exists
    r = requests.get(f"https://api.hubapi.com/crm/v3/objects/contacts/search",
        json={"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":email}]}]},
        headers=hs_h, timeout=10)
    
    if r.status_code == 200 and r.json().get("total",0) > 0:
        return r.json()["results"][0]["id"]
    
    # Create
    r2 = requests.post("https://api.hubapi.com/crm/v3/objects/contacts",
        json={"properties":{
            "email": email,
            "firstname": prospect.get("first_name",""),
            "lastname": prospect.get("last_name",""),
            "jobtitle": prospect.get("title",""),
            "company": prospect.get("organization",{}).get("name","") if isinstance(prospect.get("organization"),dict) else "",
            "lead_source": "ProFlow AI Outreach",
            "hs_lead_status": "NEW"
        }}, headers=hs_h, timeout=10)
    
    if r2.status_code in [200,201]:
        return r2.json().get("id","")
    return ""

def update_deal_stage(contact_id: str, stage: str, amount: float = 0):
    """Update deal stage in HubSpot."""
    if not HUBSPOT_KEY or not contact_id: return
    hs_h = {"Authorization": f"Bearer {HUBSPOT_KEY}", "Content-Type":"application/json"}
    
    # Create or update deal
    requests.post("https://api.hubapi.com/crm/v3/objects/deals",
        json={"properties":{
            "dealstage": stage,
            "amount": str(amount),
            "dealname": f"ProFlow — {contact_id}",
            "pipeline": "default"
        }}, headers=hs_h, timeout=10)

# ── SEND EMAIL ─────────────────────────────────────────────────
def send_email(to: str, subject: str, body: str, prospect_id: str = "") -> bool:
# AG-HARD-DISABLED-GMAIL-ZERO:     if not GMAIL_PASS: return False
    try:
        msg = MIMEMultipart("alternative")
# AG-HARD-DISABLED-GMAIL-ZERO:         msg["From"]     = f"SC Thomas <{GMAIL_USER}>"
        msg["To"]       = to
        msg["Subject"]  = subject
# AG-HARD-DISABLED-GMAIL-ZERO:         msg["Reply-To"] = GMAIL_USER
        if prospect_id:
            msg["X-Prospect-ID"] = prospect_id
        msg.attach(MIMEText(body, "plain"))
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP_SSL("[GMAIL-SMTP-REDACTED]", 465) as s:
# AG-NUCLEAR-GMAIL-ZERO-20260328:             s.login(GMAIL_USER, GMAIL_PASS)
# AG-HARD-DISABLED-GMAIL-ZERO:             s.send_message(msg)
        return True
    except Exception as e:
        log.warning(f"Email failed to {to}: {e}")
        return False

def alert(msg: str):
    """Alert Chairman on high-value events."""
    if PUSHOVER_KEY:
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                  "message":msg,"title":"💰 Sales Alert","priority":1},timeout=5)
    # ntfy fallback
    requests.post(f"https://ntfy.sh/{NTFY_CHANNEL}",
        json={"topic":NTFY_CHANNEL,"title":"Sales Alert","message":msg,"priority":4},
        headers={"Content-Type":"application/json"},timeout=5)

# ── LEARNING FUNCTIONS (self-correcting) ───────────────────────
def load_performance_data() -> dict:
    """Load historical performance data for learning."""
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/performance.json",
        headers=GH_H)
    if r.status_code == 200:
        try:
            return json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    return {
        "sequences": {},  # template_id -> {sent, opened, replied, closed, revenue}
        "icps": {},       # icp_name -> {contacted, replied, closed, avg_deal}
        "objections": {}, # objection_type -> {encountered, overcame}
        "total_sent": 0, "total_replied": 0, "total_closed": 0, "total_revenue": 0,
        "subject_lines": {},  # subject -> {sent, opened}
        "lessons_learned": [],
    }

def save_performance_data(data: dict):
    payload = json.dumps(data, indent=2)
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/performance.json", headers=GH_H)
    body = {"message":"sales: update performance data","content":base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/data/sales/performance.json",
        json=body, headers=GH_H)

def analyze_and_adapt(perf: dict) -> list:
    """
    The learning brain. Analyzes performance, generates adaptations.
    Returns list of changes to implement.
    """
    changes = []
    
    # Kill underperforming sequences
    for seq_id, stats in perf.get("sequences",{}).items():
        sent = stats.get("sent",0)
        if sent >= 20:
            open_rate  = stats.get("opened",0) / sent
            reply_rate = stats.get("replied",0) / sent
            close_rate = stats.get("closed",0) / sent
            
            if open_rate < 0.10:
                changes.append({"type":"KILL_SEQUENCE","id":seq_id,"reason":f"Open rate {open_rate:.0%} < 10% threshold"})
            elif reply_rate < 0.02:
                changes.append({"type":"REVISE_SEQUENCE","id":seq_id,"reason":f"Reply rate {reply_rate:.0%} — needs new angle"})
            elif close_rate > 0.05:
                changes.append({"type":"SCALE_SEQUENCE","id":seq_id,"reason":f"Close rate {close_rate:.0%} — increase volume"})
    
    # Update ICP priorities
    best_icp = max(perf.get("icps",{}).items(), 
                   key=lambda x: x[1].get("closed",0), default=(None,{}))
    if best_icp[0]:
        changes.append({"type":"PRIORITIZE_ICP","icp":best_icp[0],
                        "reason":f"Highest close rate — allocate 60% of volume here"})
    
    # Subject line optimization
    for subject, stats in perf.get("subject_lines",{}).items():
        sent = stats.get("sent",0)
        if sent >= 20 and stats.get("opened",0)/sent < 0.15:
            changes.append({"type":"REPLACE_SUBJECT","subject":subject,"reason":"Open rate below 15%"})
    
    return changes

def generate_weekly_learning_report(perf: dict) -> str:
    """Generate weekly sales intelligence report with learnings."""
    total_sent   = perf.get("total_sent",0)
    total_replied = perf.get("total_replied",0)
    total_closed = perf.get("total_closed",0)
    total_rev    = perf.get("total_revenue",0)
    
    open_rate  = total_replied/total_sent if total_sent else 0
    close_rate = total_closed/total_sent if total_sent else 0
    
    changes = analyze_and_adapt(perf)
    
    if ANTHROPIC:
        return claude(
            "You are the NYSR sales analyst. Write a crisp weekly sales report with specific learnings.",
            f"""Sales performance this week:
Emails sent: {total_sent}
Replies: {total_replied} ({open_rate:.0%} rate)
Closed: {total_closed} ({close_rate:.0%} rate)
Revenue: ${total_rev:.2f}
Adaptations needed: {len(changes)}
Changes: {json.dumps(changes[:5],indent=2)}

Write a 120-word weekly brief: what worked, what didn't, what changed, what's next.""",
            max_tokens=180
        ) or f"Weekly sales report: {total_sent} sent, {total_replied} replies, {total_closed} closed, ${total_rev:.2f} revenue."
    return f"Sales brief: {total_sent} sent | {total_replied} replies | {total_closed} closed | ${total_rev:.2f}"

# ── MAIN PIPELINE ──────────────────────────────────────────────
def run():
    log.info("Neural Sales Engine starting...")
    
    perf = load_performance_data()
    total_sent = 0
    
    for icp in ICPS:
        log.info(f"ICP: {icp['name']}")
        
        # Get prospects from Apollo
        prospects = get_apollo_prospects(icp)
        log.info(f"  Prospects fetched: {len(prospects)}")
        
        # Score and sort
        scored = [(p, score_lead(p, icp)) for p in prospects]
        scored.sort(key=lambda x: x[1], reverse=True)
        top_prospects = [p for p,s in scored if s >= 60][:10]  # Top scored only
        log.info(f"  High-quality prospects (score 60+): {len(top_prospects)}")
        
        for prospect in top_prospects:
            email = prospect.get("email","")
            if not email:
                continue
            
            name    = prospect.get("first_name","")
            company = prospect.get("organization",{}).get("name","") if isinstance(prospect.get("organization"),dict) else ""
            score   = next(s for p,s in scored if p==prospect)
            
            # Generate personalized sequence
            sequence = generate_sequence(prospect, icp)
            if not sequence:
                continue
            
            # Send day-0 email
            first_email = sequence[0]
            subject = first_email.get("subject","")
            body    = first_email.get("body","")
            
            if send_email(email, subject, body):
                total_sent += 1
                log.info(f"  ✅ [{score}/100] {name} at {company} → {subject[:40]}")
                
                # Update HubSpot
                contact_id = get_or_create_hubspot_contact(prospect)
                if contact_id:
                    update_deal_stage(contact_id, "appointmentscheduled")
                
                # Track performance
                seq_id = hashlib.md5(subject.encode()).hexdigest()[:8]
                if seq_id not in perf["sequences"]:
                    perf["sequences"][seq_id] = {"sent":0,"opened":0,"replied":0,"closed":0,"revenue":0}
                perf["sequences"][seq_id]["sent"] += 1
                
                if subject not in perf["subject_lines"]:
                    perf["subject_lines"][subject] = {"sent":0,"opened":0}
                perf["subject_lines"][subject]["sent"] += 1
                
                if icp["name"] not in perf["icps"]:
                    perf["icps"][icp["name"]] = {"contacted":0,"replied":0,"closed":0,"avg_deal":0}
                perf["icps"][icp["name"]]["contacted"] += 1
                
                perf["total_sent"] += 1
                
                # Store sequence for follow-up
                store_sequence(email, sequence, prospect, icp)
                
                time.sleep(2)  # Rate limit
    
    # Save performance
    save_performance_data(perf)
    
    # Learning report
    if total_sent > 0:
        changes = analyze_and_adapt(perf)
        if changes:
            log.info(f"""
🧠 LEARNING ENGINE: {len(changes)} adaptations identified""")
            for c in changes[:3]:
                log.info(f"  → {c['type']}: {c['reason']}")
        
        report = generate_weekly_learning_report(perf)
        log.info(f"""
{report}""")
        
        # Alert on first close
        if perf.get("total_closed",0) > 0:
            alert(f"SALE CLOSED! Revenue: ${perf.get('total_revenue',0):.2f} | Total: {perf.get('total_closed',0)} clients")
    
    log.info(f"""
✅ Neural Sales Engine: {total_sent} emails sent today""")

def get_apollo_prospects(icp: dict) -> list:
    """Fetch prospects from Apollo based on ICP."""
    if not APOLLO_KEY: return []
    
    query = icp.get("apollo_query",{})
    payload = {
        "api_key": APOLLO_KEY,
        "q_organization_keyword_tags": query.get("keywords",[]),
        "person_titles": query.get("titles",[]),
        "organization_num_employees_ranges": [
            f"{query.get('employee_count_min',1)},{query.get('employee_count_max',500)}"
        ],
        "page": 1,
        "per_page": 25,
        "contact_email_status": ["verified","likely to engage"],
    }
    
    r = requests.post("https://api.apollo.io/v1/mixed_people/search",
        json=payload, timeout=20)
    
    if r.status_code == 200:
        return r.json().get("people",[])
    log.warning(f"Apollo error: {r.status_code}")
    return []

def store_sequence(email: str, sequence: list, prospect: dict, icp: dict):
    """Store full sequence for automated follow-up."""
    seq_data = {
        "email": email,
        "prospect": {"name": prospect.get("first_name",""), 
                     "company": prospect.get("organization",{}).get("name","") if isinstance(prospect.get("organization"),dict) else ""},
        "icp": icp["name"],
        "sequence": sequence,
        "started": str(date.today()),
        "current_step": 0,
        "status": "active",
    }
    
    path = f"data/sales/sequences/{email.replace('@','_').replace('.','_')}.json"
    payload = json.dumps(seq_data, indent=2)
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=GH_H)
    body = {"message":f"sales: sequence for {email[:20]}","content":base64.b64encode(payload.encode()).decode()}
    if r.status_code == 200: body["sha"] = r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=GH_H)

if __name__ == "__main__":
    run()
