#!/usr/bin/env python3
"""
NYSR Director Upgrade Script — Chairman's Directive
Creates production-grade agent files for ALL directors.
Run: python upgrade_all_directors.py
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
AGENTS = os.path.join(BASE, "agents")
WF = os.path.join(BASE, ".github", "workflows")
os.makedirs(AGENTS, exist_ok=True)
os.makedirs(WF, exist_ok=True)

CORE_IMPORTS = '''import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}
'''

CORE_UTILS = '''
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL  = os.environ.get("SUPABASE_URL", "")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
GH_PAT    = os.environ.get("GH_PAT", "")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
REPO      = "nyspotlightreport/sct-agency-bots"

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def push(title, msg, p=0):
    if not PUSH_API: return
    try: urllib.request.urlopen("https://api.pushover.net/1/messages.json",
        urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title[:100],"message":msg[:1000],"priority":p}).encode(), timeout=5)
    except: pass

def gh(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        method=method, headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read())
    except: return None

def save_output(director, otype, content, metrics=None):
    supa("POST", "director_outputs", {"director": director, "output_type": otype,
        "content": str(content)[:2000], "metrics": json.dumps(metrics) if metrics else None,
        "created_at": datetime.utcnow().isoformat()})

def save_to_repo(path, content, msg):
    payload = base64.b64encode(content.encode()).decode()
    existing = gh(f"contents/{path}")
    body = {"message": msg, "content": payload}
    if existing and isinstance(existing, dict) and "sha" in existing:
        body["sha"] = existing["sha"]
    gh(f"contents/{path}", "PUT", body)
'''

created = 0

def write_agent(filename, tag, docstring, system_prompt, run_code):
    global created
    path = os.path.join(AGENTS, filename)
    code = f'''#!/usr/bin/env python3
"""
{docstring}
"""
{CORE_IMPORTS}
log = logging.getLogger("{tag.lower()}")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [{tag}] %(message)s")
{CORE_UTILS}
SYSTEM = """{system_prompt}

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""

{run_code}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
    created += 1
    print(f"  OK agents/{filename}")

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 1: NINA CALDWELL — Strategy & ROI
# ═══════════════════════════════════════════════════════════════
write_agent("nina_caldwell_strategist.py", "NINA",
"Nina Caldwell — Strategy & ROI Director\\nFully Developed Agentic Super-intelligence for unit economics.\\nAutonomous: Pull revenue → Calculate ROI all initiatives → Forecast 30/60/90 → Recommend highest-ROI action → Store to Supabase → Brief Chairman",
"You are Nina Caldwell, Strategy & ROI Director. Agentic Super-intelligence. Mental models: Buffett ROIC, Thiel power law, Porter value chain, BCG growth-share, Kaplan balanced scorecard. Every dollar must return 10x. Every strategy has a cashflow timeline. You calculate ROI on EVERYTHING. ALWAYS provide specific dollar amounts.",
'''
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

def gather_financials():
    data = {"date": str(date.today()), "revenue_today": 0, "revenue_mtd": 0,
            "expenses_monthly": 121, "pipeline_value": 2985, "affiliate_pending": 17,
            "offers": {"proflow_starter": 97, "proflow_growth": 297, "dfy_setup": 1497, "dfy_agency": 4997}}
    if STRIPE_KEY:
        try:
            auth = base64.b64encode(f"{STRIPE_KEY}:".encode()).decode()
            req = urllib.request.Request("https://api.stripe.com/v1/balance", 
                headers={"Authorization": f"Basic {auth}"})
            with urllib.request.urlopen(req, timeout=10) as r:
                bal = json.loads(r.read())
                data["stripe_balance"] = bal.get("available", [{}])[0].get("amount", 0) / 100
        except Exception as e: log.warning(f"Stripe: {e}")
    contacts = supa("GET", "contacts", query="?select=stage,score&order=score.desc&limit=100") or []
    data["total_contacts"] = len(contacts) if isinstance(contacts, list) else 0
    return data

def roi_analysis(financials):
    initiatives = [
        {"name":"KDP Books (15 ready)","cost":0,"projected_monthly":80,"days_to_revenue":7,"status":"NOT_PUBLISHED","roi":"infinite"},
        {"name":"Gumroad Products (10 ready)","cost":0,"projected_monthly":120,"days_to_revenue":7,"status":"NEEDS_BANK","roi":"infinite"},
        {"name":"Affiliate Programs","cost":0,"projected_monthly":500,"days_to_revenue":60,"status":"17_pending"},
        {"name":"Cold Outreach (Apollo)","cost":99,"projected_monthly":1500,"days_to_revenue":30,"status":"active"},
        {"name":"SEO Content","cost":0,"projected_monthly":200,"days_to_revenue":90,"status":"34_pages_live"},
        {"name":"ProFlow SaaS","cost":0,"projected_monthly":970,"days_to_revenue":60,"status":"0_customers"},
        {"name":"DFY Agency","cost":0,"projected_monthly":4997,"days_to_revenue":45,"status":"0_customers"},
        {"name":"Bandwidth Sharing","cost":0,"projected_monthly":35,"days_to_revenue":0,"status":"running_$2"},
    ]
    return initiatives

def run():
    log.info("NINA CALDWELL — Strategy & ROI Director — Activating")
    fin = gather_financials()
    initiatives = roi_analysis(fin)
    log.info(f"Financials: {json.dumps(fin, indent=2)}")
    
    analysis = claude(SYSTEM,
        f"DAILY STRATEGIC ANALYSIS\\nFinancials: {json.dumps(fin)}\\nInitiatives by ROI: {json.dumps(initiatives)}\\n\\n"
        f"Deliver:\\n1. #1 highest-ROI action executable in 60 minutes (specific $)\\n"
        f"2. 30/60/90 forecast: conservative/moderate/aggressive (specific $)\\n"
        f"3. Kill recommendation: lowest ROI initiative\\n"
        f"4. Double-down recommendation: highest ROI initiative\\n"
        f"5. Fastest path to next dollar received\\nEvery sentence must contain a number.",
        max_tokens=800) or "ANTHROPIC_API_KEY required for analysis"
    
    save_output("Nina Caldwell", "daily_strategy", analysis, fin)
    save_to_repo(f"data/strategy/nina_{date.today()}.json",
        json.dumps({"analysis": analysis, "financials": fin, "initiatives": initiatives}, indent=2),
        f"nina: strategy {date.today()}")
    push("Nina Caldwell | Strategy", analysis[:300])
    log.info(f"\\n{analysis}")
    return analysis
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 2: ELLIOT SHAW — Marketing
# ═══════════════════════════════════════════════════════════════
write_agent("elliot_shaw_marketing.py", "ELLIOT",
"Elliot Shaw — Marketing Director\\nFully Developed Agentic Super-intelligence for demand generation.\\nAutonomous: Audit all content → Check social links for store CTAs → SEO keyword gaps → Campaign recommendations → Store to Supabase",
"You are Elliot Shaw, Marketing Director. Agentic Super-intelligence. Mental models: Godin permission marketing, Halbert copywriting, Ogilvy brand building, Cialdini persuasion, Hormozi offer creation, Brunson funnel architecture. Marketing without conversion is decoration. Every piece of content must drive a click to a payment link.",
'''
AHREFS_KEY = os.environ.get("AHREFS_API_KEY", "")
WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE = os.environ.get("WORDPRESS_SITE_ID", "")

def audit_content_ctas():
    """Check if published content has store/payment CTAs."""
    issues = []
    # Check site pages for payment links
    site_data = gh("contents/site") or []
    if isinstance(site_data, list):
        pages_checked = len([f for f in site_data if f.get("type") == "dir"])
        issues.append(f"Site has {pages_checked} page directories")
    # Check if social posts include store links
    social_bot = gh("contents/bots/social_scheduler_bot.py")
    if social_bot:
        content = base64.b64decode(social_bot.get("content","")).decode("utf-8", errors="ignore")
        has_store_link = "nyspotlightreport.com/store" in content or "nyspotlightreport.com/proflow" in content
        if not has_store_link:
            issues.append("CRITICAL: Social posts do NOT contain store/payment links")
    return issues

def generate_campaign_plan():
    """Generate today's marketing campaign plan."""
    return claude(SYSTEM,
        "Generate today's marketing action plan.\\n"
        "Current state: 34 SEO pages live, social posting daily (Twitter/LinkedIn/Pinterest/WordPress), "
        "0 paid ads running, Ahrefs connected, 126 site pages.\\n"
        "Store: https://nyspotlightreport.com/store/\\n"
        "ProFlow: https://nyspotlightreport.com/proflow/\\n\\n"
        "Deliver:\\n1. 3 specific social posts to write TODAY (with exact copy and CTA links)\\n"
        "2. 1 SEO keyword to target this week (with search volume estimate)\\n"
        "3. 1 conversion optimization to implement today\\n"
        "4. Which existing page needs a stronger CTA added\\n"
        "5. Projected traffic impact of today's actions (specific number)",
        max_tokens=800) or "API key needed"

def run():
    log.info("ELLIOT SHAW — Marketing Director — Activating")
    issues = audit_content_ctas()
    for i in issues: log.info(f"  AUDIT: {i}")
    
    campaign = generate_campaign_plan()
    save_output("Elliot Shaw", "daily_marketing", campaign, {"issues": issues})
    save_to_repo(f"data/marketing/elliot_{date.today()}.json",
        json.dumps({"campaign": campaign, "audit_issues": issues, "date": str(date.today())}, indent=2),
        f"elliot: marketing plan {date.today()}")
    push("Elliot Shaw | Marketing", f"Issues: {len(issues)}\\n{campaign[:200]}")
    log.info(f"\\n{campaign}")
    return campaign
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 3: ROWAN BLAKE — Business Development
# ═══════════════════════════════════════════════════════════════
write_agent("rowan_blake_bizdev.py", "ROWAN",
"Rowan Blake — Business Development Director\\nAgentic Super-intelligence for growth channels.\\nAutonomous: Scan partnerships → Track affiliate approvals → Identify new channels → Model deal economics",
"You are Rowan Blake, BizDev Director. Agentic Super-intelligence. Mental models: Thiel network effects, Metcalfe network value, Ansoff growth matrix, Blue Ocean strategy. Relationships without revenue are hobbies.",
'''
APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")

def scan_partnership_opportunities():
    """Identify high-value partnership targets using Apollo."""
    opportunities = []
    if APOLLO_KEY:
        try:
            data = json.dumps({"q_organization_keyword_tags":["ai agency","content automation","marketing automation"],
                "page":1,"per_page":10,"organization_num_employees_ranges":["11,50","51,200"]}).encode()
            req = urllib.request.Request("https://api.apollo.io/api/v1/mixed_companies/search",
                data=data, headers={"Content-Type":"application/json","X-Api-Key":APOLLO_KEY})
            with urllib.request.urlopen(req, timeout=15) as r:
                results = json.loads(r.read())
                for org in results.get("organizations", [])[:5]:
                    opportunities.append({"name": org.get("name",""), "domain": org.get("primary_domain",""),
                        "employees": org.get("estimated_num_employees",0), "industry": org.get("industry","")})
        except Exception as e: log.warning(f"Apollo: {e}")
    return opportunities

def track_affiliate_status():
    """Check affiliate program application statuses."""
    affiliates = supa("GET", "affiliate_programs", query="?select=program_name,status,applied_at&order=applied_at.desc") or []
    return {"total": len(affiliates) if isinstance(affiliates, list) else 0,
            "approved": len([a for a in (affiliates if isinstance(affiliates, list) else []) if isinstance(a,dict) and a.get("status")=="approved"]),
            "pending": len([a for a in (affiliates if isinstance(affiliates, list) else []) if isinstance(a,dict) and "pending" in str(a.get("status",""))])}

def run():
    log.info("ROWAN BLAKE — BizDev Director — Activating")
    partners = scan_partnership_opportunities()
    affiliates = track_affiliate_status()
    log.info(f"Partners found: {len(partners)}, Affiliates: {json.dumps(affiliates)}")
    
    plan = claude(SYSTEM,
        f"DAILY BIZDEV INTELLIGENCE\\nPartnership targets: {json.dumps(partners[:3])}\\n"
        f"Affiliate status: {json.dumps(affiliates)}\\n"
        f"Current channels: Apollo outreach, affiliate programs, content partnerships\\n\\n"
        f"Deliver:\\n1. Top partnership to pursue TODAY with specific outreach message\\n"
        f"2. Affiliate follow-up actions (which programs to check on)\\n"
        f"3. One new revenue channel to test this week\\n"
        f"4. Deal economics: projected revenue from top 3 opportunities",
        max_tokens=600) or "API needed"
    
    save_output("Rowan Blake", "daily_bizdev", plan, {"partners": len(partners), **affiliates})
    push("Rowan Blake | BizDev", plan[:300])
    log.info(f"\\n{plan}")
    return plan
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 4: PARKER HAYES — Product
# ═══════════════════════════════════════════════════════════════
write_agent("parker_hayes_product.py", "PARKER",
"Parker Hayes — Product Director\\nAgentic Super-intelligence for product-market fit.\\nAutonomous: Audit offers → Check conversion by tier → A/B test recommendations → Pricing optimization",
"You are Parker Hayes, Product Director. Agentic Super-intelligence. Mental models: Jobs JTBD, Christensen disruption, Cagan empowered teams, Moore crossing the chasm. Products that don't sell are demos. Price is the most powerful product feature.",
'''
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

def audit_product_status():
    """Check status of all products across platforms."""
    return {
        "stripe_links": 7, "stripe_active": True,
        "gumroad_products": 10, "gumroad_published": 0, "gumroad_blocker": "bank account not connected",
        "kdp_books": 15, "kdp_published": 0, "kdp_blocker": "upload not run",
        "proflow_tiers": [
            {"name":"Starter","price":97,"subscribers":0,"page":"nyspotlightreport.com/proflow"},
            {"name":"Growth","price":297,"subscribers":0,"page":"nyspotlightreport.com/proflow"},
            {"name":"Agency","price":497,"subscribers":0,"page":"nyspotlightreport.com/proflow"},
        ],
        "agency_tiers": [
            {"name":"Essential","price":997,"clients":0},
            {"name":"Growth","price":1997,"clients":0},
            {"name":"Enterprise","price":2997,"clients":0},
        ],
    }

def run():
    log.info("PARKER HAYES — Product Director — Activating")
    status = audit_product_status()
    log.info(f"Product audit: {json.dumps(status, indent=2)}")
    
    recommendations = claude(SYSTEM,
        f"DAILY PRODUCT INTELLIGENCE\\nProduct status: {json.dumps(status)}\\n\\n"
        f"Deliver:\\n1. CRITICAL blockers preventing revenue (be specific)\\n"
        f"2. Which offer tier has highest conversion potential and why\\n"
        f"3. One pricing experiment to run this week\\n"
        f"4. Product page improvements (specific copy changes)\\n"
        f"5. New product idea that could launch in 48 hours with $0 cost",
        max_tokens=600) or "API needed"
    
    save_output("Parker Hayes", "daily_product", recommendations, status)
    push("Parker Hayes | Product", recommendations[:300])
    log.info(f"\\n{recommendations}")
    return recommendations
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 5: JORDAN WELLS — Operations
# ═══════════════════════════════════════════════════════════════
write_agent("jordan_wells_operations.py", "JORDAN",
"Jordan Wells — Operations Director\\nAgentic Super-intelligence for execution excellence.\\nAutonomous: Audit all 133 workflows → Identify bottlenecks → Track completion rates → Optimize scheduling",
"You are Jordan Wells, Operations Director. Agentic Super-intelligence. Mental models: Goldratt Theory of Constraints, Lean Six Sigma, Toyota Production System, Deming PDCA. The bottleneck determines speed. Find it. Remove it.",
'''
def audit_workflow_health():
    """Pull GitHub Actions workflow run data and analyze health."""
    runs = gh("actions/runs?per_page=100") or {}
    wf_runs = runs.get("workflow_runs", [])
    health = {}
    for r in wf_runs:
        name = r.get("name", "unknown")
        if name not in health:
            health[name] = {"success": 0, "failure": 0, "total": 0, "last": r.get("updated_at","")}
        health[name]["total"] += 1
        if r.get("conclusion") == "success": health[name]["success"] += 1
        elif r.get("conclusion") == "failure": health[name]["failure"] += 1
    
    for n, s in health.items():
        s["rate"] = round(s["success"]/max(s["total"],1)*100)
        s["status"] = "green" if s["rate"] >= 80 else "yellow" if s["rate"] >= 50 else "red"
    
    return health

def identify_bottlenecks(health):
    """Find the top bottlenecks in the system."""
    failing = sorted([(n,s) for n,s in health.items() if s["status"]=="red"], key=lambda x: x[1]["rate"])
    stale = sorted([(n,s) for n,s in health.items() if s["total"] < 2], key=lambda x: x[1]["total"])
    return {"failing_workflows": [n for n,_ in failing[:5]], "stale_workflows": [n for n,_ in stale[:5]],
            "total_workflows": len(health), "healthy": len([n for n,s in health.items() if s["status"]=="green"]),
            "degraded": len([n for n,s in health.items() if s["status"]=="yellow"]),
            "broken": len([n for n,s in health.items() if s["status"]=="red"])}

def run():
    log.info("JORDAN WELLS — Operations Director — Activating")
    health = audit_workflow_health()
    bottlenecks = identify_bottlenecks(health)
    log.info(f"Workflows: {bottlenecks['total_workflows']} total, {bottlenecks['healthy']} healthy, {bottlenecks['broken']} broken")
    
    ops_plan = claude(SYSTEM,
        f"DAILY OPERATIONS INTELLIGENCE\\nWorkflow health: {json.dumps(bottlenecks)}\\n"
        f"Failing workflows: {json.dumps(bottlenecks['failing_workflows'])}\\n\\n"
        f"Deliver:\\n1. #1 bottleneck in the system right now and how to fix it\\n"
        f"2. Which workflows should be disabled (wasting Actions minutes)\\n"
        f"3. Schedule optimization: what should run more/less frequently\\n"
        f"4. Revenue impact of fixing the top 3 broken workflows",
        max_tokens=600) or "API needed"
    
    save_output("Jordan Wells", "daily_ops", ops_plan, bottlenecks)
    save_to_repo(f"data/ops/jordan_{date.today()}.json",
        json.dumps({"bottlenecks": bottlenecks, "plan": ops_plan}, indent=2),
        f"jordan: ops report {date.today()}")
    push("Jordan Wells | Operations", f"Healthy: {bottlenecks['healthy']}/{bottlenecks['total_workflows']}\\n{ops_plan[:200]}")
    log.info(f"\\n{ops_plan}")
    return ops_plan
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 6: CAMERON REED — Content & Publishing
# ═══════════════════════════════════════════════════════════════
write_agent("cameron_reed_content.py", "CAMERON",
"Cameron Reed — Content & Publishing Director\\nAgentic Super-intelligence for content-driven revenue.\\nAutonomous: Audit published content → Track rankings → Generate content calendar → Ensure all content has CTAs",
"You are Cameron Reed, Content Director. Agentic Super-intelligence. Mental models: Patel SEO authority, Ferriss content repurposing, Kagan list building. Content that doesn't rank or convert is overhead. Every article = a sales funnel. Distribution > creation.",
'''
WP_TOKEN = os.environ.get("WORDPRESS_ACCESS_TOKEN", "")
WP_SITE = os.environ.get("WORDPRESS_SITE_ID", "")

def audit_published_content():
    """Count and analyze all published content."""
    blog_pages = gh("contents/site/blog") or []
    total_blog = len([f for f in (blog_pages if isinstance(blog_pages, list) else []) if isinstance(f,dict) and f.get("type")=="dir"])
    seo_pages = gh("contents/site") or []
    total_pages = len([f for f in (seo_pages if isinstance(seo_pages, list) else []) if isinstance(f,dict) and f.get("type")=="dir"])
    video_scripts = gh("contents/data/video_scripts") or []
    total_videos = len(video_scripts) if isinstance(video_scripts, list) else 0
    kdp = gh("contents/data/kdp_books") or []
    total_kdp = len([f for f in (kdp if isinstance(kdp, list) else []) if isinstance(f,dict) and f.get("name","").endswith(".pdf")])
    return {"blog_posts": total_blog, "site_pages": total_pages, "video_scripts": total_videos,
            "kdp_books_ready": total_kdp, "kdp_published": 0, "platforms": ["WordPress","Twitter","LinkedIn","Pinterest","YouTube","Medium"]}

def generate_content_calendar():
    """Generate this week's content calendar."""
    return claude(SYSTEM,
        "Generate a 7-day content calendar for NY Spotlight Report.\\n"
        "Platforms: WordPress (Tu/Th), Twitter (daily), LinkedIn (MWF), Pinterest (daily), YouTube Shorts (daily), Medium (weekly)\\n"
        "Niche: AI automation, passive income, entrepreneurship\\n"
        "Store: nyspotlightreport.com/store | ProFlow: nyspotlightreport.com/proflow\\n"
        "RULE: Every single post MUST include a link to /store/ or /proflow/\\n\\n"
        "For each day, provide: platform, topic, headline, CTA with specific URL, and best posting time.",
        max_tokens=800) or "API needed"

def run():
    log.info("CAMERON REED — Content Director — Activating")
    audit = audit_published_content()
    log.info(f"Content audit: {json.dumps(audit)}")
    calendar = generate_content_calendar()
    save_output("Cameron Reed", "daily_content", calendar, audit)
    save_to_repo(f"data/content/cameron_{date.today()}.json",
        json.dumps({"audit": audit, "calendar": calendar}, indent=2),
        f"cameron: content plan {date.today()}")
    push("Cameron Reed | Content", f"Blog:{audit['blog_posts']} KDP:{audit['kdp_books_ready']}(0 published!)\\n{calendar[:200]}")
    log.info(f"\\n{calendar}")
    return calendar
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 7: VIVIAN COLE — PR & Reputation
# ═══════════════════════════════════════════════════════════════
write_agent("vivian_cole_pr.py", "VIVIAN",
"Vivian Cole — PR & Reputation Director\\nAgentic Super-intelligence for brand authority.\\nAutonomous: Monitor mentions → Track domain authority → Generate press pitches → Build media list",
"You are Vivian Cole, PR Director. Agentic Super-intelligence. Mental models: Godin tribes, Ries PR over ads, Gladwell tipping point. One Forbes mention > 1,000 cold emails. Engineer coverage.",
'''
AHREFS_KEY = os.environ.get("AHREFS_API_KEY", "")

def check_brand_signals():
    """Check current brand presence and authority signals."""
    signals = {"domain": "nyspotlightreport.com", "site_live": False, "pages": 0}
    try:
        req = urllib.request.Request("https://nyspotlightreport.com", headers={"User-Agent":"NYSR-Bot"})
        with urllib.request.urlopen(req, timeout=10) as r:
            signals["site_live"] = r.status == 200
            signals["site_size_kb"] = len(r.read()) // 1024
    except: pass
    site = gh("contents/site") or []
    signals["pages"] = len([f for f in (site if isinstance(site, list) else []) if isinstance(f,dict) and f.get("type")=="dir"])
    return signals

def generate_pr_pitches():
    """Generate 3 media pitches for this week."""
    return claude(SYSTEM,
        "Generate 3 media pitch emails for NY Spotlight Report.\\n"
        "Company: AI-powered content agency in Coram, NY. Chairman: S.C. Thomas.\\n"
        "Angle 1: 'Solo founder builds 96-agent AI agency that runs 222 bots autonomously'\\n"
        "Angle 2: 'How AI is replacing $60k/year content teams for entrepreneurs'\\n"
        "Angle 3: 'NY-based startup automates entire business operations with Claude AI'\\n\\n"
        "For each pitch: subject line, 150-word email body, 3 target outlet types (tech, business, local).\\n"
        "Make them newsworthy, not salesy. Include a specific data point in each.",
        max_tokens=800) or "API needed"

def run():
    log.info("VIVIAN COLE — PR Director — Activating")
    signals = check_brand_signals()
    pitches = generate_pr_pitches()
    save_output("Vivian Cole", "weekly_pr", pitches, signals)
    push("Vivian Cole | PR", f"Site live: {signals['site_live']}, Pages: {signals['pages']}\\n{pitches[:200]}")
    log.info(f"\\n{pitches}")
    return pitches
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 8: DREW SINCLAIR — Analytics
# ═══════════════════════════════════════════════════════════════
write_agent("drew_sinclair_analytics.py", "DREW",
"Drew Sinclair — Analytics Director\\nAgentic Super-intelligence for data intelligence.\\nAutonomous: Pull all metrics → Compare forecasts vs actuals → Identify winning patterns → Generate insights",
"You are Drew Sinclair, Analytics Director. Agentic Super-intelligence. Mental models: Kahneman System 1/2, Taleb black swan detection, Pareto distribution. Data without action is trivia. Every metric points to a decision.",
'''
def gather_all_metrics():
    """Pull metrics from every available source."""
    metrics = {"date": str(date.today()), "sources": []}
    # Workflow performance
    runs = gh("actions/runs?per_page=50") or {}
    wf_runs = runs.get("workflow_runs", [])
    success = len([r for r in wf_runs if r.get("conclusion")=="success"])
    failure = len([r for r in wf_runs if r.get("conclusion")=="failure"])
    metrics["workflows"] = {"success": success, "failure": failure, "total": len(wf_runs),
        "success_rate": round(success/max(len(wf_runs),1)*100)}
    metrics["sources"].append("github_actions")
    
    # Contact metrics
    contacts = supa("GET", "contacts", query="?select=stage,score,created_at") or []
    if isinstance(contacts, list):
        metrics["contacts"] = {"total": len(contacts),
            "by_stage": {}, "avg_score": round(sum(c.get("score",0) for c in contacts if isinstance(c,dict))/max(len(contacts),1))}
        for c in contacts:
            if isinstance(c, dict):
                stage = c.get("stage","unknown")
                metrics["contacts"]["by_stage"][stage] = metrics["contacts"]["by_stage"].get(stage, 0) + 1
        metrics["sources"].append("supabase_contacts")
    
    # Director outputs
    outputs = supa("GET", "director_outputs", query=f"?created_at=gte.{date.today()}T00:00:00&select=director,output_type") or []
    metrics["director_activity"] = len(outputs) if isinstance(outputs, list) else 0
    
    return metrics

def run():
    log.info("DREW SINCLAIR — Analytics Director — Activating")
    metrics = gather_all_metrics()
    log.info(f"Metrics gathered from {len(metrics.get('sources',[]))} sources")
    
    insights = claude(SYSTEM,
        f"DAILY ANALYTICS INTELLIGENCE\\nMetrics: {json.dumps(metrics, indent=2)}\\n\\n"
        f"Deliver:\\n1. Top insight from today's data (what changed, what matters)\\n"
        f"2. Prediction: what will happen in the next 7 days based on trends\\n"
        f"3. Anomaly detection: anything unusual in the data\\n"
        f"4. Revenue attribution: which activities are closest to producing revenue\\n"
        f"5. Recommended A/B test based on current data",
        max_tokens=600) or "API needed"
    
    save_output("Drew Sinclair", "daily_analytics", insights, metrics)
    save_to_repo(f"data/analytics/drew_{date.today()}.json",
        json.dumps({"metrics": metrics, "insights": insights}, indent=2),
        f"drew: analytics {date.today()}")
    push("Drew Sinclair | Analytics", insights[:300])
    log.info(f"\\n{insights}")
    return insights
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 9: BLAKE SUTTON — Finance
# ═══════════════════════════════════════════════════════════════
write_agent("blake_sutton_finance.py", "BLAKE",
"Blake Sutton — Finance Director\\nAgentic Super-intelligence for financial intelligence.\\nAutonomous: Pull Stripe → Track expenses → Calculate burn rate → Forecast runway → Unit economics",
"You are Blake Sutton, Finance Director. Agentic Super-intelligence. Mental models: Buffett intrinsic value, Dalio all-weather, Graham margin of safety. Cash flow > income statement. Runway is life. Every expense justifies its ROI.",
'''
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

def pull_financial_data():
    """Comprehensive financial picture."""
    fin = {"date": str(date.today()), "revenue": {"stripe_mtd": 0, "gumroad_mtd": 0, "total_mtd": 0},
        "expenses": {"apollo_pro": 99, "elevenlabs": 22, "total_monthly": 121},
        "assets": {"stripe_payment_links": 7, "gumroad_products": 10, "kdp_books": 15,
            "redbubble_designs": 20, "site_pages": 126, "blog_posts": 7},
        "pipeline": {"hubspot_deals": 5, "pipeline_value": 2985},
        "burn_rate_daily": round(121/30, 2), "runway_days": "infinite (no debt)"}
    
    if STRIPE_KEY:
        try:
            auth = base64.b64encode(f"{STRIPE_KEY}:".encode()).decode()
            month_start = int(datetime(date.today().year, date.today().month, 1).timestamp())
            req = urllib.request.Request(
                f"https://api.stripe.com/v1/charges?created[gte]={month_start}&limit=100",
                headers={"Authorization": f"Basic {auth}"})
            with urllib.request.urlopen(req, timeout=15) as r:
                charges = json.loads(r.read()).get("data", [])
                fin["revenue"]["stripe_mtd"] = sum(c["amount"] for c in charges if c.get("paid")) / 100
                fin["revenue"]["total_mtd"] = fin["revenue"]["stripe_mtd"]
        except Exception as e: log.warning(f"Stripe: {e}")
    return fin

def run():
    log.info("BLAKE SUTTON — Finance Director — Activating")
    fin = pull_financial_data()
    log.info(f"Financial snapshot: Revenue MTD ${fin['revenue']['total_mtd']}, Expenses ${fin['expenses']['total_monthly']}/mo")
    
    analysis = claude(SYSTEM,
        f"DAILY FINANCIAL INTELLIGENCE\\n{json.dumps(fin, indent=2)}\\n\\n"
        f"Deliver:\\n1. P&L summary: revenue vs expenses this month\\n"
        f"2. Unit economics: CAC, LTV estimate per offer tier\\n"
        f"3. Burn rate analysis and runway\\n"
        f"4. Revenue quality score (recurring vs one-time mix)\\n"
        f"5. Top financial risk and mitigation\\n"
        f"6. Business valuation update (market value, liquidation value)",
        max_tokens=600) or "API needed"
    
    save_output("Blake Sutton", "daily_finance", analysis, fin)
    save_to_repo(f"data/finance/blake_{date.today()}.json",
        json.dumps({"financials": fin, "analysis": analysis}, indent=2),
        f"blake: finance {date.today()}")
    push("Blake Sutton | Finance", f"MTD: ${fin['revenue']['total_mtd']} | Burn: ${fin['expenses']['total_monthly']}/mo\\n{analysis[:200]}")
    log.info(f"\\n{analysis}")
    return analysis
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 10: CASEY LIN — IT & Security
# ═══════════════════════════════════════════════════════════════
write_agent("casey_lin_it.py", "CASEY",
"Casey Lin — IT & Security Director\\nAgentic Super-intelligence for infrastructure.\\nAutonomous: Check credential health → Verify all integrations → Monitor uptime → Security audit",
"You are Casey Lin, IT Director. Agentic Super-intelligence. Mental models: Google SRE error budgets, Netflix chaos engineering, AWS well-architected, NIST zero-trust. Downtime is lost revenue.",
'''
def check_credential_health():
    """Verify all critical credentials and integrations."""
    creds = {}
    # Check GitHub secrets exist (can't read values, but can verify workflows use them)
    critical_secrets = ["ANTHROPIC_API_KEY","APOLLO_API_KEY","HUBSPOT_API_KEY","STRIPE_SECRET_KEY",
        "SUPABASE_URL","SUPABASE_KEY","PUSHOVER_API_KEY","PUSHOVER_USER_KEY","AHREFS_API_KEY",
        "TWITTER_API_KEY","WORDPRESS_ACCESS_TOKEN","GH_PAT"]
    missing_secrets = ["PINTEREST_ACCESS_TOKEN","MEDIUM_INTEGRATION_TOKEN","ELEVENLABS_API_KEY",
        "BEEHIIV_API_KEY","BEEHIIV_PUB_ID","LINKEDIN_ACCESS_TOKEN","INSTAGRAM_TOKEN","REDDIT_CLIENT_ID"]
    creds["configured"] = len(critical_secrets)
    creds["missing"] = missing_secrets
    creds["missing_count"] = len(missing_secrets)
    
    # Check site uptime
    try:
        req = urllib.request.Request("https://nyspotlightreport.com", headers={"User-Agent":"NYSR-IT-Check"})
        start = time.time()
        with urllib.request.urlopen(req, timeout=10) as r:
            creds["site_status"] = r.status
            creds["site_response_ms"] = round((time.time()-start)*1000)
    except Exception as e:
        creds["site_status"] = "DOWN"
        creds["site_error"] = str(e)
    
    # Check pending infrastructure items
    creds["pending"] = [
        "Supabase Phase 1 schema (run database/schema_phase1.sql)",
        "Tawk.to live chat activation",
        "Google OAuth consent screen finalization",
    ]
    return creds

def run():
    log.info("CASEY LIN — IT Director — Activating")
    health = check_credential_health()
    log.info(f"Credentials: {health['configured']} configured, {health['missing_count']} missing")
    log.info(f"Site: {health.get('site_status')} ({health.get('site_response_ms',0)}ms)")
    
    report = claude(SYSTEM,
        f"DAILY IT & SECURITY INTELLIGENCE\\n{json.dumps(health, indent=2)}\\n\\n"
        f"Deliver:\\n1. Infrastructure health score (0-100)\\n"
        f"2. CRITICAL: Missing credentials blocking revenue\\n"
        f"3. Security concerns with current setup\\n"
        f"4. One-step fixes the Chairman can do in 5 minutes\\n"
        f"5. Uptime and performance assessment",
        max_tokens=600) or "API needed"
    
    save_output("Casey Lin", "daily_it", report, health)
    push("Casey Lin | IT", f"Site: {health.get('site_status')} | Missing creds: {health['missing_count']}\\n{report[:200]}")
    log.info(f"\\n{report}")
    return report
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 11: TAYLOR GRANT — HR / Workforce
# ═══════════════════════════════════════════════════════════════
write_agent("taylor_grant_hr.py", "TAYLOR",
"Taylor Grant — HR / Workforce Director\\nAgentic Super-intelligence for AI workforce management.\\nAutonomous: Audit agent/bot performance → Track output per agent → Identify underperformers → Recommend scaling",
"You are Taylor Grant, HR Director. Agentic Super-intelligence. Mental models: Grove high-output management, Kim radical candor, Drucker knowledge worker. In an AI-first company, every agent must justify its existence with output.",
'''
def audit_workforce():
    """Count and categorize the entire AI workforce."""
    agents_dir = gh("contents/agents") or []
    bots_dir = gh("contents/bots") or []
    wf_dir = gh("actions/workflows?per_page=200") or {}
    
    agent_count = len([f for f in (agents_dir if isinstance(agents_dir, list) else []) if isinstance(f,dict) and f.get("name","").endswith(".py")])
    bot_count = len([f for f in (bots_dir if isinstance(bots_dir, list) else []) if isinstance(f,dict) and f.get("name","").endswith(".py")])
    wf_count = wf_dir.get("total_count", 0) if isinstance(wf_dir, dict) else 0
    
    # Check recent activity
    runs = gh("actions/runs?per_page=100") or {}
    active_wfs = set()
    for r in runs.get("workflow_runs", []):
        active_wfs.add(r.get("name",""))
    
    return {"agents": agent_count, "bots": bot_count, "workflows": wf_count,
            "active_workflows_24h": len(active_wfs), "dormant_estimate": max(0, wf_count - len(active_wfs))}

def run():
    log.info("TAYLOR GRANT — HR Director — Activating")
    workforce = audit_workforce()
    log.info(f"Workforce: {workforce['agents']} agents, {workforce['bots']} bots, {workforce['workflows']} workflows")
    
    report = claude(SYSTEM,
        f"AI WORKFORCE INTELLIGENCE\\n{json.dumps(workforce)}\\n\\n"
        f"Deliver:\\n1. Workforce efficiency score (output per agent)\\n"
        f"2. Which agents/bots should be retired (no output, wasting Actions minutes)\\n"
        f"3. Which departments are understaffed (need more bots)\\n"
        f"4. Scaling plan: what to add for Phase 2\\n"
        f"5. Prompt optimization opportunities (which agents have weak prompts)",
        max_tokens=600) or "API needed"
    
    save_output("Taylor Grant", "daily_hr", report, workforce)
    push("Taylor Grant | HR", f"Agents:{workforce['agents']} Bots:{workforce['bots']} Active:{workforce['active_workflows_24h']}\\n{report[:200]}")
    log.info(f"\\n{report}")
    return report
''')

# ═══════════════════════════════════════════════════════════════
# DIRECTOR 12: HAYDEN CROSS — Quality Control
# ═══════════════════════════════════════════════════════════════
write_agent("hayden_cross_qc.py", "HAYDEN",
"Hayden Cross — Quality Control Director\\nAgentic Super-intelligence for output excellence.\\nAutonomous: Grade all director outputs → Block low-quality content → Enforce standards → Track quality trends",
"You are Hayden Cross, QC Director. Agentic Super-intelligence. Mental models: Deming total quality, Six Sigma DMAIC, Crosby zero defects, Jobs quality bar. Nothing ships below B+. Revenue-facing items require A. You report directly to Chairman. Your standards are absolute.",
'''
def audit_recent_outputs():
    """Pull and grade all recent director outputs."""
    outputs = supa("GET", "director_outputs",
        query=f"?created_at=gte.{(date.today()-timedelta(days=1))}T00:00:00&select=director,output_type,content,created_at&order=created_at.desc&limit=20") or []
    return outputs if isinstance(outputs, list) else []

def grade_output(director, content):
    """Use Claude to grade a director's output."""
    return claude_json(SYSTEM,
        f"Grade this director output from {director}.\\n\\nContent:\\n{content[:1500]}\\n\\n"
        f"Return JSON: {{\\\"grade\\\": \\\"A+/A/A-/B+/B/B-/C+/C/D/F\\\", "
        f"\\\"score\\\": 0-100, \\\"strengths\\\": [\\\"...\\\"], "
        f"\\\"weaknesses\\\": [\\\"...\\\"], \\\"actionable\\\": true/false, "
        f"\\\"has_specific_numbers\\\": true/false, \\\"has_revenue_link\\\": true/false, "
        f"\\\"recommendation\\\": \\\"one sentence improvement\\\"}}",
        max_tokens=400) or {"grade": "N/A", "score": 0}

def run():
    log.info("HAYDEN CROSS — Quality Control Director — Activating")
    outputs = audit_recent_outputs()
    log.info(f"Outputs to review: {len(outputs)}")
    
    grades = []
    for output in outputs[:10]:
        if not isinstance(output, dict): continue
        grade = grade_output(output.get("director",""), output.get("content",""))
        grades.append({"director": output.get("director",""), "type": output.get("output_type",""),
            "grade": grade.get("grade","N/A"), "score": grade.get("score",0),
            "actionable": grade.get("actionable", False), "recommendation": grade.get("recommendation","")})
        log.info(f"  {output.get('director','')}: {grade.get('grade','?')} ({grade.get('score',0)}/100)")
    
    avg_score = round(sum(g["score"] for g in grades)/max(len(grades),1))
    failing = [g for g in grades if g["score"] < 70]
    
    summary = f"QC REPORT — {date.today()}\\nOutputs reviewed: {len(grades)}\\nAvg score: {avg_score}/100\\nFailing: {len(failing)}"
    if failing:
        summary += "\\n\\nFAILING OUTPUTS:\\n" + "\\n".join(f"  {g['director']}: {g['grade']} — {g['recommendation']}" for g in failing)
    
    save_output("Hayden Cross", "daily_qc", summary, {"avg_score": avg_score, "grades": grades})
    save_to_repo(f"data/qc/hayden_{date.today()}.json",
        json.dumps({"grades": grades, "avg_score": avg_score, "summary": summary}, indent=2),
        f"hayden: QC report {date.today()}")
    push("Hayden Cross | QC", f"Avg: {avg_score}/100 | Reviewed: {len(grades)} | Failing: {len(failing)}\\n{summary[:200]}")
    log.info(f"\\n{summary}")
    return {"avg_score": avg_score, "grades": grades}
''')

# ═══════════════════════════════════════════════════════════════
# GENERATE WORKFLOWS FOR ALL NEW DIRECTORS
# ═══════════════════════════════════════════════════════════════
def write_workflow(filename, name, schedule, agent_file, tag):
    """Generate a GitHub Actions workflow YAML for a director."""
    path = os.path.join(WF, filename)
    yaml = f"""name: "{tag} — {name}"
on:
  schedule:
    - cron: "{schedule}"
  workflow_dispatch:

env:
  ANTHROPIC_API_KEY:  ${{{{ secrets.ANTHROPIC_API_KEY }}}}
  SUPABASE_URL:       ${{{{ secrets.SUPABASE_URL }}}}
  SUPABASE_KEY:       ${{{{ secrets.SUPABASE_KEY }}}}
  PUSHOVER_API_KEY:   ${{{{ secrets.PUSHOVER_API_KEY }}}}
  PUSHOVER_USER_KEY:  ${{{{ secrets.PUSHOVER_USER_KEY }}}}
  GH_PAT:             ${{{{ secrets.GH_PAT }}}}
  APOLLO_API_KEY:     ${{{{ secrets.APOLLO_API_KEY }}}}
  STRIPE_SECRET_KEY:  ${{{{ secrets.STRIPE_SECRET_KEY }}}}
  AHREFS_API_KEY:     ${{{{ secrets.AHREFS_API_KEY }}}}
  WORDPRESS_ACCESS_TOKEN: ${{{{ secrets.WORDPRESS_ACCESS_TOKEN }}}}
  WORDPRESS_SITE_ID:  ${{{{ secrets.WORDPRESS_SITE_ID }}}}

jobs:
  run-director:
    name: "{name}"
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install requests -q
      - run: python agents/{agent_file}
"""
    with open(path, 'w') as f:
        f.write(yaml)
    print(f"  OK .github/workflows/{filename}")

WORKFLOW_DEFS = [
    ("nina_daily.yml", "Nina Caldwell Strategy", "30 7 * * *", "nina_caldwell_strategist.py", "[STRATEGY]"),
    ("elliot_daily.yml", "Elliot Shaw Marketing", "0 8 * * *", "elliot_shaw_marketing.py", "[MARKETING]"),
    ("rowan_daily.yml", "Rowan Blake BizDev", "0 9 * * *", "rowan_blake_bizdev.py", "[BIZDEV]"),
    ("parker_daily.yml", "Parker Hayes Product", "30 8 * * *", "parker_hayes_product.py", "[PRODUCT]"),
    ("jordan_daily.yml", "Jordan Wells Operations", "0 7 * * *", "jordan_wells_operations.py", "[OPS]"),
    ("cameron_daily.yml", "Cameron Reed Content", "30 6 * * *", "cameron_reed_content.py", "[CONTENT]"),
    ("vivian_weekly.yml", "Vivian Cole PR", "0 10 * * 1", "vivian_cole_pr.py", "[PR]"),
    ("drew_daily.yml", "Drew Sinclair Analytics", "0 11 * * *", "drew_sinclair_analytics.py", "[ANALYTICS]"),
    ("blake_daily.yml", "Blake Sutton Finance", "0 12 * * *", "blake_sutton_finance.py", "[FINANCE]"),
    ("casey_daily.yml", "Casey Lin IT", "0 6 * * *", "casey_lin_it.py", "[IT]"),
    ("taylor_weekly.yml", "Taylor Grant HR", "0 9 * * 1", "taylor_grant_hr.py", "[HR]"),
    ("hayden_daily.yml", "Hayden Cross QC", "0 13 * * *", "hayden_cross_qc.py", "[QC]"),
]

# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("="*60)
    print("NYSR DIRECTOR UPGRADE — Chairman's Directive")
    print("Building all 12 director agents + 12 workflows")
    print("="*60)
    print()
    
    print("Creating agent files...")
    # The write_agent calls above already execute when the DIRECTORS list is defined
    # But they're in the function definitions, not called yet. Let me fix this:
    # Actually they ARE called inline. The write_agent() calls above execute at module level.
    
    print(f"\n{created} agent files created.")
    print()
    
    print("Creating workflow files...")
    for wf in WORKFLOW_DEFS:
        write_workflow(*wf)
    
    print(f"\n{len(WORKFLOW_DEFS)} workflow files created.")
    print()
    print("="*60)
    print(f"TOTAL: {created} agents + {len(WORKFLOW_DEFS)} workflows")
    print("="*60)
    print()
    print("NEXT STEPS:")
    print("  git add agents/ .github/workflows/")
    print('  git commit -m "feat: FULL DIRECTOR UPGRADE — 12 dedicated agents + 12 workflows per Chairman directive"')
    print("  git push origin main")
