#!/usr/bin/env python3
"""
bots/content_qa_gate_bot.py
Autonomous content publishing with guardrails.
80%+ of content auto-publishes. Edge cases go to Sean via Pushover.
Score 5/5 = publish now. Score 4/5 = publish in 2hrs. Score ≤3/5 = queue for review.
"""
import os, json, logging, datetime, urllib.request, urllib.error, re
log = logging.getLogger("content_qa")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONTENT QA] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
now       = datetime.datetime.utcnow()

# Content that should never auto-publish
BLOCKLIST = ["lawsuit","legal action","sued","bankrupt","scandal","fired",
             "racist","offensive","political","lawsuit","leaked","hacked"]
CTA_PHRASES = ["nyspotlightreport.com","store/","webinar","proflow","dfy","learn more",
               "get started","book a call","schedule","link in bio","comment below"]

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

def qa_score_content(content: str, content_type: str) -> dict:
    """Score content on 5 criteria. Returns score dict."""
    content_lower = content.lower()

    # Criterion 1: No sensitive topics
    no_sensitive = not any(kw in content_lower for kw in BLOCKLIST)

    # Criterion 2: Appropriate length
    word_count = len(content.split())
    if content_type in ["tweet","twitter"]:
        length_ok = 10 <= word_count <= 60
    elif content_type in ["linkedin"]:
        length_ok = 30 <= word_count <= 400
    elif content_type in ["blog","wordpress"]:
        length_ok = word_count >= 200
    else:
        length_ok = word_count >= 20

    # Criterion 3: CTA present
    has_cta = any(cta in content_lower for cta in CTA_PHRASES)

    # Criterion 4: Not empty/placeholder
    no_placeholders = not any(p in content for p in ["[INSERT","[TODO","PLACEHOLDER","[YOUR","[NAME]"])

    # Criterion 5: AI brand voice check (simplified — check for key signals)
    has_value = any(v in content_lower for v in
                   ["automat","ai","workflow","system","business","revenue","agency",
                    "proflow","nysr","save time","scale","growth"])

    criteria = {
        "no_sensitive_topics": no_sensitive,
        "appropriate_length": length_ok,
        "cta_present": has_cta,
        "no_placeholders": no_placeholders,
        "relevant_value": has_value
    }
    score = sum(1 for v in criteria.values() if v)
    return {"score": score, "criteria": criteria, "max_score": 5}

def process_content_queue():
    """Process pending content in QA queue."""
    queue = supa("GET","content_qa_queue","","?status=eq.pending&select=*&limit=20") or []
    auto_approved = 0; queued = 0; vetoed = 0

    for item in (queue if isinstance(queue,list) else []):
        content   = item.get("content","")
        c_type    = item.get("content_type","general")
        item_id   = item.get("id","")

        qa = qa_score_content(content, c_type)
        score = qa["score"]

        # Update QA score
        supa("PATCH","content_qa_queue",{
            "qa_score":score,"qa_criteria":qa["criteria"]
        },f"?id=eq.{item_id}")

        if score == 5:
            # Auto-publish immediately
            supa("PATCH","content_qa_queue",{
                "status":"approved","published_at":now.isoformat()
            },f"?id=eq.{item_id}")
            # Log analytics event
            supa("POST","analytics_events",{
                "event_name":"content_published","event_category":"content",
                "properties":json.dumps({"type":c_type,"score":score,"method":"auto"})
            })
            auto_approved += 1

        elif score == 4:
            # Publish after 2-hour delay — Sean can veto via Pushover
            auto_at = (now + datetime.timedelta(hours=2)).isoformat()
            supa("PATCH","content_qa_queue",{
                "status":"pending","auto_approve_at":auto_at
            },f"?id=eq.{item_id}")

            if PUSH_API and PUSH_USER and not item.get("pushover_sent"):
                preview = content[:150].replace("\n"," ")
                msg = f"Content ready [{c_type}] Score:{score}/5\n{preview}...\nAuto-publishes in 2hrs. Reply VETO to block."
                data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
                    "title":"⚡ Content auto-publishing in 2hrs","message":msg,"priority":0}).encode()
                req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                    data=data, headers={"Content-Type":"application/json"})
                try:
                    urllib.request.urlopen(req, timeout=10)
                    supa("PATCH","content_qa_queue",{"pushover_sent":True},f"?id=eq.{item_id}")
                except Exception:  # noqa: bare-except

                    pass
            queued += 1

        else:
            # Score ≤ 3 — queue for manual review
            supa("PATCH","content_qa_queue",{"status":"needs_review"},f"?id=eq.{item_id}")
            if PUSH_API and PUSH_USER:
                failed = [k for k,v in qa["criteria"].items() if not v]
                msg = f"Content needs review [{c_type}] Score:{score}/5\nFailed: {', '.join(failed)}\n{content[:100]}"
                data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
                    "title":"📝 Content needs review","message":msg,"priority":0}).encode()
                req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                    data=data, headers={"Content-Type":"application/json"})
                try: urllib.request.urlopen(req, timeout=10)
                except Exception:  # noqa: bare-except

                    pass
            vetoed += 1

    # Process auto-approve timeouts
    overdue = supa("GET","content_qa_queue","",
        f"?status=eq.pending&auto_approve_at=lt.{now.isoformat()}&select=*&limit=10") or []
    for item in (overdue if isinstance(overdue,list) else []):
        supa("PATCH","content_qa_queue",{
            "status":"approved","published_at":now.isoformat()
        },f"?id=eq.{item['id']}")
        auto_approved += 1

    log.info(f"Content QA: {auto_approved} auto-approved | {queued} queued (2hr) | {vetoed} needs review")
    return {"auto_approved":auto_approved,"queued":queued,"needs_review":vetoed}

if __name__ == "__main__": process_content_queue()
