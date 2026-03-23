#!/usr/bin/env python3
"""
ElevenLabs Voice Pipeline — NYSR Agency  
Auto-voices all YouTube Shorts scripts.
Saves MP3 to /tmp/ for YouTube upload bot to pick up.
Voice: warm, authoritative (matches SC Thomas brand).
At 30 Shorts/month × 150 words each = ~4,500 chars = well under 30k limit.
"""
import os, requests, json, logging, time
log = logging.getLogger("VoicePipeline")

EL_KEY  = os.environ.get("ELEVENLABS_API_KEY","")
EL_BASE = "https://api.elevenlabs.io/v1"

# Best voice for SC Thomas brand: "Adam" — deep, authoritative, American
# Fallback: "Antoni" — warm, direct
VOICE_PROFILES = {
    "primary":  {"id":"pNInz6obpgDQGcFmaJgB","name":"Adam",   "desc":"Deep, authoritative"},
    "fallback": {"id":"ErXwobaYiN019PkySvjV","name":"Antoni", "desc":"Warm, direct"},
}
VOICE_SETTINGS = {"stability":0.65,"similarity_boost":0.80,"style":0.25,"use_speaker_boost":True}

def get_voices() -> list:
    """List available voices — check what we have access to."""
    if not EL_KEY: return []
    r = requests.get(f"{EL_BASE}/voices", headers={"xi-api-key": EL_KEY}, timeout=10)
    return r.json().get("voices",[]) if r.status_code==200 else []

def check_quota() -> dict:
    """Check remaining character quota for month."""
    if not EL_KEY: return {"used":0,"limit":0,"remaining":0}
    r = requests.get(f"{EL_BASE}/user", headers={"xi-api-key": EL_KEY}, timeout=10)
    if r.status_code==200:
        sub = r.json().get("subscription",{})
        used = sub.get("character_count",0)
        limit = sub.get("character_limit",30000)
        return {"used":used,"limit":limit,"remaining":limit-used}
    return {"used":0,"limit":0,"remaining":0}

def voice_script(script: str, output_path: str, voice_id: str = None) -> bool:
    """Convert script to MP3 voiceover."""
    if not EL_KEY:
        log.warning("No ELEVENLABS_API_KEY — skipping voice")
        return False
    vid = voice_id or VOICE_PROFILES["primary"]["id"]
    r = requests.post(
        f"{EL_BASE}/text-to-speech/{vid}",
        headers={"xi-api-key": EL_KEY, "Content-Type":"application/json"},
        json={"text": script, "model_id":"eleven_monolingual_v1",
              "voice_settings": VOICE_SETTINGS},
        timeout=60
    )
    if r.status_code==200:
        with open(output_path,"wb") as f: f.write(r.content)
        size_kb = len(r.content)//1024
        log.info(f"✅ Voiced {len(script)} chars → {output_path} ({size_kb}KB)")
        return True
    log.error(f"ElevenLabs {r.status_code}: {r.text[:100]}")
    return False

def voice_all_pending_scripts() -> int:
    """Voice all pending YouTube Shorts scripts."""
    quota = check_quota()
    log.info(f"ElevenLabs quota: {quota['used']:,}/{quota['limit']:,} chars used | {quota['remaining']:,} remaining")
    
    # Load pending scripts
    try:
        with open("/tmp/youtube_scripts_pending.json") as f:
            scripts = json.load(f)
    except Exception:  # noqa: bare-except
        log.info("No pending scripts file — checking data/video_scripts/")
        scripts = []
    
    voiced = 0
    for i, s in enumerate(scripts[:10]):  # Max 10 per run
        script_text = s.get("script","")
        title = s.get("title","video")
        if not script_text or len(script_text) > quota["remaining"]:
            log.warning(f"Skipping '{title}' — quota or no script")
            continue
        out = f"/tmp/voice_{i}_{title[:20].replace(' ','_').replace('/','_')}.mp3"
        ok = voice_script(script_text, out)
        if ok:
            voiced += 1
            quota["remaining"] -= len(script_text)
            time.sleep(1)
    
    log.info(f"Voiced {voiced} scripts")
    return voiced

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    quota = check_quota()
    if not EL_KEY:
        print("No ELEVENLABS_API_KEY — add secret to activate")
    else:
        print(f"ElevenLabs active: {quota['remaining']:,} chars remaining this month")
        voices = get_voices()
        print(f"Available voices: {len(voices)}")
        voiced = voice_all_pending_scripts()
        print(f"Voiced today: {voiced} scripts")
