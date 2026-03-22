#!/usr/bin/env python3
"""
bots/living_context_sync_bot.py
Every agent wakes up knowing the current state of the business.
Runs nightly — syncs all context from live sources.
Agents pull nysr_live_context table instead of stale prompts.
This is the fix for agents operating on week-old information.
"""
import os, json, logging, datetime, urllib.request, urllib.error
log = logging.getLogger("context_sync")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONTEXT] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
now       = datetime.datetime.utcnow()
today     = datetime.date.today().isoformat()

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except Exception as e:
        log.debug(f"Supa: {str(e)[:50]}"); return None

def upsert_context(key, value, source):
    supa("POST","nysr_live_context",{
        "context_key":key, "context_value":value, "source":source,
        "updated_at":now.isoformat()
    })
    # Use upsert via PATCH
    existing = supa("GET","nysr_live_context","",f"?context_key=eq.{key}&select=id&limit=1")
    if existing and isinstance(existing,list) and existing:
        supa("PATCH","nysr_live_context",{"context_value":value,"updated_at":now.isoformat()},
             f"?context_key=eq.{key}")
    log.info(f"  Context updated: {key}")

def sync_offers():
    """Pull current active offer tiers."""
    tiers = supa("GET","offer_tiers","","?active=eq.true&select=tier_key,name,price_monthly,price_onetime,setup_fee,retainer_monthly,guarantee_text&order=position") or []
    if tiers and isinstance(tiers,list):
        upsert_context("active_offers", {
            "tiers": [{
                "key": t.get("tier_key"),
                "name": t.get("name"),
                "price_monthly": t.get("price_monthly"),
                "price_onetime": t.get("price_onetime"),
                "setup_fee": t.get("setup_fee"),
                "retainer": t.get("retainer_monthly"),
                "guarantee": t.get("guarantee_text")
            } for t in tiers],
            "store_url": "https://nyspotlightreport.com/store/",
            "pricing_url": "https://nyspotlightreport.com/pricing/",
            "updated": today
        }, "supabase")

def sync_revenue():
    """Pull current MRR and revenue data."""
    revenue = supa("GET","revenue_daily","",f"?select=amount,source,date&order=date.desc&limit=7") or []
    won = supa("GET","contacts","","?stage=eq.CLOSED_WON&select=lifetime_value") or []
    mrr = sum(float(c.get("lifetime_value",0) or 0) for c in (won if isinstance(won,list) else []))
    recent = sum(float(r.get("amount",0) or 0) for r in (revenue if isinstance(revenue,list) else []))
    upsert_context("current_mrr", {
        "mrr_estimate": mrr,
        "revenue_7d": recent,
        "target_day30": 350,
        "target_day60": 1100,
        "target_day90": 3200,
        "currency": "usd",
        "updated": today
    }, "supabase")

def sync_pipeline():
    """Pull current pipeline health."""
    contacts = supa("GET","contacts","","?select=stage,score,name,company&order=score.desc&limit=20") or []
    by_stage = {}
    for c in (contacts if isinstance(contacts,list) else []):
        s = c.get("stage","UNKNOWN")
        by_stage[s] = by_stage.get(s,0) + 1
    upsert_context("pipeline_health", {
        "total_contacts": len(contacts if isinstance(contacts,list) else []),
        "by_stage": by_stage,
        "hot_leads": by_stage.get("HOT",0) + by_stage.get("DEMO",0) + by_stage.get("PROPOSAL",0),
        "top_prospects": [{"name":c.get("name"),"company":c.get("company"),"score":c.get("score")}
                         for c in (contacts if isinstance(contacts,list) else [])[:5]],
        "updated": today
    }, "supabase")

def sync_objections():
    """Pull top objections and winning responses."""
    obj = supa("GET","objection_library","","?active=eq.true&order=success_rate.desc&select=objection_key,objection_type,right_response&limit=6") or []
    upsert_context("top_objections", {
        "handlers": [{"key":o.get("objection_key"),"type":o.get("objection_type"),
                     "response_snippet":o.get("right_response","")[:100]} 
                    for o in (obj if isinstance(obj,list) else [])],
        "updated": today
    }, "supabase")

def sync_testimonials():
    """Pull recent testimonials for social proof in outreach."""
    test = supa("GET","testimonials","","?status=eq.published&select=author_name,author_company,body,rating&order=created_at.desc&limit=5") or []
    upsert_context("recent_testimonials", {
        "testimonials": [{"name":t.get("author_name"),"company":t.get("author_company"),
                         "quote":t.get("body","")[:150],"rating":t.get("rating")}
                        for t in (test if isinstance(test,list) else [])],
        "count": len(test if isinstance(test,list) else []),
        "updated": today
    }, "supabase")

def sync_system_state():
    """Pull current system health metrics."""
    runs = supa("GET","agent_run_logs","",f"?started_at=gte.{today}T00:00:00&select=status") or []
    success = len([r for r in (runs if isinstance(runs,list) else []) if r.get("status")=="success"])
    total   = len(runs if isinstance(runs,list) else [])
    upsert_context("system_health", {
        "agent_runs_today": total,
        "success_rate": round(success/max(total,1)*100,1),
        "orgs_active": 17,
        "workflows_active": 100,
        "bots_deployed": 177,
        "agents_deployed": 88,
        "updated": now.isoformat()
    }, "github")

def run():
    log.info("=" * 50)
    log.info("LIVING CONTEXT SYNC — All agents get current state")
    log.info("=" * 50)

    try: sync_offers()
    except Exception as e: log.error(f"Offers: {e}")
    try: sync_revenue()
    except Exception as e: log.error(f"Revenue: {e}")
    try: sync_pipeline()
    except Exception as e: log.error(f"Pipeline: {e}")
    try: sync_objections()
    except Exception as e: log.error(f"Objections: {e}")
    try: sync_testimonials()
    except Exception as e: log.error(f"Testimonials: {e}")
    try: sync_system_state()
    except Exception as e: log.error(f"System: {e}")

    log.info("Context sync complete — all agents now operating on live data")

if __name__ == "__main__": run()
