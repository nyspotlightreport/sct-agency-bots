#!/usr/bin/env python3
"""
agents/voice_ai/director.py — Voice AI Daily Health Check Director
Orchestrates daily health checks for the ProFlow Voice AI platform.
Tests voice synthesis, checks Twilio webhook status, logs results to Supabase.
"""
import os, sys, json, logging, time
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
log = logging.getLogger("voice_ai_director")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [VOICE-DIRECTOR] %(message)s")
import urllib.request as urlreq, urllib.parse

# ═══ CREDENTIALS ═══
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
SUPA_URL = os.environ.get("SUPABASE_URL", "")
SUPA_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
WEBHOOK_URL = os.environ.get("VOICE_WEBHOOK_URL", "https://nyspotlightreport.com/.netlify/functions/voice-ai")


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


# ═══ HEALTH CHECK: ELEVENLABS VOICE SYNTHESIS ═══
def check_voice_synthesis():
    """Test ElevenLabs voice synthesis with a short sample."""
    if not ELEVEN_KEY:
        log.warning("  SKIP voice synthesis check — no ELEVENLABS_API_KEY")
        return {"status": "skipped", "reason": "no_api_key"}
    test_text = "ProFlow Voice AI health check. All systems nominal."
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default male voice
    data = {
        "text": test_text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.71, "similarity_boost": 0.80}
    }
    result, latency, err = _api(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data,
        {"Content-Type": "application/json", "xi-api-key": ELEVEN_KEY}
    )
    if result and len(result) > 0:
        log.info(f"  VOICE SYNTHESIS: OK — {len(result)} bytes, {latency}ms")
        return {"status": "ok", "bytes": len(result), "latency_ms": latency, "provider": "elevenlabs"}
    log.error(f"  VOICE SYNTHESIS: FAILED — {err}")
    return {"status": "error", "error": err, "latency_ms": latency}


def check_voice_list():
    """Verify ElevenLabs voice library is accessible."""
    if not ELEVEN_KEY:
        log.warning("  SKIP voice list check — no ELEVENLABS_API_KEY")
        return {"status": "skipped", "reason": "no_api_key", "count": 0}
    result, latency, err = _api(
        "https://api.elevenlabs.io/v1/voices", None,
        {"xi-api-key": ELEVEN_KEY, "Accept": "application/json"}
    )
    if result:
        voices = json.loads(result).get("voices", [])
        log.info(f"  VOICE LIBRARY: {len(voices)} voices available ({latency}ms)")
        return {"status": "ok", "count": len(voices), "latency_ms": latency}
    log.error(f"  VOICE LIBRARY: FAILED — {err}")
    return {"status": "error", "error": err, "count": 0}


# ═══ HEALTH CHECK: TWILIO WEBHOOK ═══
def check_twilio_webhook():
    """Verify Twilio webhook endpoint is reachable."""
    try:
        req = urlreq.Request(WEBHOOK_URL, method="GET")
        start = time.time()
        with urlreq.urlopen(req, timeout=10) as r:
            latency = int((time.time() - start) * 1000)
            status = r.getcode()
            log.info(f"  WEBHOOK: {WEBHOOK_URL} — HTTP {status} ({latency}ms)")
            return {"status": "ok", "http_code": status, "latency_ms": latency, "url": WEBHOOK_URL}
    except Exception as e:
        log.error(f"  WEBHOOK: {WEBHOOK_URL} — FAILED ({e})")
        return {"status": "error", "error": str(e)[:200], "url": WEBHOOK_URL}


# ═══ HEALTH CHECK: TWILIO ACCOUNT ═══
def check_twilio_account():
    """Verify Twilio account SID and auth token are valid."""
    if not TWILIO_SID:
        log.warning("  SKIP Twilio account check — no TWILIO_ACCOUNT_SID")
        return {"status": "skipped", "reason": "no_credentials"}
    import base64
    auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}.json"
    req = urlreq.Request(url, method="GET",
                         headers={"Authorization": f"Basic {auth}"})
    try:
        start = time.time()
        with urlreq.urlopen(req, timeout=10) as r:
            latency = int((time.time() - start) * 1000)
            data = json.loads(r.read())
            status = data.get("status", "unknown")
            log.info(f"  TWILIO ACCOUNT: {status} ({latency}ms)")
            return {"status": "ok", "account_status": status, "latency_ms": latency}
    except Exception as e:
        log.error(f"  TWILIO ACCOUNT: FAILED — {e}")
        return {"status": "error", "error": str(e)[:200]}


# ═══ HEALTH CHECK: ACTIVE CALLS ═══
def check_active_calls():
    """Check for any currently active Twilio calls."""
    if not TWILIO_SID:
        return {"status": "skipped", "reason": "no_credentials", "active": 0}
    import base64
    auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Calls.json?Status=in-progress"
    req = urlreq.Request(url, method="GET",
                         headers={"Authorization": f"Basic {auth}"})
    try:
        with urlreq.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            count = len(data.get("calls", []))
            log.info(f"  ACTIVE CALLS: {count}")
            return {"status": "ok", "active": count}
    except Exception as e:
        return {"status": "error", "error": str(e)[:200], "active": 0}


# ═══ ORCHESTRATOR IMPORT CHECK ═══
def check_orchestrator():
    """Verify orchestrator module loads and core classes are available."""
    try:
        from agents.voice_ai.orchestrator import VoiceSession, list_voices, think
        log.info("  ORCHESTRATOR: module imports OK")
        return {"status": "ok", "classes": ["VoiceSession", "list_voices", "think"]}
    except Exception as e:
        log.error(f"  ORCHESTRATOR: import FAILED — {e}")
        return {"status": "error", "error": str(e)[:200]}


# ═══ TELEPHONY IMPORT CHECK ═══
def check_telephony():
    """Verify telephony module loads and functions are available."""
    try:
        from agents.voice_ai.telephony import (
            twilio_api, make_outbound_call, generate_twiml_greeting,
            get_active_calls as _get_active, get_call_recording
        )
        log.info("  TELEPHONY: module imports OK")
        return {"status": "ok", "functions": [
            "twilio_api", "make_outbound_call", "generate_twiml_greeting",
            "get_active_calls", "get_call_recording"
        ]}
    except Exception as e:
        log.error(f"  TELEPHONY: import FAILED — {e}")
        return {"status": "error", "error": str(e)[:200]}


# ═══ RUN: DAILY HEALTH CHECK ═══
def run():
    """Orchestrate the daily Voice AI health check."""
    log.info("=" * 60)
    log.info("VOICE AI DEPARTMENT — Daily Health Check")
    log.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    log.info("=" * 60)

    results = {}
    errors = []

    # Provider status
    log.info("\n[1/7] Checking provider credentials...")
    creds = {
        "elevenlabs": bool(ELEVEN_KEY),
        "twilio": bool(TWILIO_SID),
        "supabase": bool(SUPA_URL),
        "pushover": bool(PUSH_API),
    }
    log.info(f"  ElevenLabs={'YES' if creds['elevenlabs'] else 'NO'}")
    log.info(f"  Twilio={'YES' if creds['twilio'] else 'NO'}")
    log.info(f"  Supabase={'YES' if creds['supabase'] else 'NO'}")
    log.info(f"  Pushover={'YES' if creds['pushover'] else 'NO'}")
    results["credentials"] = creds

    # Module imports
    log.info("\n[2/7] Verifying orchestrator module...")
    results["orchestrator"] = check_orchestrator()
    if results["orchestrator"]["status"] == "error":
        errors.append("orchestrator import failed")

    log.info("\n[3/7] Verifying telephony module...")
    results["telephony"] = check_telephony()
    if results["telephony"]["status"] == "error":
        errors.append("telephony import failed")

    # Voice synthesis test
    log.info("\n[4/7] Testing voice synthesis...")
    results["voice_synthesis"] = check_voice_synthesis()
    if results["voice_synthesis"]["status"] == "error":
        errors.append("voice synthesis failed")

    # Voice library
    log.info("\n[5/7] Checking voice library...")
    results["voice_library"] = check_voice_list()

    # Twilio checks
    log.info("\n[6/7] Checking Twilio account & webhook...")
    results["twilio_account"] = check_twilio_account()
    results["twilio_webhook"] = check_twilio_webhook()
    results["active_calls"] = check_active_calls()
    if results["twilio_account"].get("status") == "error":
        errors.append("twilio account check failed")

    # Summary
    log.info("\n[7/7] Compiling results...")
    passed = sum(1 for v in results.values()
                 if isinstance(v, dict) and v.get("status") == "ok")
    skipped = sum(1 for v in results.values()
                  if isinstance(v, dict) and v.get("status") == "skipped")
    failed = sum(1 for v in results.values()
                 if isinstance(v, dict) and v.get("status") == "error")
    total = passed + skipped + failed

    status = "healthy" if failed == 0 else "degraded"
    summary = f"{passed}/{total} passed, {skipped} skipped, {failed} failed"

    log.info(f"\n{'=' * 60}")
    log.info(f"VOICE AI HEALTH: {status.upper()} — {summary}")
    if errors:
        for e in errors:
            log.error(f"  ISSUE: {e}")
    log.info(f"{'=' * 60}")

    # Log to Supabase
    supa_log({
        "director": "Voice AI Director",
        "output_type": "daily_health_check",
        "content": json.dumps({
            "status": status,
            "summary": summary,
            "checks": {k: v.get("status", "unknown") if isinstance(v, dict) else str(v)
                       for k, v in results.items()},
            "errors": errors,
        })[:4000],
        "created_at": datetime.utcnow().isoformat()
    })

    # Notify
    priority = 0 if failed == 0 else 1
    push(
        f"Voice AI | {status.upper()}",
        f"{summary}\n" + ("\n".join(f"- {e}" for e in errors) if errors else "All systems nominal"),
        priority
    )

    return {"status": status, "summary": summary, "results": results, "errors": errors}


if __name__ == "__main__":
    run()
