#!/usr/bin/env python3
"""
agents/sales_force/director.py — Victoria Cross, VP Sales Force Operations
Orchestrates daily sales force operations: pipeline review, lead scoring,
outreach prioritization, rep performance tracking.
"""
import os, sys, json, logging, time
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
log = logging.getLogger("sales_force_director")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SALES-FORCE] %(message)s")
import urllib.request as urlreq, urllib.parse

# ═══ CREDENTIALS ═══
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")

# Products and commission structure
PRODUCTS = {
    "dfy_content_engine":    {"name": "DFY Content Engine Setup",   "price": 1497,  "commission": 299},
    "dfy_full_automation":   {"name": "DFY Full Agency Automation", "price": 4997,  "commission": 999},
    "enterprise_proflow":    {"name": "Enterprise ProFlow License", "price": 9997,  "commission": 1999},
    "white_label":           {"name": "White-Label Partnership",    "price": 14997, "commission": 2999},
    "custom_ai_department":  {"name": "Custom AI Department Build", "price": 24997, "commission": 4999},
}


def _api(url, data, headers, timeout=30):
    """Universal API caller."""
    body = json.dumps(data).encode() if isinstance(data, dict) else data
    req = urlreq.Request(url, data=body, headers=headers)
    try:
        start = time.time()
        with urlreq.urlopen(req, timeout=timeout) as r:
            return r.read(), int((time.time() - start) * 1000), None
    except Exception as e:
        return None, 0, str(e)[:200]


def push(t, m, p=0):
    """Send Pushover notification."""
    if not PUSH_API:
        return
    try:
        urlreq.urlopen(
            "https://api.pushover.net/1/messages.json",
            urllib.parse.urlencode({
                "token": PUSH_API, "user": PUSH_USER,
                "title": t[:100], "message": m[:1000], "priority": p
            }).encode(), timeout=5
        )
    except Exception:
        pass


def supa_log(data):
    """Log results to Supabase."""
    if not SUPA_URL:
        return
    try:
        req = urlreq.Request(
            f"{SUPA_URL}/rest/v1/director_outputs",
            data=json.dumps(data).encode(), method="POST",
            headers={
                "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json", "Prefer": "return=minimal"
            }
        )
        urlreq.urlopen(req, timeout=10)
    except Exception:
        pass


def supa_query(table, select="*", filters=None, limit=100):
    """Query Supabase table with optional filters."""
    if not SUPA_URL:
        return []
    url = f"{SUPA_URL}/rest/v1/{table}?select={select}&limit={limit}"
    if filters:
        for k, v in filters.items():
            url += f"&{k}={urllib.parse.quote(str(v))}"
    req = urlreq.Request(
        url, method="GET",
        headers={
            "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urlreq.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"  Supabase query failed: {e}")
        return []


def claude(system, prompt, max_tokens=1000):
    """Call Claude API for analysis."""
    if not ANTHROPIC:
        return ""
    data = {
        "model": "claude-sonnet-4-20250514", "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}]
    }
    result, ms, err = _api(
        "https://api.anthropic.com/v1/messages", data,
        {"Content-Type": "application/json", "x-api-key": ANTHROPIC,
         "anthropic-version": "2023-06-01"}
    )
    if result:
        return json.loads(result)["content"][0]["text"]
    return ""


# ═══ PIPELINE DATA ═══
def pull_pipeline_data():
    """Pull current sales pipeline from Supabase."""
    if not SUPA_URL:
        log.warning("  SKIP pipeline pull — no SUPABASE_URL")
        return {"leads": [], "deals": [], "reps": []}

    leads = supa_query("leads", limit=200)
    deals = supa_query("deals", limit=200)
    reps = supa_query("sales_reps", limit=50)

    log.info(f"  PIPELINE: {len(leads)} leads, {len(deals)} deals, {len(reps)} reps")
    return {"leads": leads, "deals": deals, "reps": reps}


# ═══ LEAD SCORING ═══
SCORING_SYSTEM = """You are Victoria Cross, VP Sales Force Operations.
Score leads on a 0-100 scale based on: company size, industry fit, engagement signals,
budget indicators, and decision-maker status.
Return ONLY valid JSON array: [{"lead_id":"...","score":N,"reason":"one line"}]
Do not include any text outside the JSON array."""


def score_leads(leads):
    """AI-powered lead scoring using Claude."""
    if not leads:
        log.info("  SCORING: No leads to score")
        return []
    if not ANTHROPIC:
        log.warning("  SKIP lead scoring — no ANTHROPIC_API_KEY")
        return []

    # Prepare compact lead summaries for scoring
    lead_summaries = []
    for lead in leads[:30]:  # Cap at 30 to stay within token limits
        lead_summaries.append({
            "id": lead.get("id", ""),
            "company": lead.get("company", "unknown"),
            "title": lead.get("title", ""),
            "industry": lead.get("industry", ""),
            "source": lead.get("source", ""),
            "engagement": lead.get("engagement_score", 0),
        })

    prompt = f"Score these leads for high-ticket AI solution sales:\n{json.dumps(lead_summaries, indent=2)}"
    response = claude(SCORING_SYSTEM, prompt, max_tokens=2000)

    scored = []
    if response:
        try:
            scored = json.loads(response)
            log.info(f"  SCORED: {len(scored)} leads")
        except json.JSONDecodeError:
            log.warning("  SCORING: Claude returned non-JSON response")
    return scored


# ═══ OUTREACH PRIORITIES ═══
OUTREACH_SYSTEM = """You are Victoria Cross, VP Sales Force Operations.
Given scored leads, generate a prioritized outreach plan for today.
Return ONLY valid JSON array: [{"lead_id":"...","action":"call|email|linkedin","priority":"hot|warm|nurture","talking_point":"one line"}]
Focus on highest-scored leads first. Limit to top 10."""


def generate_outreach_priorities(scored_leads, pipeline):
    """Generate daily outreach priorities from scored leads."""
    if not scored_leads:
        log.info("  OUTREACH: No scored leads for prioritization")
        return []
    if not ANTHROPIC:
        log.warning("  SKIP outreach generation — no ANTHROPIC_API_KEY")
        return []

    deals = pipeline.get("deals", [])
    context = {
        "scored_leads": scored_leads[:20],
        "active_deals": len(deals),
        "today": datetime.utcnow().strftime("%A, %B %d, %Y"),
    }

    prompt = f"Generate today's outreach priorities:\n{json.dumps(context, indent=2)}"
    response = claude(OUTREACH_SYSTEM, prompt, max_tokens=1500)

    priorities = []
    if response:
        try:
            priorities = json.loads(response)
            log.info(f"  OUTREACH: {len(priorities)} priorities generated")
        except json.JSONDecodeError:
            log.warning("  OUTREACH: Claude returned non-JSON response")
    return priorities


# ═══ REP PERFORMANCE ═══
def analyze_rep_performance(reps, deals):
    """Analyze sales rep performance metrics."""
    if not reps:
        log.info("  REPS: No rep data available")
        return []

    summaries = []
    for rep in reps:
        rep_id = rep.get("id", "")
        rep_deals = [d for d in deals if d.get("rep_id") == rep_id]
        closed = [d for d in rep_deals if d.get("status") == "closed_won"]
        revenue = sum(d.get("amount", 0) for d in closed)
        commission = int(revenue * 0.20)
        summaries.append({
            "rep_id": rep_id,
            "name": rep.get("name", "Unknown"),
            "total_deals": len(rep_deals),
            "closed_won": len(closed),
            "revenue": revenue,
            "commission": commission,
            "win_rate": round(len(closed) / max(len(rep_deals), 1) * 100, 1),
        })

    summaries.sort(key=lambda x: x["revenue"], reverse=True)
    for s in summaries[:5]:
        log.info(f"  REP: {s['name']} — {s['closed_won']} closed, ${s['revenue']:,} revenue, {s['win_rate']}% win rate")
    return summaries


# ═══ APOLLO ENRICHMENT CHECK ═══
def check_apollo():
    """Verify Apollo.io API connectivity for lead enrichment."""
    if not APOLLO_KEY:
        log.warning("  SKIP Apollo check — no APOLLO_API_KEY")
        return {"status": "skipped", "reason": "no_api_key"}
    result, latency, err = _api(
        "https://api.apollo.io/api/v1/auth/health",
        {"api_key": APOLLO_KEY},
        {"Content-Type": "application/json", "Cache-Control": "no-cache"}
    )
    if result:
        log.info(f"  APOLLO: API reachable ({latency}ms)")
        return {"status": "ok", "latency_ms": latency}
    log.warning(f"  APOLLO: API check failed — {err}")
    return {"status": "error", "error": err}


# ═══ RUN: DAILY SALES FORCE OPERATIONS ═══
def run():
    """Orchestrate daily sales force operations."""
    log.info("=" * 60)
    log.info("SALES FORCE DEPARTMENT — Director Victoria Cross")
    log.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    log.info("=" * 60)

    results = {}
    errors = []

    # Credential check
    log.info("\n[1/6] Checking credentials...")
    creds = {
        "anthropic": bool(ANTHROPIC),
        "supabase": bool(SUPA_URL),
        "pushover": bool(PUSH_API),
        "apollo": bool(APOLLO_KEY),
    }
    for k, v in creds.items():
        log.info(f"  {k.title()}={'YES' if v else 'NO'}")
    results["credentials"] = creds

    # Pull pipeline
    log.info("\n[2/6] Pulling pipeline data...")
    pipeline = pull_pipeline_data()
    results["pipeline"] = {
        "leads": len(pipeline["leads"]),
        "deals": len(pipeline["deals"]),
        "reps": len(pipeline["reps"]),
    }

    # Score leads
    log.info("\n[3/6] Scoring leads...")
    scored = score_leads(pipeline["leads"])
    results["scored_leads"] = len(scored)
    hot_leads = [s for s in scored if s.get("score", 0) >= 70]
    log.info(f"  HOT LEADS (70+): {len(hot_leads)}")

    # Generate outreach
    log.info("\n[4/6] Generating outreach priorities...")
    outreach = generate_outreach_priorities(scored, pipeline)
    results["outreach_priorities"] = len(outreach)

    # Rep performance
    log.info("\n[5/6] Analyzing rep performance...")
    rep_perf = analyze_rep_performance(pipeline["reps"], pipeline["deals"])
    results["active_reps"] = len(rep_perf)
    total_revenue = sum(r.get("revenue", 0) for r in rep_perf)
    results["total_revenue"] = total_revenue

    # Apollo check
    log.info("\n[6/6] Checking Apollo enrichment API...")
    results["apollo"] = check_apollo()

    # Summary
    status = "operational"
    if not creds["supabase"]:
        status = "degraded"
        errors.append("no Supabase connection — pipeline data unavailable")
    if not creds["anthropic"]:
        status = "degraded"
        errors.append("no Claude API — lead scoring/outreach unavailable")

    summary = (
        f"Pipeline: {results['pipeline']['leads']}L/{results['pipeline']['deals']}D/{results['pipeline']['reps']}R | "
        f"Scored: {results['scored_leads']} | Hot: {len(hot_leads)} | "
        f"Outreach: {results['outreach_priorities']} | Revenue: ${total_revenue:,}"
    )

    log.info(f"\n{'=' * 60}")
    log.info(f"SALES FORCE: {status.upper()} — {summary}")
    if errors:
        for e in errors:
            log.error(f"  ISSUE: {e}")
    log.info(f"{'=' * 60}")

    # Log to Supabase
    supa_log({
        "director": "Victoria Cross",
        "output_type": "daily_sales_ops",
        "content": json.dumps({
            "status": status,
            "summary": summary,
            "pipeline": results.get("pipeline"),
            "scored_leads": results["scored_leads"],
            "hot_leads": len(hot_leads),
            "outreach_count": results["outreach_priorities"],
            "total_revenue": total_revenue,
            "active_reps": results["active_reps"],
            "errors": errors,
        })[:4000],
        "created_at": datetime.utcnow().isoformat()
    })

    # Notify
    priority = 0 if not errors else 1
    push(
        f"Sales Force | {status.upper()}",
        summary + ("\n" + "\n".join(f"- {e}" for e in errors) if errors else ""),
        priority
    )

    return {"status": status, "summary": summary, "results": results, "errors": errors}


if __name__ == "__main__":
    run()
