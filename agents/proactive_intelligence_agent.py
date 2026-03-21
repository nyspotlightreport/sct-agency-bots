"""
proactive_intelligence_agent.py
════════════════════════════════════════════════════════════════
The system the Chairman said was missing from day one.

This agent does NOT wait to be asked.
It does NOT react to low fitness scores.
It HUNTS for gaps, opportunities, and improvements CONSTANTLY.

It scans:
  - Every table for patterns that imply missing capabilities
  - Every agent/bot for signs of underperformance or redundancy
  - Every workflow for dead weight or missed triggers  
  - The entire roadmap for what's built vs what's not
  - Revenue data for untapped opportunities
  - The system's own standing mandates for compliance

Then it:
  - Creates intelligence_opportunity records
  - Contributes to the Chairman's daily briefing
  - Sends targeted messages to the right departments
  - Takes action autonomously where it safely can
  - Escalates to Chairman ONLY what genuinely needs a decision

Rob Vance — CITWO. This should have been the first thing built.
"""
import os, sys, json, logging, datetime, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INTEL] %(message)s")
log = logging.getLogger("proactive_intel")

sys.path.insert(0, ".")
try:
    from agents.rsi_base_agent import RSIBaseAgent, _supa, _claude, _push
except ImportError:
    # Standalone fallback
    import urllib.request, urllib.error
    def _supa(method, table, data=None, query=""):
        SUPABASE_URL = os.environ.get("SUPABASE_URL","")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
        if not SUPABASE_URL: return None
        url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
        payload = json.dumps(data).encode() if data else None
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                   "Content-Type": "application/json", "Prefer": "return=representation"}
        req = urllib.request.Request(url, data=payload, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read(); return json.loads(body) if body else {}
        except: return None
    def _claude(prompt, system="", model="claude-haiku-4-5-20251001", max_tokens=600):
        ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
        if not ANTHROPIC_KEY: return ""
        data = json.dumps({"model": model, "max_tokens": max_tokens,
                           "system": system or "You are an AI intelligence analyst.",
                           "messages": [{"role":"user","content":prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["content"][0]["text"]
        except: return ""
    def _push(title, msg, priority=0):
        api = os.environ.get("PUSHOVER_API_KEY",""); user = os.environ.get("PUSHOVER_USER_KEY","")
        if not api: return
        data = json.dumps({"token":api,"user":user,"title":title,"message":msg,"priority":priority}).encode()
        req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data,
                                      headers={"Content-Type":"application/json"})
        try: urllib.request.urlopen(req, timeout=10)
        except: pass
    class RSIBaseAgent:
        ORG_ID = "base"; NAME = "Base"
        def supa(self, *a, **k): return _supa(*a, **k)
        def claude(self, *a, **k): return _claude(*a, **k)
        def push(self, *a, **k): return _push(*a, **k)

GH_TOKEN = os.environ.get("GH_PAT", "")
REPO     = "nyspotlightreport/sct-agency-bots"


# ══════════════════════════════════════════════════════════════
# INTELLIGENCE OPPORTUNITY FACTORY
# ══════════════════════════════════════════════════════════════

def create_opportunity(discovered_by: str, opp_type: str, priority: str,
                        title: str, description: str, evidence: str = "",
                        impact: str = "", effort: str = "medium",
                        action: str = "", systems: list = None,
                        auto_actionable: bool = False) -> bool:
    """Create an intelligence opportunity if it doesn't already exist."""
    # Dedup check — don't create the same opportunity twice
    existing = _supa("GET", "intelligence_opportunities",
                     f"?title=eq.{title[:50]}&status=in.(open,in_progress)&select=id&limit=1") or []
    if existing: return False
    _supa("POST", "intelligence_opportunities", {
        "discovered_by": discovered_by,
        "opportunity_type": opp_type,
        "priority": priority,
        "title": title,
        "description": description,
        "evidence": evidence,
        "estimated_impact": impact,
        "estimated_effort": effort,
        "recommended_action": action,
        "affected_systems": systems or [],
        "auto_actionable": auto_actionable,
    })
    log.info(f"[{priority.upper()}] {opp_type}: {title}")
    return True


# ══════════════════════════════════════════════════════════════
# SCAN MODULES
# ══════════════════════════════════════════════════════════════

def scan_agent_coverage():
    """
    Are all 85 agents RSI-enabled?
    Are there agents with no corresponding synthetic_org?
    Are there tables with no agent watching them?
    """
    log.info("Scanning agent RSI coverage...")
    findings = []

    # Get all registered synthetic orgs
    orgs = _supa("GET", "synthetic_orgs", "?select=org_id,name,total_runs,last_run_at") or []
    never_run = [o for o in orgs if not o.get("last_run_at")]

    if never_run:
        for o in never_run:
            create_opportunity(
                "citwo_corp", "gap", "high",
                f"Synthetic Org Never Executed: {o['name']}",
                f"The {o['name']} org is registered but has never run. "
                f"It is not contributing to the system.",
                evidence=f"org_id={o['org_id']}, last_run_at=NULL",
                impact="Department fully inactive — zero contribution",
                effort="low",
                action=f"Trigger {o['org_id']} in rsi_synthetic_orgs_daily.yml",
                systems=[o['org_id']],
                auto_actionable=True
            )
            findings.append(f"Never-run org: {o['org_id']}")

    # Check GitHub repo for agents NOT yet importing RSIBaseAgent
    if GH_TOKEN:
        import urllib.request as ur
        try:
            req = ur.Request(
                f"https://api.github.com/repos/{REPO}/contents/agents",
                headers={"Authorization": f"token {GH_TOKEN}"})
            with ur.urlopen(req, timeout=10) as r:
                agent_files = json.loads(r.read())
            non_rsi = [f["name"] for f in agent_files
                       if f["name"].endswith(".py")
                       and "rsi_base_agent" not in f["name"]
                       and "rsi_synthetic" not in f["name"]
                       and not f["name"].startswith("__")]
            if len(non_rsi) > 10:
                create_opportunity(
                    "citwo_corp", "improvement", "high",
                    f"{len(non_rsi)} Agents Not Yet RSI-Upgraded",
                    f"{len(non_rsi)} agent files in /agents/ do not inherit from RSIBaseAgent. "
                    f"They have no self-improvement loop, no genome, no inter-org messaging, "
                    f"no fitness scoring, and no standing mandate compliance.",
                    evidence=f"Non-RSI agents: {', '.join(non_rsi[:8])}...",
                    impact="Agents operating as dumb scripts instead of Digital Entities",
                    effort="high",
                    action="Systematically upgrade each agent to inherit RSIBaseAgent",
                    systems=non_rsi[:10]
                )
                findings.append(f"{len(non_rsi)} non-RSI agents")
        except Exception as e:
            log.warning(f"GitHub agent scan failed: {e}")

    return findings


def scan_revenue_opportunities():
    """
    Is there money being left on the table right now?
    Stale pipeline, abandoned carts, unused offers, idle capabilities.
    """
    log.info("Scanning revenue opportunities...")
    findings = []
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    # 1. Check for stale hot leads
    hot_leads = _supa("GET", "contacts",
        f"?stage=in.(HOT,DEMO,PROPOSAL)&last_contacted=lt.{week_ago}T00:00:00&select=id,name,company") or []
    if hot_leads:
        create_opportunity(
            "analytics_corp", "revenue", "critical",
            f"{len(hot_leads)} Hot Leads With No Contact in 7+ Days",
            f"Hot leads going cold is direct revenue loss. These contacts were "
            f"previously qualified as HOT/DEMO/PROPOSAL but haven't been touched.",
            evidence=f"Contacts: {', '.join(c.get('name','?') for c in hot_leads[:3])}",
            impact=f"Estimated ${len(hot_leads) * 297:.0f}–${len(hot_leads) * 1497:.0f} at risk",
            effort="low",
            action="Trigger follow_up_bot.py immediately for these contacts",
            systems=["follow_up_bot", "sales_corp"],
            auto_actionable=True
        )
        findings.append(f"Stale hot leads: {len(hot_leads)}")

    # 2. Check for cart abandonment not being recovered
    cart_abandoned = _supa("GET", "store_cart_events",
        f"?event_type=eq.checkout_start&created_at=gte.{week_ago}T00:00:00&select=contact_id,session_id") or []
    purchases = _supa("GET", "store_cart_events",
        f"?event_type=eq.purchase&created_at=gte.{week_ago}T00:00:00&select=session_id") or []
    purchased_sessions = {e.get("session_id") for e in purchases}
    truly_abandoned = [e for e in cart_abandoned if e.get("session_id") not in purchased_sessions]
    if len(truly_abandoned) > 2:
        create_opportunity(
            "analytics_corp", "revenue", "high",
            f"{len(truly_abandoned)} Unrecovered Cart Abandonments",
            f"Visitors started checkout but did not complete purchase. "
            f"No recovery emails have been triggered for all of them.",
            evidence=f"Abandoned in last 7 days: {len(truly_abandoned)}",
            impact=f"Estimated ${len(truly_abandoned) * 97:.0f}–${len(truly_abandoned) * 297:.0f} recoverable",
            effort="low",
            action="Trigger cart recovery journey for all abandoned sessions",
            systems=["shopify_store_agent", "email_journey_builder_bot"],
            auto_actionable=True
        )
        findings.append(f"Cart abandonments: {len(truly_abandoned)}")

    # 3. Check for zero revenue days this week
    rev_days = _supa("GET", "revenue_daily", f"?date=gte.{week_ago}&select=date,amount") or []
    zero_days = [r for r in rev_days if float(r.get("amount",0)) == 0]
    if zero_days:
        create_opportunity(
            "finance_corp", "revenue", "critical",
            f"{len(zero_days)} Zero-Revenue Days This Week",
            f"On {len(zero_days)} day(s) this week, no revenue was recorded across "
            f"all streams (Stripe, Gumroad, HubSpot). Either systems are not capturing "
            f"revenue or there was genuinely no revenue.",
            evidence=f"Zero days: {[d['date'] for d in zero_days]}",
            impact="Direct cashflow gap — minimum Day 30 target at risk",
            effort="medium",
            action="Verify Stripe/Gumroad webhooks are firing and trigger cashflow emergency workflow",
            systems=["revenue_unifier_bot", "cashflow_emergency"],
            auto_actionable=False
        )
        findings.append(f"Zero revenue days: {len(zero_days)}")

    # 4. Gumroad products not yet published
    gumroad_products = _supa("GET", "store_products",
        "?gumroad_id=not.is.null&status=eq.inactive&select=title,gumroad_id") or []
    if gumroad_products:
        create_opportunity(
            "sales_corp", "revenue", "high",
            f"{len(gumroad_products)} Gumroad Products Inactive/Unpublished",
            f"These products exist in our database but are marked inactive. "
            f"Each inactive product is passive income not being earned.",
            evidence=f"Products: {', '.join(p.get('title','?') for p in gumroad_products[:3])}",
            impact=f"Estimated ${len(gumroad_products)*47:.0f}–${len(gumroad_products)*97:.0f}/mo passive income blocked",
            effort="low",
            action="Activate all products on Gumroad dashboard. Connect bank account if not done.",
            systems=["gumroad_product_creator", "store_products"],
            auto_actionable=False
        )
        findings.append(f"Inactive products: {len(gumroad_products)}")

    return findings


def scan_system_gaps():
    """
    What capabilities should exist but don't?
    What workflows are running with broken dependencies?
    What tables have data but no agent processing it?
    """
    log.info("Scanning system gaps...")
    findings = []

    # 1. Tables with data but no synthetic org watching them
    tables_with_data = _supa("GET", "system_knowledge",
        "?entity_type=eq.table&status=eq.active&select=entity_name") or []
    orgs = _supa("GET", "synthetic_orgs", "?select=org_id,kpi_targets") or []

    # Check SEO opportunities table — should be being acted on
    seo_opps = _supa("GET", "seo_opportunities", "?status=eq.pending&select=id,keyword&limit=5") or []
    if len(seo_opps) > 3:
        create_opportunity(
            "citwo_corp", "gap", "medium",
            f"{len(seo_opps)} SEO Opportunities Sitting Unacted Upon",
            f"The seo_opportunities table has {len(seo_opps)} pending keywords "
            f"identified by Ahrefs but no content has been created for them.",
            evidence=f"Keywords: {', '.join(o.get('keyword','?') for o in seo_opps[:3])}",
            impact="Organic traffic and leads being left on table",
            effort="medium",
            action="Trigger seo_audit_agent.py to process pending opportunities into content briefs",
            systems=["seo_audit_agent", "content_corp", "marketing_corp"],
            auto_actionable=True
        )
        findings.append(f"Unprocessed SEO opps: {len(seo_opps)}")

    # 2. Wiki pages with zero views — content not being discovered
    dead_wiki = _supa("GET", "wiki_pages",
        "?status=eq.published&views=eq.0&select=id,title,created_at&limit=10") or []
    if len(dead_wiki) > 2:
        create_opportunity(
            "marketing_corp", "improvement", "medium",
            f"{len(dead_wiki)} Wiki Pages With Zero Views",
            f"Published wiki pages with no traffic are not contributing to SEO, "
            f"lead gen, or client value. They need to be discoverable.",
            evidence=f"Pages: {', '.join(p.get('title','?')[:30] for p in dead_wiki[:3])}",
            impact="SEO and authority building stalled",
            effort="low",
            action="Add these pages to sitemap, add internal links from store/portal, syndicate via wiki_syndication_bot",
            systems=["wiki_syndication_bot", "sitemap_generator_bot", "content_corp"],
            auto_actionable=True
        )
        findings.append(f"Zero-view wiki pages: {len(dead_wiki)}")

    # 3. Portal users with no tickets and no deliverables — incomplete onboarding
    portal_users = _supa("GET", "portal_users", "?active=eq.true&onboarded=eq.true&select=id,email") or []
    if portal_users:
        for u in portal_users[:10]:
            tickets = _supa("GET", "tickets", f"?portal_user_id=eq.{u['id']}&select=id&limit=1") or []
            if not tickets:
                create_opportunity(
                    "ops_corp", "gap", "high",
                    f"Portal User {u.get('email','?')[:30]} Has No Tickets",
                    f"An onboarded portal client has zero tickets. This means either "
                    f"onboarding is incomplete or the client doesn't know how to use the portal.",
                    evidence=f"portal_user_id={u['id']}",
                    impact="Client not getting value — churn risk",
                    effort="low",
                    action="Trigger client_onboarding_bot to re-send welcome sequence and create first ticket",
                    systems=["client_onboarding_bot", "itsm_commander_agent"],
                    auto_actionable=True
                )
                findings.append(f"Portal user no tickets: {u.get('email','')[:20]}")
                break  # Only flag once per scan

    # 4. Workflows with no recent success run
    if GH_TOKEN:
        import urllib.request as ur
        try:
            req = ur.Request(
                f"https://api.github.com/repos/{REPO}/actions/runs?per_page=50&status=failure",
                headers={"Authorization": f"token {GH_TOKEN}"})
            with ur.urlopen(req, timeout=15) as r:
                failed_runs = json.loads(r.read()).get("workflow_runs", [])
            # Group by workflow name
            from collections import Counter
            fail_counts = Counter(r["name"] for r in failed_runs)
            persistent_failures = {name: count for name, count in fail_counts.items() if count >= 3}
            if persistent_failures:
                for name, count in list(persistent_failures.items())[:3]:
                    create_opportunity(
                        "citwo_corp", "risk", "high",
                        f"Persistent Workflow Failure: {name[:50]}",
                        f"The workflow '{name}' has failed {count} times recently. "
                        f"This is a persistent failure, not a transient one.",
                        evidence=f"Failure count: {count}",
                        impact="Revenue or operations blocked by recurring failure",
                        effort="medium",
                        action=f"Rob: directly read source code, find root cause, apply fix",
                        systems=[name]
                    )
                    findings.append(f"Persistent failure: {name[:30]}")
        except Exception as e:
            log.warning(f"GitHub workflow scan: {e}")

    return findings


def scan_phase_roadmap():
    """
    What phases are not built?
    What has the Chairman said should exist that doesn't?
    """
    log.info("Scanning phase roadmap...")
    findings = []

    # Check what phases are live
    phases_live = {
        "phase_1": True,   # HubSpot closer layer
        "phase_2": True,   # Project management + wiki
        "phase_3": True,   # Shopify (pending credentials)
        "phase_4": True,   # ITSM + portal
        "phase_5": True,   # BI + Customer 360
        "phase_6": False,  # SOC2 + marketplace
    }

    # Phase 3 is "live" but needs Shopify credentials
    shopify_products = _supa("GET", "store_products",
        "?shopify_id=not.is.null&select=id&limit=1") or []
    if not shopify_products:
        create_opportunity(
            "engineering_corp", "gap", "high",
            "Phase 3 Shopify Not Actually Connected",
            "Phase 3 schema is live and code is deployed but no products have been "
            "pushed to Shopify because SHOPIFY_ACCESS_TOKEN and SHOPIFY_STORE_DOMAIN "
            "secrets are missing from GitHub.",
            evidence="store_products table has 0 shopify_id values",
            impact="$2k-8k/mo MRR unlock blocked by 2 missing secrets",
            effort="low",
            action="Chairman: go to shopify.com/free-trial (5 min). "
                   "Add SHOPIFY_ACCESS_TOKEN + SHOPIFY_STORE_DOMAIN to GitHub secrets.",
            systems=["shopify_store_agent", "phase3_storefront"],
            auto_actionable=False
        )
        findings.append("Phase 3 Shopify not connected")

    # Phase 6 not built
    create_opportunity(
        "strategy_corp", "improvement", "medium",
        "Phase 6 Not Yet Started — SOC2 + Marketplace",
        "Phase 6 (SOC2 compliance + agency marketplace) unlocks $100k–$2M ARR "
        "tier. No schema, no agents, no workflows exist for it yet.",
        evidence="phases_live['phase_6'] = False",
        impact="$100k–$2M ARR unlock sitting idle",
        effort="high",
        action="Build Phase 6: SOC2 audit trails, marketplace listings, enterprise contracts",
        systems=["citwo_corp", "engineering_corp"]
    )
    findings.append("Phase 6 not built")

    return findings


def scan_standing_mandate_compliance():
    """
    Are agents actually following their standing mandates?
    When were mandates last checked?
    """
    log.info("Checking standing mandate compliance...")
    findings = []

    mandates = _supa("GET", "standing_mandates", "?active=eq.true&select=*") or []
    week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()

    stale_mandates = [m for m in mandates
                      if not m.get("last_checked") or m["last_checked"] < week_ago]

    if stale_mandates:
        create_opportunity(
            "qc_corp", "gap", "high",
            f"{len(stale_mandates)} Standing Mandates Never Been Checked",
            f"These mandates define required agent behaviors but have never been "
            f"verified as being followed. Compliance is unknown.",
            evidence=f"Mandates: {', '.join(m['mandate_id'] for m in stale_mandates[:5])}",
            impact="Core operating rules potentially being ignored system-wide",
            effort="low",
            action="Each RSI agent must call check_mandates() in its execute() method",
            systems=["all_rsi_agents", "qc_corp"],
            auto_actionable=False
        )
        findings.append(f"Unchecked mandates: {len(stale_mandates)}")

    return findings


def scan_for_capability_synergies():
    """
    What capabilities exist that aren't connected to each other?
    What data in one table could improve another table?
    """
    log.info("Scanning for unactivated synergies...")
    findings = []

    # 1. Customer 360 data not feeding BI alerts
    c360 = _supa("GET", "customer_360", "?churn_risk=in.(high,critical)&select=id") or []
    bi_churn_alert = _supa("GET", "bi_alerts",
        "?metric_name=eq.churn_risk_count&active=eq.true&select=id") or []
    if c360 and not bi_churn_alert:
        create_opportunity(
            "analytics_corp", "synergy", "medium",
            "C360 Churn Risk Not Connected to BI Alert System",
            f"Customer 360 identifies {len(c360)} high-risk customers but there's "
            f"no BI alert configured to fire when churn risk exceeds threshold.",
            evidence=f"High-risk C360 profiles: {len(c360)}, BI churn alerts: {len(bi_churn_alert)}",
            impact="Churn prevention opportunities being missed",
            effort="low",
            action="BI analytics agent: ensure churn_risk_count KPI is computed and alert threshold is active",
            systems=["bi_analytics_agent", "customer_360", "bi_alerts"],
            auto_actionable=True
        )
        findings.append("C360 not connected to BI alerts")

    # 2. Wiki pages not being included in SEO sitemap
    wiki_count = _supa("GET", "wiki_pages", "?status=eq.published&select=id") or []
    sitemap_wiki = _supa("GET", "sitemap_pages",
        "?url=like.*wiki*&select=id") or []
    if len(wiki_count) > len(sitemap_wiki) + 2:
        create_opportunity(
            "marketing_corp", "synergy", "medium",
            f"{len(wiki_count)-len(sitemap_wiki)} Wiki Pages Missing From Sitemap",
            f"We have {len(wiki_count)} published wiki pages but only {len(sitemap_wiki)} "
            f"wiki URLs in the sitemap. Google can't index what it can't find.",
            evidence=f"Wiki pages: {len(wiki_count)}, Sitemap wiki entries: {len(sitemap_wiki)}",
            impact="Organic traffic loss — each unindexed page is a missed lead",
            effort="low",
            action="Trigger sitemap_generator_bot.py to rebuild sitemap with all wiki URLs",
            systems=["sitemap_generator_bot", "wiki_pages"],
            auto_actionable=True
        )
        findings.append(f"Wiki pages not in sitemap: {len(wiki_count)-len(sitemap_wiki)}")

    # 3. Testimonials table empty — social proof engine has no fuel
    testimonials = _supa("GET", "testimonials", "?status=eq.published&select=id") or []
    if not testimonials:
        create_opportunity(
            "pr_corp", "gap", "high",
            "Testimonials Table Empty — Social Proof Engine Has No Fuel",
            "The social_proof_amplifier_bot exists and is scheduled but the testimonials "
            "table is empty. There is nothing to amplify. The bot runs but does nothing.",
            evidence="testimonials table: 0 published rows",
            impact="Social proof conversion lift (typically 15-30%) not being captured",
            effort="medium",
            action="Seed 3 placeholder testimonials manually, then connect store_reviews -> testimonials sync",
            systems=["social_proof_amplifier_bot", "testimonials", "store_reviews"],
            auto_actionable=False
        )
        findings.append("Empty testimonials table")

    return findings


# ══════════════════════════════════════════════════════════════
# CHAIRMAN BRIEFING BUILDER
# ══════════════════════════════════════════════════════════════

def build_chairman_briefing(all_findings: list):
    """Build today's Chairman intelligence briefing."""
    today = datetime.date.today().isoformat()
    opps = _supa("GET", "intelligence_opportunities",
                 "?status=eq.open&order=priority.asc&select=*&limit=50") or []
    critical = [o for o in opps if o["priority"] == "critical"]
    high     = [o for o in opps if o["priority"] == "high"]
    revenue  = [o for o in opps if o["opportunity_type"] == "revenue"]
    risks    = [o for o in opps if o["opportunity_type"] == "risk"]
    auto_act = [o for o in opps if o.get("auto_actionable")]

    # Generate summary via Claude
    opp_summary = "\n".join(f"- [{o['priority'].upper()}] {o['title']}: {o['description'][:80]}"
                             for o in opps[:10])
    summary = _claude(
        f"You are the Chief Intelligence Officer for NYSR Agency. "
        f"Write a tight 3-sentence executive briefing for the Chairman (S.C. Thomas). "
        f"Cover: most critical issues, revenue opportunities, and recommended priority. "
        f"Never mention you're an AI. Be direct, specific, profit-focused.\n\n"
        f"Open opportunities:\n{opp_summary}",
        max_tokens=200
    ) or f"Intelligence scan complete. {len(opps)} opportunities identified. {len(critical)} critical."

    # Upsert briefing
    existing = _supa("GET", "chairman_briefings", f"?date=eq.{today}&select=id&limit=1") or []
    briefing_data = {
        "date": today,
        "total_opportunities": len(opps),
        "critical_count": len(critical),
        "high_count": len(high),
        "revenue_opportunities": [{"title": o["title"], "impact": o.get("estimated_impact","?")} for o in revenue[:5]],
        "risk_flags": [{"title": o["title"], "action": o.get("recommended_action","?")} for o in risks[:5]],
        "system_improvements": [{"title": o["title"]} for o in opps if o["opportunity_type"] in ["gap","improvement","synergy"]][:5],
        "auto_actioned": [{"title": o["title"]} for o in auto_act[:5]],
        "summary_text": summary,
        "delivered": False,
    }
    if existing:
        _supa("PATCH", "chairman_briefings", briefing_data, query=f"?date=eq.{today}")
    else:
        _supa("POST", "chairman_briefings", briefing_data)

    # Pushover alert for critical items
    if critical:
        crit_list = "\n".join(f"• {o['title'][:50]}" for o in critical[:3])
        _push("🚨 Intel Briefing — ACTION NEEDED",
              f"{len(critical)} CRITICAL opportunities:\n{crit_list}\n\nFull briefing: /bi/",
              priority=1)
    elif high:
        _push("📊 Daily Intel Briefing",
              f"{len(opps)} opportunities found. {len(high)} high priority.\n{summary[:150]}",
              priority=0)

    log.info(f"Chairman briefing built: {len(opps)} opps, {len(critical)} critical, {len(high)} high")
    return len(opps)


# ══════════════════════════════════════════════════════════════
# AUTO-ACTION ENGINE
# ══════════════════════════════════════════════════════════════

def execute_auto_actions():
    """
    For opportunities marked auto_actionable=True, execute them directly.
    No Chairman needed. No waiting.
    """
    auto_opps = _supa("GET", "intelligence_opportunities",
                      "?auto_actionable=eq.true&status=eq.open&select=*&limit=10") or []
    actioned = 0
    now = datetime.datetime.utcnow().isoformat()

    for opp in auto_opps:
        title = opp.get("title","")
        systems = opp.get("affected_systems", [])
        action = opp.get("recommended_action", "")

        # Pattern match to known auto-actions
        acted = False

        if "sitemap" in action.lower() or "sitemap" in " ".join(systems).lower():
            # We can trigger the sitemap generator via GitHub Actions
            if GH_TOKEN:
                import urllib.request as ur
                try:
                    data = json.dumps({"ref": "main"}).encode()
                    req = ur.Request(
                        f"https://api.github.com/repos/{REPO}/actions/workflows/synergy_engine_daily.yml/dispatches",
                        data=data, method="POST",
                        headers={"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json"})
                    ur.urlopen(req, timeout=15)
                    log.info(f"Auto-actioned: triggered synergy engine for sitemap rebuild")
                    acted = True
                except Exception as e:
                    log.warning(f"Auto-action trigger failed: {e}")

        if acted:
            _supa("PATCH", "intelligence_opportunities",
                  {"status": "in_progress", "actioned_at": now,
                   "updated_at": now},
                  query=f"?id=eq.{opp['id']}")
            actioned += 1

    log.info(f"Auto-actioned: {actioned}/{len(auto_opps)} opportunities")
    return actioned


# ══════════════════════════════════════════════════════════════
# MAIN RUN
# ══════════════════════════════════════════════════════════════

def run():
    log.info("═"*60)
    log.info("PROACTIVE INTELLIGENCE ENGINE — SCANNING EVERYTHING")
    log.info("This is the system that should have existed from day one.")
    log.info("═"*60)
    start = time.time()
    all_findings = []

    scans = [
        ("Agent RSI Coverage",       scan_agent_coverage),
        ("Revenue Opportunities",    scan_revenue_opportunities),
        ("System Gaps",              scan_system_gaps),
        ("Phase Roadmap",            scan_phase_roadmap),
        ("Standing Mandate Compliance", scan_standing_mandate_compliance),
        ("Capability Synergies",     scan_for_capability_synergies),
    ]

    for scan_name, scan_fn in scans:
        try:
            findings = scan_fn()
            all_findings.extend(findings)
            log.info(f"  ✓ {scan_name}: {len(findings)} findings")
        except Exception as e:
            log.warning(f"  ✗ {scan_name} failed: {e}")

    # Execute auto-actions
    auto_actioned = execute_auto_actions()

    # Build Chairman briefing
    total_opps = build_chairman_briefing(all_findings)

    elapsed = time.time() - start
    log.info(f"═"*60)
    log.info(f"Intelligence scan complete in {elapsed:.1f}s")
    log.info(f"Findings: {len(all_findings)} | Opportunities created: {total_opps} | Auto-actioned: {auto_actioned}")
    log.info(f"Chairman briefing available at: https://nyspotlightreport.com/intel/")
    log.info("═"*60)

    return {"findings": len(all_findings), "opportunities": total_opps, "auto_actioned": auto_actioned}


if __name__ == "__main__":
    try:
        result = run()
    except Exception as e:
        log.error(f"Intelligence engine error: {e}")
        import traceback; traceback.print_exc()
    sys.exit(0)
