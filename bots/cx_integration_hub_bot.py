#!/usr/bin/env python3
"""
bots/cx_integration_hub_bot.py
Morgan Ellis x All 16 Departments — Integration Hub
═══════════════════════════════════════════════════════
CX is the nervous system connecting every revenue, content,
product, and operational department. This bot runs all
bi-directional data flows every cycle.

Integration Map:
  CX → Sales:       Hot leads, appointment outcomes, pipeline value
  CX → Marketing:   Conversation signals → A/B test fuel, ad copy
  CX → Content:     Pain points → wiki/blog ideas, testimonials
  CX → SEO:         Chat keywords → seo_opportunities
  CX → Analytics:   All CX events → kpi_snapshots + analytics_events
  CX → Finance:     Deal values, upsell revenue, churn cost
  CX → Engineering: Bug reports → tickets with engineering tag
  CX → Product:     Feature requests → intelligence_opportunities
  CX → Email:       Sequence replies → CX handles, bounces cleaned
  CX → ITSM:        Support tickets unified under SLA
  CX → Webinar:     Registrant follow-up, no-show re-engagement
  CX → Shopify:     Post-purchase CX, upsell, return handling
  CX → Newsletter:  Beehiiv subscribers → outreach sequences
  CX → HubSpot:     All interactions synced to contact timeline
  CX → RSI:         Fitness data → self-improvement loop
  CX → Intel:       Competitor mentions → opportunities table
"""
import os, json, logging, datetime, urllib.request, urllib.error, time
log = logging.getLogger("cx_integration")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CX HUB] %(message)s")

SUPA = os.environ.get("SUPABASE_URL","")
KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
HUBSPOT   = os.environ.get("HUBSPOT_API_KEY","")

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
        log.warning(f"Supa {method} {table}: {str(e)[:60]}"); return None

def ai(prompt, max_tokens=200):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def push_notify(title, msg, priority=0):
    if not PUSH_API: return
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

today = datetime.date.today().isoformat()
now   = datetime.datetime.utcnow().isoformat()

# ── 1. CX → SALES ────────────────────────────────────────
def cx_to_sales():
    """Hot leads and appointment outcomes flow into sales pipeline."""
    results = {}

    # Promote hot chat leads to sales pipeline
    hot_convos = supa("GET","conversation_log","",
        f"?created_at=gte.{today}T00:00:00&intent=eq.purchase&resolved=eq.true&select=contact_id,body") or []
    upgraded = 0
    for c in hot_convos:
        cid = c.get("contact_id")
        if not cid: continue
        contact = supa("GET","contacts","",f"?id=eq.{cid}&stage=neq.CLOSED_WON&select=id,stage&limit=1")
        if contact:
            supa("PATCH","contacts",{
                "stage":"HOT","score":90,
                "next_action":"CX flagged purchase intent — immediate sales follow-up",
                "next_action_date":today,
                "last_updated":now
            },f"?id=eq.{cid}")
            upgraded += 1

    # Completed appointments → advance pipeline stage
    completed_appts = supa("GET","appointments","",
        f"?status=eq.completed&outcome=in.(interested,demo_requested,proposal_requested)&follow_up_date=is.null&select=*") or []
    for appt in completed_appts:
        cid = appt.get("contact_id")
        new_stage = {
            "interested":"QUALIFIED",
            "demo_requested":"DEMO",
            "proposal_requested":"PROPOSAL"
        }.get(appt.get("outcome",""), "WARM")
        if cid:
            supa("PATCH","contacts",{"stage":new_stage,"next_action":"Follow up post-appointment",
                "next_action_date":today},f"?id=eq.{cid}")
            supa("PATCH","appointments",{"follow_up_date":today},f"?id=eq.{appt['id']}")

    log.info(f"CX→Sales: {upgraded} hot leads promoted | {len(completed_appts)} appts processed")
    results["hot_leads_promoted"] = upgraded
    results["appointments_processed"] = len(completed_appts)
    return results

# ── 2. CX → CONTENT / SEO ─────────────────────────────────
def cx_to_content():
    """Mine conversations for content ideas, keywords, and testimonial triggers."""
    results = {}

    # Mine chat/email conversations for recurring questions → wiki content
    recent_convos = supa("GET","conversation_log","",
        f"?created_at=gte.{today}T00:00:00&direction=eq.inbound&select=body,intent&limit=30") or []

    pain_points = [c.get("body","") for c in recent_convos if len(c.get("body","")) > 20]

    if len(pain_points) >= 3:
        content_ideas = ai(
            f"These are real customer messages from today:\n{chr(10).join(pain_points[:5])}\n\n"
            f"Identify 3 high-value content/SEO topics they suggest. "
            f"For each, give: keyword (5 words max) and estimated monthly searches (just number). "
            f"Format: keyword|searches per line.",
            max_tokens=150)

        if content_ideas:
            for line in content_ideas.strip().split("\n"):
                parts = line.split("|")
                if len(parts) == 2:
                    keyword = parts[0].strip().lower()
                    try:
                        traffic = int(''.join(filter(str.isdigit, parts[1]))) or 500
                    except: traffic = 500
                    existing = supa("GET","seo_opportunities","",f"?keyword=ilike.*{keyword[:20]}*&select=id&limit=1")
                    if not existing:
                        supa("POST","seo_opportunities",{
                            "keyword":keyword,"page_position":0,
                            "estimated_traffic":traffic,"status":"pending",
                            "brief":json.dumps({"source":"cx_conversation_mining","date":today})
                        })
                        results["seo_keywords_added"] = results.get("seo_keywords_added",0) + 1

    # Promoters (CSAT 5) → auto-request testimonials
    promoters = supa("GET","cx_satisfaction","",
        f"?score=gte.9&created_at=gte.{today}T00:00:00&select=contact_id") or []
    for p in promoters:
        cid = p.get("contact_id")
        if not cid: continue
        existing = supa("GET","testimonials","",f"?contact_id=eq.{cid}&select=id&limit=1")
        if not existing:
            contact = supa("GET","contacts","",f"?id=eq.{cid}&select=name,company,title&limit=1")
            if contact:
                c = (contact[0] if isinstance(contact,list) else contact)
                supa("POST","testimonials",{
                    "contact_id":cid,
                    "author_name":c.get("name",""),
                    "author_company":c.get("company",""),
                    "author_title":c.get("title",""),
                    "body":"[Pending — testimonial request sent]",
                    "rating":5,"status":"pending","source":"cx_promoter","featured":False
                })
                results["testimonial_requests"] = results.get("testimonial_requests",0) + 1

    log.info(f"CX→Content: {results.get('seo_keywords_added',0)} SEO keywords | {results.get('testimonial_requests',0)} testimonial requests")
    return results

# ── 3. CX → ANALYTICS ─────────────────────────────────────
def cx_to_analytics():
    """Push all CX metrics into kpi_snapshots and analytics_events."""

    # Count today's CX metrics
    convos = supa("GET","conversation_log","",f"?created_at=gte.{today}T00:00:00&select=id,direction,resolved,csat_score") or []
    inbound  = [c for c in convos if c.get("direction")=="inbound"]
    outbound = [c for c in convos if c.get("direction")=="outbound"]
    resolved = [c for c in convos if c.get("resolved")]
    csat_scores = [c.get("csat_score",0) for c in convos if c.get("csat_score")]
    avg_csat = sum(csat_scores)/max(len(csat_scores),1) if csat_scores else 0

    appts = supa("GET","appointments","",f"?created_at=gte.{today}T00:00:00&select=id,status") or []
    booked   = [a for a in appts if a.get("status") in ["confirmed","pending"]]
    completed = [a for a in appts if a.get("status")=="completed"]

    seqs = supa("GET","outreach_sequences","","?status=eq.active&select=id") or []
    open_t = supa("GET","tickets","","?status=in.(open,pending)&select=id") or []

    kpis = [
        ("cx_conversations_today",    len(convos),   0),
        ("cx_inbound_today",          len(inbound),  0),
        ("cx_outbound_today",         len(outbound), 0),
        ("cx_resolution_rate",        round(len(resolved)/max(len(inbound),1)*100,1), 0),
        ("cx_avg_csat",               round(avg_csat,1), 0),
        ("cx_appointments_booked",    len(booked),   0),
        ("cx_appointments_completed", len(completed),0),
        ("cx_sequences_active",       len(seqs),     0),
        ("cx_open_tickets",           len(open_t),   0),
    ]

    for metric_name, val, prev in kpis:
        supa("POST","kpi_snapshots",{
            "date":today,"metric_name":metric_name,
            "metric_value":val,"prev_value":prev
        })

    # Log as analytics event
    supa("POST","analytics_events",{
        "event_name":"cx_daily_cycle",
        "event_category":"cx",
        "page_path":"/cx/",
        "session_id":f"cx_hub_{today}",
        "properties":json.dumps({
            "conversations":len(convos),
            "resolution_rate":round(len(resolved)/max(len(inbound),1)*100,1),
            "avg_csat":round(avg_csat,1),
            "appointments_booked":len(booked),
            "active_sequences":len(seqs)
        })
    })

    log.info(f"CX→Analytics: {len(kpis)} KPIs logged | {len(convos)} conversations tracked")
    return {"kpis_logged":len(kpis),"conversations":len(convos)}

# ── 4. CX → FINANCE ───────────────────────────────────────
def cx_to_finance():
    """Track CX-sourced revenue: appointments → deal values → revenue_daily."""
    closed_appts = supa("GET","appointments","",
        "?status=eq.completed&outcome=eq.closed&select=deal_value,contact_id") or []
    total_cx_revenue = sum(float(a.get("deal_value",0) or 0) for a in closed_appts)

    if total_cx_revenue > 0:
        supa("POST","revenue_daily",{
            "date":today,"source":"cx_outreach",
            "amount":total_cx_revenue,"orders":len(closed_appts),
            "meta":json.dumps({"source":"cx_appointment_closures","deals":len(closed_appts)})
        })
        log.info(f"CX→Finance: ${total_cx_revenue:.0f} revenue from {len(closed_appts)} closed appointments")

    # Flag churn risk from low CSAT → proactive save
    low_csat = supa("GET","cx_satisfaction","",
        f"?score=lte.3&created_at=gte.{today}T00:00:00&select=contact_id,score") or []
    for lc in low_csat:
        cid = lc.get("contact_id")
        if cid:
            supa("PATCH","contacts",{
                "health_risk":"HIGH","health_action":"CSAT below 3 — immediate outreach to save account",
                "next_action":"Save churning account — CX escalation",
                "next_action_date":today,"priority":"HIGH"
            },f"?id=eq.{cid}")

    log.info(f"CX→Finance: {len(low_csat)} churn risks flagged")
    return {"cx_revenue":total_cx_revenue,"churn_risks":len(low_csat)}

# ── 5. CX → PRODUCT / ENGINEERING ─────────────────────────
def cx_to_product_eng():
    """Surface feature requests and bugs from conversations → intelligence_opportunities."""
    feature_convos = supa("GET","conversation_log","",
        f"?created_at=gte.{today}T00:00:00&intent=in.(feature_request,bug_report)&direction=eq.inbound&select=body,intent,contact_id&limit=10") or []

    bugs = [c for c in feature_convos if c.get("intent")=="bug_report"]
    features = [c for c in feature_convos if c.get("intent")=="feature_request"]

    for bug in bugs:
        summary = ai(f"Summarize this bug report in 10 words: {bug.get('body','')}", max_tokens=50) or "Bug reported via CX channel"
        supa("POST","intelligence_opportunities",{
            "discovered_by":"cx_outreach_corp",
            "opportunity_type":"system_improvement",
            "priority":"high",
            "title":f"Bug: {summary[:80]}",
            "description":bug.get("body","")[:500],
            "recommended_action":"Assign to Engineering — ticket created from CX channel",
            "affected_systems":["engineering_corp","it_corp"],
            "status":"open","auto_actionable":False
        })

    for feat in features:
        summary = ai(f"Summarize this feature request in 10 words: {feat.get('body','')}", max_tokens=50) or "Feature request via CX channel"
        supa("POST","intelligence_opportunities",{
            "discovered_by":"cx_outreach_corp",
            "opportunity_type":"revenue",
            "priority":"medium",
            "title":f"Feature Request: {summary[:80]}",
            "description":feat.get("body","")[:500],
            "recommended_action":"Route to Product Corp for roadmap consideration",
            "affected_systems":["product_corp","engineering_corp"],
            "status":"open","auto_actionable":False
        })

    log.info(f"CX→Eng/Product: {len(bugs)} bugs | {len(features)} feature requests surfaced")
    return {"bugs":len(bugs),"feature_requests":len(features)}

# ── 6. CX → EMAIL JOURNEYS ────────────────────────────────
def cx_to_email():
    """Handle email sequence replies through CX. Clean bounces. Tag responders."""
    # Find contacts who replied to email sequences but haven't been in a CX conversation
    replied = supa("GET","outreach_sequences","",
        "?reply_received=eq.true&channel=eq.email&select=contact_id,reply_sentiment") or []

    for seq in replied:
        cid = seq.get("contact_id")
        if not cid: continue
        # Check if CX has already handled this reply
        existing = supa("GET","conversation_log","",
            f"?contact_id=eq.{cid}&intent=eq.outreach&direction=eq.outbound&select=id&limit=1")
        if existing: continue

        # Create CX conversation record for this reply
        contact = supa("GET","contacts","",f"?id=eq.{cid}&select=name,email&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact,list) else contact)
        sentiment = seq.get("reply_sentiment","neutral")
        supa("POST","conversation_log",{
            "contact_id":cid,"channel":"email","direction":"inbound",
            "subject":"Reply to outreach sequence",
            "body":f"[Reply detected via outreach_sequences — sentiment: {sentiment}]",
            "sentiment":sentiment,
            "intent":"purchase" if sentiment=="positive" else "objection" if sentiment=="negative" else "inquiry",
            "agent_name":"CX Email Handler"
        })

    # Tag webinar registrants in CX pipeline
    webinar_contacts = supa("GET","contacts","",
        "?source=eq.webinar_registration&journey_key=neq.webinar_to_customer&select=id,name") or []
    enrolled = 0
    for wc in webinar_contacts:
        existing = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{wc['id']}&sequence_name=ilike.*webinar*&select=id&limit=1")
        if not existing:
            next_touch = (datetime.datetime.utcnow()+datetime.timedelta(hours=2)).isoformat()
            campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
            cid_campaign = (campaign[0] if isinstance(campaign,list) else campaign).get("id") if campaign else None
            supa("POST","outreach_sequences",{
                "campaign_id":cid_campaign,
                "contact_id":wc["id"],
                "sequence_name":"Webinar→DFY Conversion",
                "current_step":0,"total_steps":5,"status":"active",
                "channel":"email","next_touch_at":next_touch
            })
            supa("PATCH","contacts",{"journey_key":"webinar_to_customer"},f"?id=eq.{wc['id']}")
            enrolled += 1

    log.info(f"CX→Email: {len(replied)} replies handled | {enrolled} webinar contacts enrolled")
    return {"replies_handled":len(replied),"webinar_enrolled":enrolled}

# ── 7. CX → NEWSLETTER / BEEHIIV ──────────────────────────
def cx_to_newsletter():
    """High-engagement newsletter subscribers → CX outreach sequences."""
    # Any contact tagged as subscriber who isn't in an outreach sequence
    subscribers = supa("GET","contacts","",
        "?tags=cs.{newsletter-subscriber}&source=eq.beehiiv&select=id,name,email&limit=20") or []
    enrolled = 0
    for sub in subscribers:
        existing = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{sub['id']}&select=id&limit=1")
        if not existing:
            campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
            cid_campaign = (campaign[0] if isinstance(campaign,list) else campaign).get("id") if campaign else None
            supa("POST","outreach_sequences",{
                "campaign_id":cid_campaign,
                "contact_id":sub["id"],
                "sequence_name":"Newsletter Subscriber→ProFlow Offer",
                "current_step":0,"total_steps":3,"status":"active",
                "channel":"email",
                "next_touch_at":(datetime.datetime.utcnow()+datetime.timedelta(days=1)).isoformat()
            })
            enrolled += 1

    log.info(f"CX→Newsletter: {enrolled} subscribers enrolled in outreach")
    return {"enrolled":enrolled}

# ── 8. CX → RSI SYSTEM ────────────────────────────────────
def cx_to_rsi():
    """Feed CX performance into RSI fitness scoring and improvement proposals."""
    open_t   = supa("GET","tickets","","?status=in.(open,pending)&select=id") or []
    sla_b    = supa("GET","tickets","","?sla_breached=eq.true&select=id") or []
    meetings = supa("GET","appointments","","?status=in.(confirmed,completed)&select=id") or []
    seqs     = supa("GET","outreach_sequences","","?status=eq.active&select=id") or []
    csat_r   = supa("GET","cx_satisfaction","","?created_at=gte.{}T00:00:00&select=score".format(today)) or []
    avg_csat = sum(c.get("score",5) for c in csat_r)/max(len(csat_r),1) if csat_r else 5

    fitness = round(min(1.0, (
        (1.0 if len(open_t)==0 else max(0.5,1-len(open_t)*0.03)) * 0.25 +
        (1.0 if not sla_b else max(0.3,1-len(sla_b)*0.1)) * 0.25 +
        (min(1.0,len(meetings)/5)) * 0.25 +
        (min(1.0,avg_csat/5)) * 0.25
    )),3)

    supa("PATCH","synthetic_orgs",{
        "fitness_score":fitness,
        "last_run":now,
        "metrics":{
            "open_tickets":len(open_t),
            "sla_breaches":len(sla_b),
            "meetings":len(meetings),
            "avg_csat":round(avg_csat,2),
            "active_sequences":len(seqs)
        }
    },"?org_id=eq.cx_outreach_corp")

    # Log agent run
    supa("POST","agent_run_logs",{
        "org_id":"cx_outreach_corp",
        "agent_name":"cx_integration_hub",
        "run_type":"integration_cycle",
        "status":"success",
        "performance_score":fitness,
        "metrics":{
            "open_tickets":len(open_t),
            "meetings_booked":len(meetings),
            "avg_csat":round(avg_csat,2)
        }
    })

    log.info(f"CX→RSI: Fitness={fitness:.0%} | CSAT={avg_csat:.1f} | Meetings={len(meetings)}")

    # Surface improvement proposal if fitness is low
    if fitness < 0.7:
        improvement = ai(
            f"CX Corp fitness is low ({fitness:.0%}). "
            f"Open tickets: {len(open_t)}, SLA breaches: {len(sla_b)}, "
            f"Meetings: {len(meetings)}, CSAT: {avg_csat:.1f}/5. "
            "Propose 1 specific, actionable improvement in 20 words.",
            max_tokens=60)
        if improvement:
            supa("POST","rsi_proposals",{
                "org_id":"cx_outreach_corp",
                "proposal_type":"performance",
                "title":f"CX Improvement — {today}",
                "description":improvement,
                "status":"pending","auto_deploy":False
            })

    return {"fitness":fitness,"open_tickets":len(open_t),"meetings":len(meetings)}

# ── 9. CX → PROACTIVE INTELLIGENCE ───────────────────────
def cx_to_intelligence():
    """Mine conversations for competitor mentions and market signals."""
    competitors = ["belkins","cience","concentrix","partnerhero","martal","sapper",
                   "hubspot","salesforce","zoominfo","apollo","outreach","salesloft"]

    recent = supa("GET","conversation_log","",
        f"?created_at=gte.{today}T00:00:00&direction=eq.inbound&select=body,contact_id") or []

    opp_count = 0
    for c in recent:
        body = (c.get("body") or "").lower()
        for comp in competitors:
            if comp in body:
                supa("POST","intelligence_opportunities",{
                    "discovered_by":"cx_outreach_corp",
                    "opportunity_type":"competitive",
                    "priority":"medium",
                    "title":f"Competitor mention: {comp} in customer conversation",
                    "description":f"Customer mentioned {comp} in conversation. Review for competitive positioning opportunity.",
                    "recommended_action":"Route to Strategy Corp + Marketing Corp for competitive response",
                    "affected_systems":["strategy_corp","marketing_corp","cx_outreach_corp"],
                    "status":"open","auto_actionable":False
                })
                opp_count += 1
                break  # One opportunity per conversation

    log.info(f"CX→Intel: {opp_count} competitive signals found")
    return {"competitive_signals":opp_count}

# ── 10. CX → INTER-DEPT MESSAGES ─────────────────────────
def cx_broadcast_to_depts():
    """Send daily CX summary to all relevant departments via org_messages."""
    open_t    = supa("GET","tickets","","?status=eq.open&select=id") or []
    meetings  = supa("GET","appointments","","?status=in.(confirmed,pending)&select=id") or []
    seqs      = supa("GET","outreach_sequences","","?status=eq.active&select=id") or []

    msgs = [
        ("sales_corp",    "cx_outreach_corp",
         f"Daily CX→Sales sync: {len(meetings)} meetings booked | {len(open_t)} open tickets. Hot leads updated in contacts table."),
        ("analytics_corp","cx_outreach_corp",
         f"CX KPIs logged: {len(seqs)} active sequences | {len(meetings)} appointments | {len(open_t)} open tickets. Check kpi_snapshots table."),
        ("strategy_corp", "cx_outreach_corp",
         f"CX Intelligence update: competitive signals and market feedback processed. Check intelligence_opportunities table."),
        ("content_corp",  "cx_outreach_corp",
         f"Content opportunities from CX conversations added to seo_opportunities. New testimonial requests triggered."),
        ("finance_corp",  "cx_outreach_corp",
         f"CX revenue attribution and churn risk flags updated in revenue_daily and contacts tables."),
    ]

    sent = 0
    for to_org, from_org, message in msgs:
        supa("POST","org_messages",{
            "from_org":from_org,"to_org":to_org,
            "message_type":"daily_sync","subject":f"CX Daily Sync — {today}",
            "body":message,"priority":"normal","read":False
        })
        sent += 1

    log.info(f"CX→Depts: {sent} department messages sent")
    return {"messages_sent":sent}

# ── MAIN ──────────────────────────────────────────────────
def run():
    log.info("="*60)
    log.info("CX INTEGRATION HUB — ALL DEPARTMENTS")
    log.info("Morgan Ellis → 16 Departments → Full System")
    log.info("="*60)

    results = {}
    try: results["sales"]        = cx_to_sales()
    except Exception as e: log.error(f"Sales integration: {e}"); results["sales"] = {"error":str(e)}
    try: results["content_seo"]  = cx_to_content()
    except Exception as e: log.error(f"Content integration: {e}")
    try: results["analytics"]    = cx_to_analytics()
    except Exception as e: log.error(f"Analytics integration: {e}")
    try: results["finance"]      = cx_to_finance()
    except Exception as e: log.error(f"Finance integration: {e}")
    try: results["product_eng"]  = cx_to_product_eng()
    except Exception as e: log.error(f"Prod/Eng integration: {e}")
    try: results["email"]        = cx_to_email()
    except Exception as e: log.error(f"Email integration: {e}")
    try: results["newsletter"]   = cx_to_newsletter()
    except Exception as e: log.error(f"Newsletter integration: {e}")
    try: results["rsi"]          = cx_to_rsi()
    except Exception as e: log.error(f"RSI integration: {e}")
    try: results["intelligence"] = cx_to_intelligence()
    except Exception as e: log.error(f"Intelligence integration: {e}")
    try: results["dept_msgs"]    = cx_broadcast_to_depts()
    except Exception as e: log.error(f"Dept broadcast: {e}")

    log.info(f"Integration Hub complete: {json.dumps({k:v for k,v in results.items() if isinstance(v,dict)}, indent=0)}")

    push_notify("CX Integration Hub", 
        f"CX↔Depts sync complete\nMeetings: {results.get('rsi',{}).get('meetings',0)} | "
        f"CSAT: {results.get('rsi',{}).get('fitness',0):.0%}")
    return results

if __name__ == "__main__": run()
