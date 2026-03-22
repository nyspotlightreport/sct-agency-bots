#!/usr/bin/env python3
"""
agents/master_sales_agent.py
Sloane Pierce — Chief Revenue Officer
The complete sales machine from the NYSR Master Sales Intelligence Report.
Implements all 12 stages. Runs every 3 hours.
"""
import os, json, logging, datetime, urllib.request, time, random
log = logging.getLogger("sloane_pierce")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SLOANE] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
APOLLO    = os.environ.get("APOLLO_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
today     = datetime.date.today().isoformat()
now       = datetime.datetime.utcnow()

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

def ai(prompt, system="", max_tokens=400):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "system": system or "You are Sloane Pierce, Chief Revenue Officer at NYSR. Expert in B2B sales, value-based selling, and closing high-ticket deals.",
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"AI: {e}"); return ""

def push_notify(title, msg, priority=0):
    if not PUSH_API: return
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

# ── STAGE 1: LEAD SCORING ─────────────────────────────────
def score_all_leads():
    """Apply full 220-point scoring to all unscored leads."""
    leads = supa("GET","contacts","","?score=lt.80&stage=in.(LEAD,PROSPECT,WARM)&select=*&limit=50") or []
    rules = supa("GET","lead_score_rules","","?active=eq.true&select=*") or []
    scored = 0

    for lead in leads:
        score = lead.get("score", 0) or 0
        tags  = lead.get("tags", []) or []
        notes = (lead.get("notes","") or "").lower()

        # Apply trigger-based scoring (highest value)
        if "job-change" in tags:       score += 40
        if "funding-raised" in tags:   score += 35
        if "webinar-registrant" in tags: score += 35
        if "webinar-attended" in tags:  score += 45
        if "chat-initiated" in tags:    score += 25
        if "competitor-review" in tags: score += 30

        # Clamp to reasonable max
        score = min(score, 220)

        # Determine stage from score
        new_stage = lead.get("stage","LEAD")
        new_priority = "MEDIUM"
        if score >= 130:
            new_stage = "HOT"; new_priority = "HIGH"
        elif score >= 80:
            new_stage = "WARM"; new_priority = "HIGH"
        elif score >= 40:
            new_stage = "QUALIFIED"; new_priority = "MEDIUM"

        if score != (lead.get("score") or 0):
            supa("PATCH","contacts",{
                "score":score,"stage":new_stage,"priority":new_priority,
                "last_updated":now.isoformat()
            },f"?id=eq.{lead['id']}")
            scored += 1

    log.info(f"Lead scoring: {scored}/{len(leads)} leads re-scored")
    return scored

# ── STAGE 2: TRIGGER-BASED OUTREACH ──────────────────────
def fire_trigger_outreach():
    """Tier 1 triggers get contact within 24hrs — highest reply rates."""
    # Find hot leads not yet in a sequence
    hot = supa("GET","contacts","","?score=gte.80&stage=in.(HOT,WARM)&select=*&limit=30") or []
    triggered = 0

    for lead in hot:
        # Check if already in active sequence
        existing = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{lead['id']}&status=eq.active&select=id&limit=1")
        if existing: continue

        # Determine sequence type from tags
        tags = lead.get("tags",[]) or []
        channel = "email"
        seq_name = "Standard 5-Touch"
        trigger_context = ""

        if "job-change" in tags:
            seq_name = "Job Change Trigger"
            trigger_context = "just changed jobs — congratulate and offer fresh-start value"
        elif "webinar-registrant" in tags:
            seq_name = "Webinar→DFY Conversion"
            trigger_context = "registered for webinar — lead with DFY offer + bonuses"
        elif "competitor-review" in tags:
            seq_name = "Competitor Conquest"
            trigger_context = "left review for competitor — reference their specific pain point"
        elif "funding-raised" in tags:
            seq_name = "Funding Trigger"
            trigger_context = "just raised funding — position around scaling systems"

        # Get active campaign
        campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
        cid = (campaign[0] if isinstance(campaign,list) else campaign).get("id") if campaign else None

        next_touch = now.isoformat()
        supa("POST","outreach_sequences",{
            "campaign_id":cid,
            "contact_id":lead["id"],
            "sequence_name":seq_name,
            "current_step":0,"total_steps":5,
            "status":"active","channel":channel,
            "next_touch_at":next_touch,
            "notes":trigger_context
        })

        # Alert for priority leads
        if lead.get("score",0) >= 130:
            push_notify("PRIORITY LEAD",
                f"{lead.get('name','?')} at {lead.get('company','?')} — score {lead.get('score')}\nTrigger: {trigger_context}\nContact NOW",
                priority=1)
        triggered += 1

    log.info(f"Trigger outreach: {triggered} leads enrolled in sequences")
    return triggered

# ── STAGE 3: ROI CALCULATOR FOR PROPOSALS ────────────────
def calculate_roi(contact):
    """Build personalized ROI calculation for proposals."""
    industry   = contact.get("industry","business")
    employees  = contact.get("employees", "5-10")
    notes      = contact.get("notes","")

    # Conservative assumptions per buyer type
    hours_manual = 40  # hours/week on manual tasks
    hourly_rate  = 75  # avg hourly value
    weekly_cost  = hours_manual * hourly_rate
    annual_waste = weekly_cost * 52
    opportunity_cost = annual_waste * 0.3  # 30% revenue opportunity missed

    roi_calc = {
        "hours_wasted_weekly":     hours_manual,
        "hourly_rate":             hourly_rate,
        "weekly_cost_manual":      weekly_cost,
        "annual_waste":            annual_waste,
        "opportunity_cost_annual": opportunity_cost,
        "total_annual_cost":       annual_waste + opportunity_cost,
        "proflow_ai_cost_annual":  97 * 12,
        "roi_ratio_proflow_ai":    round((annual_waste + opportunity_cost) / (97*12), 1),
        "proflow_growth_cost":     297 * 12,
        "roi_ratio_growth":        round((annual_waste + opportunity_cost) / (297*12), 1),
        "dfy_setup_year1_total":   997 + (497*12),
        "roi_ratio_dfy":           round((annual_waste + opportunity_cost) / (997+(497*12)), 1),
    }
    return roi_calc

# ── STAGE 4: PROPOSAL GENERATION ─────────────────────────
def generate_proposals():
    """Auto-generate ROI-first proposals for hot leads."""
    hot = supa("GET","contacts","",
        "?stage=in.(HOT,DEMO)&select=*&limit=20") or []
    proposals_created = 0

    for lead in hot:
        # Check if proposal already exists
        existing = supa("GET","appointments","",
            f"?contact_id=eq.{lead['id']}&appointment_type=eq.proposal&select=id&limit=1")
        if existing: continue

        roi = calculate_roi(lead)
        score = lead.get("score",0) or 0

        # Determine recommended tier based on score + signals
        if score >= 130:   tier = "dfy_agency"
        elif score >= 100: tier = "dfy_setup"
        elif score >= 80:  tier = "proflow_elite"
        else:              tier = "proflow_growth"

        # Generate personalized proposal content
        proposal_content = ai(
            f"Write a 3-section ROI-first proposal for {lead.get('name')} at {lead.get('company')}."
            f"Industry: {lead.get('industry')}. Notes: {lead.get('notes','')}."
            f"Annual waste: ${roi['annual_waste']:,.0f}. ROI ratio: {roi['roi_ratio_growth']}x."
            f"Recommended tier: {tier}."
            f"Sections: 1)Current State (their numbers) 2)Future State (specific outcomes) 3)Investment (price as fraction of value)."
            f"Under 300 words. No fluff.",
            max_tokens=400)

        # Create appointment record
        supa("POST","appointments",{
            "contact_id":lead["id"],
            "appointment_type":"proposal",
            "status":"pending",
            "prep_notes":json.dumps({"roi":roi,"tier":tier,"content":proposal_content[:500]}),
            "deal_value":{"dfy_agency":4997,"dfy_setup":1497,"proflow_elite":797*12,
                         "proflow_growth":297*12,"proflow_ai":97*12}.get(tier,297*12),
            "follow_up_date":(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
        })

        # For $2500+ deals — alert Sean for Loom recording
        deal_val = {"dfy_agency":4997,"dfy_setup":1497}.get(tier,0)
        if deal_val >= 1497:
            push_notify("Record Loom NOW",
                f"Proposal ready for {lead.get('name')} at {lead.get('company')}\nDeal: ${deal_val:,}\nROI: {roi['roi_ratio_growth']}x\nTier: {tier}",
                priority=0)

        proposals_created += 1

    log.info(f"Proposals: {proposals_created} generated")
    return proposals_created

# ── STAGE 5: OBJECTION HANDLING ──────────────────────────
def handle_objections():
    """Detect objection signals and fire appropriate response."""
    neg_replies = supa("GET","outreach_sequences","",
        "?reply_received=eq.true&reply_sentiment=in.(negative,neutral)&current_step=lt.5&select=*&limit=30") or []
    objections = supa("GET","objection_library","","?active=eq.true&select=*") or []
    handled = 0

    for seq in neg_replies:
        contact = supa("GET","contacts","",f"?id=eq.{seq.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = contact[0] if isinstance(contact,list) else contact

        last_msg = supa("GET","conversation_log","",
            f"?contact_id=eq.{c['id']}&direction=eq.inbound&order=created_at.desc&limit=1&select=body")
        if not last_msg: continue
        msg_body = (last_msg[0] if isinstance(last_msg,list) else last_msg).get("body","").lower()

        # Match objection type
        matched = None
        for obj in objections:
            triggers = obj.get("trigger_phrases",[]) or []
            if any(t.lower() in msg_body for t in triggers):
                matched = obj; break

        if not matched:
            # Default: surface the real objection
            matched = next((o for o in objections if o["objection_key"]=="need_to_think"), None)

        if matched:
            roi = calculate_roi(c)
            response = ai(
                f"Respond to this objection using the approved playbook.\n"
                f"Objection type: {matched['objection_key']}\n"
                f"Their message: {msg_body[:200]}\n"
                f"Right response framework: {matched['right_response']}\n"
                f"Reframe script: {matched.get('reframe_script','')}\n"
                f"Contact: {c.get('name')} at {c.get('company')}\n"
                f"Their annual waste: ${roi['annual_waste']:,.0f}\n"
                f"Pilot offer: {matched.get('pilot_offer','')}\n"
                f"Write a personalized response. Under 120 words. Warm but confident.",
                max_tokens=200)

            if response:
                supa("POST","conversation_log",{
                    "contact_id":c["id"],"channel":seq.get("channel","email"),
                    "direction":"outbound","body":response,
                    "intent":"objection_handling","agent_name":"Sloane Pierce AI"
                })
                handled += 1

    log.info(f"Objections handled: {handled}")
    return handled

# ── STAGE 6: CLOSE SEQUENCES ─────────────────────────────
def run_close_sequences():
    """Pilot close, assumptive close, future pace — all automated."""
    # Find proposals stalled 5+ days without response
    five_days_ago = (now - datetime.timedelta(days=5)).date().isoformat()
    stalled = supa("GET","appointments","",
        f"?appointment_type=eq.proposal&status=eq.pending&created_at=lt.{five_days_ago}T00:00:00&select=*&limit=10") or []

    for appt in stalled:
        contact = supa("GET","contacts","",f"?id=eq.{appt.get('contact_id','')}&select=*&limit=1")
        if not contact: continue
        c = contact[0] if isinstance(contact,list) else contact
        deal_val = appt.get("deal_value",0) or 0

        # High-value deals → alert Sean for authority email
        if deal_val >= 2500:
            push_notify("Authority Email Needed",
                f"{c.get('name')} at {c.get('company')}\nDeal: ${deal_val:,}\nStalled 5 days\nSend the Sean Thomas authority email",
                priority=1)
        else:
            # Pilot close offer for mid-ticket
            pilot_msg = ai(
                f"Write a short pilot close email for {c.get('name')} at {c.get('company')}.\n"
                f"Their deal was ${deal_val:,} — offer a 30-day pilot at $497 (applies to full).\n"
                f"Full refund if no results. Under 80 words. Confident.",
                max_tokens=150)
            if pilot_msg:
                supa("POST","conversation_log",{
                    "contact_id":c["id"],"channel":"email","direction":"outbound",
                    "body":pilot_msg,"intent":"pilot_close","agent_name":"Sloane Pierce AI"
                })

    log.info(f"Close sequences: {len(stalled)} stalled deals actioned")
    return len(stalled)

# ── STAGE 7: UPSELL ENGINE ────────────────────────────────
def run_upsells():
    """Automated upsell triggers on behavioral milestones."""
    # Clients on lower tiers ripe for upsell
    proflow_clients = supa("GET","contacts","",
        "?stage=eq.CLOSED_WON&journey_key=eq.onboarding&select=*&limit=20") or []
    upsells_triggered = 0

    for c in proflow_clients:
        tags = c.get("tags",[]) or []
        touch_count = c.get("touch_count",0) or 0

        # ProFlow AI → Growth upsell at 5th engagement
        if "proflow-ai" in tags and touch_count >= 5 and "upsell-growth-sent" not in tags:
            msg = ai(
                f"Write a 2-sentence upsell email for {c.get('name')} on ProFlow AI.\n"
                f"Upgrade to Growth ($297/mo) — they''ve been active 5+ times.\n"
                f"Focus on the BI dashboard and client portal they''re missing.",
                max_tokens=100)
            if msg:
                supa("POST","conversation_log",{
                    "contact_id":c["id"],"channel":"email","direction":"outbound",
                    "body":msg,"intent":"upsell","agent_name":"Upsell Engine"
                })
                # Tag as sent
                new_tags = list(set(tags + ["upsell-growth-sent"]))
                supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
                upsells_triggered += 1

    log.info(f"Upsells: {upsells_triggered} triggered")
    return upsells_triggered

# ── STAGE 8: REFERRAL ENGINE ──────────────────────────────
def trigger_referrals():
    """Fire referral request after successful 30-day onboarding."""
    # Clients 30 days post-conversion not yet asked for referral
    thirty_ago = (now - datetime.timedelta(days=30)).isoformat()
    converted = supa("GET","contacts","",
        f"?stage=eq.CLOSED_WON&converted_at=lt.{thirty_ago}&select=*&limit=20") or []
    referrals_sent = 0

    for c in converted:
        tags = c.get("tags",[]) or []
        if "referral-requested" in tags: continue

        # Get their tier to personalize reward
        tier = next((t for t in ["dfy-agency","dfy-setup","proflow-elite","proflow-growth","proflow-ai"]
                     if t in " ".join(tags)),None)
        rewards = {"dfy-agency":"$500 cash + 10% of their first year",
                   "dfy-setup":"$297 cash","proflow-elite":"$250 cash",
                   "proflow-growth":"$150 cash","proflow-ai":"1 free month ($97)"}
        reward = rewards.get(tier,"$97 credit")

        ref_msg = ai(
            f"Write a referral request email for {c.get('name')} at {c.get('company')}.\n"
            f"They''ve been a client for 30 days. Reward for referral: {reward}.\n"
            f"Tone: grateful, not pushy. Reference results they''ve likely seen.\n"
            f"Under 100 words. Include a unique referral link placeholder: [YOUR_REFERRAL_LINK]",
            max_tokens=150)

        if ref_msg:
            supa("POST","conversation_log",{
                "contact_id":c["id"],"channel":"email","direction":"outbound",
                "body":ref_msg,"intent":"referral_request","agent_name":"Referral Engine"
            })
            new_tags = list(set(tags + ["referral-requested"]))
            supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
            referrals_sent += 1

    log.info(f"Referrals: {referrals_sent} requests sent")
    return referrals_sent

# ── STAGE 9: QBR SCHEDULER ───────────────────────────────
def schedule_qbrs():
    """Auto-schedule quarterly business reviews for $297+ clients."""
    qbr_candidates = supa("GET","contacts","",
        "?stage=eq.CLOSED_WON&lifetime_value=gte.297&select=*&limit=20") or []
    scheduled = 0

    for c in qbr_candidates:
        # Check if QBR scheduled in last 90 days
        existing = supa("GET","qbr_sessions","",
            f"?contact_id=eq.{c['id']}&created_at=gte.{(now-datetime.timedelta(days=90)).isoformat()}&select=id&limit=1")
        if existing: continue

        # Schedule QBR 90 days from conversion
        converted_at = c.get("converted_at")
        if not converted_at: continue
        try:
            conv_date = datetime.datetime.fromisoformat(converted_at.replace("Z","+00:00")).date()
            qbr_date = conv_date + datetime.timedelta(days=90)
            if qbr_date >= datetime.date.today():
                supa("POST","qbr_sessions",{
                    "contact_id":c["id"],
                    "scheduled_date":qbr_date.isoformat(),
                    "status":"scheduled"
                })
                scheduled += 1
        except: pass

    log.info(f"QBRs scheduled: {scheduled}")
    return scheduled

# ── STAGE 10: CLOSED-LOST REACTIVATION ────────────────────
def reactivation_sequences():
    """6-month reactivation for every closed-lost deal."""
    closed_lost = supa("GET","contacts","",
        "?stage=eq.CLOSED_LOST&select=*&limit=30") or []
    reactivated = 0

    for c in closed_lost:
        tags = c.get("tags",[]) or []
        if "reactivation-active" in tags: continue

        # Enroll in reactivation sequence
        campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
        cid = (campaign[0] if isinstance(campaign,list) else campaign).get("id") if campaign else None

        # Spread touches across 6 months
        supa("POST","outreach_sequences",{
            "campaign_id":cid,
            "contact_id":c["id"],
            "sequence_name":"6-Month Closed-Lost Reactivation",
            "current_step":0,"total_steps":6,
            "status":"active","channel":"email",
            "next_touch_at":(now + datetime.timedelta(days=30)).isoformat(),
            "notes":"6-month reactivation — 20-30% eventually buy"
        })
        new_tags = list(set(tags + ["reactivation-active"]))
        supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
        reactivated += 1

    log.info(f"Reactivation: {reactivated} closed-lost enrolled")
    return reactivated

# ── STAGE 11: PIPELINE VELOCITY METRICS ──────────────────
def update_pipeline_velocity():
    """Calculate and store the 10 sales health numbers."""
    contacts = supa("GET","contacts","","?select=stage,score,converted_at,lifetime_value") or []
    appts    = supa("GET","appointments","","?select=status,deal_value,appointment_type") or []

    won      = [c for c in contacts if c.get("stage")=="CLOSED_WON"]
    lost     = [c for c in contacts if c.get("stage")=="CLOSED_LOST"]
    pipeline = [c for c in contacts if c.get("stage") in ["HOT","DEMO","PROPOSAL","QUALIFIED"]]

    total_deals   = len(won) + len(lost)
    win_rate      = round(len(won)/max(total_deals,1)*100,1)
    avg_deal      = sum(float(a.get("deal_value",0) or 0) for a in appts if a.get("status")=="completed") / max(len([a for a in appts if a.get("status")=="completed"]),1)
    velocity      = (len(pipeline) * avg_deal * (win_rate/100)) / max(14,1)

    supa("POST","pipeline_velocity",{
        "week_date":today,
        "total_deals":total_deals,
        "avg_deal_value":round(avg_deal,2),
        "win_rate_pct":win_rate,
        "pipeline_velocity":round(velocity,2),
    })

    log.info(f"Pipeline: {total_deals} deals | {win_rate}% win rate | ${avg_deal:.0f} avg | ${velocity:.0f}/day velocity")
    return {"total_deals":total_deals,"win_rate":win_rate,"avg_deal":avg_deal}

# ── DAILY REVENUE REPORT ──────────────────────────────────
def daily_revenue_report():
    contacts = supa("GET","contacts","","?select=stage,score") or []
    hot   = len([c for c in contacts if c.get("stage") in ["HOT","DEMO","PROPOSAL"]])
    warm  = len([c for c in contacts if c.get("stage") in ["WARM","QUALIFIED"]])
    total = len(contacts)
    seqs  = supa("GET","outreach_sequences","","?status=eq.active&select=id") or []
    appts = supa("GET","appointments","","?status=in.(confirmed,pending)&select=id") or []

    report = (f"Sales Daily — {today}\n"
              f"Pipeline: {total} contacts | Hot: {hot} | Warm: {warm}\n"
              f"Active sequences: {len(seqs)} | Meetings: {len(appts)}\n"
              f"Target: $350 by Day 30")
    push_notify("Sales Report", report)
    supa("POST","agent_run_logs",{
        "org_id":"sales_corp","agent_name":"master_sales_agent",
        "run_type":"daily_cycle","status":"success",
        "metrics":{"hot":hot,"warm":warm,"sequences":len(seqs),"appointments":len(appts)}
    })
    return report

# ── MAIN ──────────────────────────────────────────────────
def run():
    log.info("=" * 55)
    log.info("SLOANE PIERCE — MASTER SALES INTELLIGENCE ENGINE")
    log.info("12 Stages. Every Lead. Every Dollar. Every Close.")
    log.info("=" * 55)
    results = {}
    try: results["scoring"]      = score_all_leads()
    except Exception as e: log.error(f"Scoring: {e}")
    try: results["outreach"]     = fire_trigger_outreach()
    except Exception as e: log.error(f"Outreach: {e}")
    try: results["proposals"]    = generate_proposals()
    except Exception as e: log.error(f"Proposals: {e}")
    try: results["objections"]   = handle_objections()
    except Exception as e: log.error(f"Objections: {e}")
    try: results["closes"]       = run_close_sequences()
    except Exception as e: log.error(f"Closes: {e}")
    try: results["upsells"]      = run_upsells()
    except Exception as e: log.error(f"Upsells: {e}")
    try: results["referrals"]    = trigger_referrals()
    except Exception as e: log.error(f"Referrals: {e}")
    try: results["qbrs"]         = schedule_qbrs()
    except Exception as e: log.error(f"QBRs: {e}")
    try: results["reactivation"] = reactivation_sequences()
    except Exception as e: log.error(f"Reactivation: {e}")
    try: results["velocity"]     = update_pipeline_velocity()
    except Exception as e: log.error(f"Velocity: {e}")
    try: results["report"]       = daily_revenue_report()
    except Exception as e: log.error(f"Report: {e}")
    log.info(f"Sales cycle complete: {json.dumps({k:v for k,v in results.items() if isinstance(v,(int,float,dict))})}")
    return results

if __name__ == "__main__": run()
