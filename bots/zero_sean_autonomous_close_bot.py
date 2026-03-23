#!/usr/bin/env python3
"""
bots/zero_sean_autonomous_close_bot.py
The machine closes deals. Sean finds out after.
All 6 layers from Report 7 — running 24/7.
Sub-$3,000 deals: fully autonomous.
$3,000+ deals: pre-qualified + pre-sold before Sean sees them.
"""
import os, json, logging, datetime, urllib.request, urllib.error
log = logging.getLogger("zero_sean")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ZERO-SEAN] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
now       = datetime.datetime.utcnow()
today     = datetime.date.today().isoformat()

STRIPE_LINK_PROFLOW_AI     = "https://nyspotlightreport.com/store/"
STRIPE_LINK_PROFLOW_GROWTH = "https://nyspotlightreport.com/store/"
STRIPE_LINK_PROFLOW_ELITE  = "https://nyspotlightreport.com/store/"
STRIPE_LINK_PILOT          = "https://nyspotlightreport.com/store/"
AUDIT_URL                  = "https://nyspotlightreport.com/audit/"
WEBINAR_URL                = "https://nyspotlightreport.com/webinar/"

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def ai(prompt, max_tokens=300):
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
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,
                        "message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: bare-except

        pass
# LAYER 1: SELF-SERVE CHECKOUT — route warm leads to store ─
def route_to_self_serve():
    """Every ready-to-buy lead gets a direct Stripe link. No call needed."""
    hot = supa("GET","contacts","",
        "?score=gte.100&stage=in.(HOT,WARM)&select=id,name,email,tags,score&limit=15") or []
    if not isinstance(hot, list): return 0

    routed = 0
    for c in hot:
        tags  = c.get("tags",[]) or []
        score = c.get("score",0) or 0
        if "checkout-link-sent" in tags: continue

        # Determine right product based on score
        if score >= 160:  link_name = "DFY Setup"; link = f"{STRIPE_LINK_PILOT}#dfy-setup"
        elif score >= 130: link_name = "ProFlow Elite"; link = f"{STRIPE_LINK_PROFLOW_ELITE}#elite"
        elif score >= 110: link_name = "ProFlow Growth"; link = f"{STRIPE_LINK_PROFLOW_GROWTH}#growth"
        else:              link_name = "ProFlow AI"; link = f"{STRIPE_LINK_PROFLOW_AI}#ai"

        msg = ai(
            f"Write a 2-sentence checkout nudge for {c.get('name')}.\n"
            f"Product: {link_name}. Include the link: {link}\n"
            f"They''re warm and ready. Just need the direct path.\n"
            f"Under 40 words. Direct and confident.",
            max_tokens=80)

        if msg:
            supa("POST","conversation_log",{"contact_id":c["id"],"channel":"email",
                "direction":"outbound","body":msg,"intent":"checkout_nudge",
                "agent_name":"Zero-Sean Bot"})
            new_tags = list(set(tags + ["checkout-link-sent"]))
            supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
            routed += 1

    log.info(f"Self-serve routing: {routed} leads sent checkout links")
    return routed

# LAYER 2: CHATBOT CONVERSATION HANDLER ───────────────────
def process_chat_leads():
    """Process chat conversations and advance warm ones to checkout."""
    chat_leads = supa("GET","contacts","",
        "?tags=cs.{chat-initiated}&stage=in.(LEAD,WARM)&select=*&limit=10") or []
    if not isinstance(chat_leads, list): return 0

    advanced = 0
    for c in chat_leads:
        tags = c.get("tags",[]) or []
        if "chat-advanced" in tags: continue

        # Get last chat message
        last_chat = supa("GET","conversation_log","",
            f"?contact_id=eq.{c['id']}&channel=eq.chat&direction=eq.inbound&order=created_at.desc&limit=1&select=body")
        if not last_chat: continue
        last_msg = (last_chat[0] if isinstance(last_chat,list) else last_chat).get("body","")

        # Generate chatbot response with Stripe link
        resp = ai(
            f"Continue this sales chatbot conversation for NYSR.\n"
            f"Their last message: {last_msg[:200]}\n"
            f"Our goal: qualify and get them to click the payment link.\n"
            f"Offer: ProFlow AI $97/mo or 30-day pilot $497 (no risk).\n"
            f"Include payment link: {STRIPE_LINK_PROFLOW_AI}\n"
            f"Under 60 words. Natural chatbot tone.",
            max_tokens=100)

        if resp:
            supa("POST","conversation_log",{"contact_id":c["id"],"channel":"chat",
                "direction":"outbound","body":resp,"intent":"chatbot_close",
                "agent_name":"Zero-Sean Bot"})
            new_tags = list(set(tags + ["chat-advanced"]))
            supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
            advanced += 1

    log.info(f"Chat close: {advanced} conversations advanced with payment links")
    return advanced

# LAYER 3: VOICE AGENT QUEUE (Bland AI integration point) ──
def queue_voice_calls():
    """Queue inbound form leads for Bland AI voice calls."""
    # Find new audit/form leads not yet called
    form_leads = supa("GET","contacts","",
        "?source=eq.lead_magnet&tags=not.cs.{voice-called}&score=gte.50&select=*&limit=10") or []
    if not isinstance(form_leads, list): return 0

    queued = 0
    for c in form_leads:
        tags = c.get("tags",[]) or []
        if "voice-queued" in tags: continue

        # Queue for Bland AI call
        # In production: POST to Bland AI /v1/calls endpoint
        call_script = ai(
            f"Write a 60-second voice call script for an AI agent calling {c.get('name')}.\n"
            f"They just requested a free AI audit at {AUDIT_URL}.\n"
            f"Goal: deliver 1 audit insight + offer ProFlow AI or pilot.\n"
            f"Script format: greeting → insight → offer → payment link via SMS.\n"
            f"Under 120 words. Natural spoken English.",
            max_tokens=160)

        if call_script:
            # Log the queued call
            supa("POST","appointments",{
                "contact_id":c["id"],"appointment_type":"voice_ai_call",
                "status":"queued","prep_notes":call_script,
                "deal_value":97
            })
            new_tags = list(set(tags + ["voice-queued"]))
            supa("PATCH","contacts",{"tags":new_tags},f"?id=eq.{c['id']}")
            queued += 1

    log.info(f"Voice queue: {queued} leads queued for Bland AI calls ($0.09/min = sub-$1 per call)")
    return queued

# LAYER 4: EMAIL SEQUENCE MANAGER ─────────────────────────
def manage_email_sequences():
    """Ensure every lead is in an active 7-email close sequence."""
    all_leads = supa("GET","contacts","",
        "?stage=in.(LEAD,WARM,QUALIFIED,HOT)&select=id,stage,score,tags&limit=50") or []
    if not isinstance(all_leads, list): return 0

    enrolled = 0
    for c in all_leads:
        tags = c.get("tags",[]) or []
        # Check if in active sequence
        seq = supa("GET","outreach_sequences","",
            f"?contact_id=eq.{c['id']}&status=eq.active&select=id&limit=1")
        if seq: continue

        # Enroll in 7-email close sequence
        campaign = supa("GET","outreach_campaigns","","?status=eq.active&limit=1&select=id") or []
        cid = (campaign[0] if isinstance(campaign,list) and campaign else {}).get("id")

        supa("POST","outreach_sequences",{
            "campaign_id":cid,"contact_id":c["id"],
            "sequence_name":"7-Email Autonomous Close Sequence",
            "current_step":0,"total_steps":7,"status":"active","channel":"email",
            "next_touch_at":now.isoformat(),
            "notes":"Zero-Sean 14-day close sequence with Stripe link in every email"
        })
        enrolled += 1

    log.info(f"Email sequences: {enrolled} leads enrolled in 7-email close")
    return enrolled

# LAYER 5: REFERRAL LOOP COMPLETION ───────────────────────
def complete_referral_loop():
    """Check referrals converted → auto-issue rewards."""
    # Find referred contacts that converted
    ref_logs = supa("GET","referral_requests_log","","?reward_issued=eq.false&select=*&limit=10") or []
    if not isinstance(ref_logs, list): return 0

    rewarded = 0
    for ref in ref_logs:
        contact_id = ref.get("contact_id")
        if not contact_id: continue

        # Check if referred contact converted
        converted = supa("GET","contacts","",
            f"?stage=eq.CLOSED_WON&referred_by=eq.{contact_id}&select=id&limit=1")
        if not converted: continue

        referrer = supa("GET","contacts","",f"?id=eq.{contact_id}&select=name,email&limit=1")
        if not referrer: continue
        r = (referrer[0] if isinstance(referrer,list) else referrer)

        # Issue reward notification
        push_notify("🎉 Referral Converted!",
            f"{r.get('name')} referred a client who just paid!\n"
            f"Issue their reward: check referral_rewards table for tier amount.",
            priority=0)

        supa("PATCH","referral_requests_log",
            {"reward_issued":True,"response":"referred"},f"?id=eq.{ref['id']}")
        rewarded += 1

    log.info(f"Referral rewards: {rewarded} rewards issued")
    return rewarded

# LAYER 6: DEAD LEAD MINING ───────────────────────────────
def mine_dead_leads():
    """Already handled by master_sales_agent reactivation — check status."""
    reactivation = supa("GET","outreach_sequences","",
        "?sequence_name=eq.6-Month Closed-Lost Reactivation&status=eq.active&select=id") or []
    active_count = len(reactivation) if isinstance(reactivation, list) else 0
    log.info(f"Dead lead mining: {active_count} closed-lost contacts in 6-month reactivation sequences")
    return active_count

# ── DEAL ROUTING ──────────────────────────────────────────
def route_deals_by_value():
    """Final routing: <$3K auto-close, $3K+ alert Sean for light touch."""
    high_value = supa("GET","appointments","",
        "?deal_value=gte.3000&status=eq.pending&select=*&limit=5") or []
    if not isinstance(high_value, list): return

    for appt in high_value:
        contact = supa("GET","contacts","",f"?id=eq.{appt.get('contact_id','')}&select=name,company&limit=1")
        if not contact: continue
        c = (contact[0] if isinstance(contact,list) else contact)
        dv = appt.get("deal_value",0)

        push_notify(f"💰 Deal Ready: ${dv:,.0f}",
            f"{c.get('name')} at {c.get('company','?')}\n"
            f"Pre-qualified. Pre-sold by AI. Your 5 min: record a Loom.\n"
            f"Everything else handled automatically.",
            priority=0)

    log.info(f"Deal routing: {len(high_value)} high-value deals surfaced to Sean")

# ── MAIN ──────────────────────────────────────────────────
def run():
    log.info("=" * 55)
    log.info("ZERO-SEAN AUTONOMOUS CLOSE — 6 Layers Active")
    log.info("Sub-$3K: fully autonomous. $3K+: pre-sold before Sean sees it.")
    log.info("=" * 55)

    results = {}
    for fn, name in [
        (route_to_self_serve, "self_serve"),
        (process_chat_leads, "chatbot"),
        (queue_voice_calls, "voice"),
        (manage_email_sequences, "email_seq"),
        (complete_referral_loop, "referrals"),
        (mine_dead_leads, "dead_leads"),
    ]:
        try: results[name] = fn()
        except Exception as e: log.error(f"{name}: {e}"); results[name] = 0

    route_deals_by_value()
    log.info(f"Zero-Sean cycle: {json.dumps(results)}")
    supa("POST","agent_run_logs",{"org_id":"sales_corp","agent_name":"zero_sean_autonomous_close",
        "run_type":"autonomous_cycle","status":"success","metrics":results})

if __name__ == "__main__": run()
