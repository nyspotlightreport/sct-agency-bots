#!/usr/bin/env python3
"""
agents/proflow_voice_engine.py — ProFlow AI Voice Production
REAL BACKEND: Generates professional voice audio using ElevenLabs API.
Produces: podcast narrations, sales calls, ad reads, receptionist greetings.
Delivers MP3 files ready for deployment.
"""
import os,sys,json,logging,base64
from datetime import datetime
sys.path.insert(0,".")
log=logging.getLogger("voice_engine")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [VOICE] %(message)s")
import urllib.request as urlreq,urllib.parse

ELEVEN_KEY=os.environ.get("ELEVENLABS_API_KEY","")
ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
OUTPUT_DIR=os.path.join(os.path.dirname(__file__),"..","data","voice_output")
os.makedirs(OUTPUT_DIR,exist_ok=True)

VOICES = {
    "male_professional": "21m00Tcm4TlvDq8ikWAM",  # ElevenLabs "Rachel" default
    "female_warm": "EXAVITQu4vr4xnSDxMaL",
    "male_narrator": "VR6AewLTigWG4xSOukaG",
    "female_receptionist": "ThT5KcBeYPX3keUQqHPh",
}

def claude(prompt, max_tokens=500):
    if not ANTHROPIC: return ""
    try:
        data = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":max_tokens,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req = urlreq.Request("https://api.anthropic.com/v1/messages", data=data,
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
        with urlreq.urlopen(req, timeout=30) as r: return json.loads(r.read())["content"][0]["text"]
    except: return ""

def generate_voice(text, voice_id=None, output_name="output"):
    """Generate real MP3 audio using ElevenLabs API."""
    if not ELEVEN_KEY:
        log.warning("No ELEVENLABS_API_KEY — using text-only mode")
        return None
    vid = voice_id or VOICES.get("male_professional")
    try:
        data = json.dumps({"text": text, "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}}).encode()
        req = urlreq.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
            data=data, headers={"Content-Type":"application/json","xi-api-key":ELEVEN_KEY})
        with urlreq.urlopen(req, timeout=60) as r:
            audio = r.read()
            path = os.path.join(OUTPUT_DIR, f"{output_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.mp3")
            with open(path, "wb") as f: f.write(audio)
            log.info(f"  Generated: {path} ({len(audio)} bytes)")
            return path
    except Exception as e:
        log.error(f"  ElevenLabs error: {e}")
        return None

def generate_podcast_script(topic, duration_min=3):
    """Use Claude to write a professional podcast script."""
    prompt = f"""Write a {duration_min}-minute podcast script about: {topic}
    Rules: Natural conversational tone. Include intro hook, 3 key points, and outro with CTA.
    No stage directions. Just the spoken words. Sound like a real podcast host, not a chatbot.
    Sign off as 'your host at NY Spotlight Report.'"""
    return claude(prompt, 1000)

def generate_sales_script(prospect_name, company, pain_point):
    """Write a natural outbound sales call script."""
    prompt = f"""Write a natural phone sales script. Caller: Michael from ProFlow.
    Prospect: {prospect_name} at {company}. Pain point: {pain_point}.
    Rules: 4 exchanges max. Sound human — use contractions, natural pauses.
    Open with specific observation about their company. End with meeting booked.
    Format: Just the AI lines (not the prospect responses)."""
    return claude(prompt, 500)

def generate_receptionist_greeting(business_name, services):
    """Write a warm, professional receptionist greeting."""
    prompt = f"""Write an AI receptionist phone greeting for {business_name}.
    Services offered: {services}. Rules: Warm, professional, 3 sentences max.
    Offer to help, list 2-3 options, sound like a real person."""
    return claude(prompt, 200)

def generate_ad_read(product, price, benefit, duration_sec=30):
    """Write a radio/podcast ad script."""
    prompt = f"""Write a {duration_sec}-second radio ad for {product}.
    Price: {price}. Key benefit: {benefit}.
    Rules: Hook in first 3 seconds. Problem-solution-CTA format.
    End with website URL: nyspotlightreport.com. Sound energetic but not cheesy."""
    return claude(prompt, 300)

def run():
    log.info("="*60)
    log.info("PROFLOW VOICE ENGINE — Production Media Department")
    log.info("="*60)
    results = []
    # 1. Podcast episode
    log.info("\n[1/4] Generating podcast script...")
    pod_script = generate_podcast_script("3 content strategies that generated $50K in pipeline")
    if pod_script:
        log.info(f"  Script: {len(pod_script)} chars")
        audio = generate_voice(pod_script[:500], VOICES.get("male_narrator"), "podcast_ep")
        results.append({"type":"podcast","script_len":len(pod_script),"audio":bool(audio)})
    # 2. Sales call script
    log.info("\n[2/4] Generating sales call script...")
    sales = generate_sales_script("Sarah","Acme Agency","blog hasn't been updated in 3 months")
    if sales:
        log.info(f"  Script: {len(sales)} chars")
        audio = generate_voice(sales[:400], VOICES.get("male_professional"), "sales_call")
        results.append({"type":"sales","script_len":len(sales),"audio":bool(audio)})
    # 3. Receptionist greeting
    log.info("\n[3/4] Generating receptionist greeting...")
    greeting = generate_receptionist_greeting("ProFlow","content automation, AI marketing, agency tools")
    if greeting:
        log.info(f"  Greeting: {len(greeting)} chars")
        audio = generate_voice(greeting, VOICES.get("female_receptionist"), "receptionist")
        results.append({"type":"receptionist","script_len":len(greeting),"audio":bool(audio)})
    # 4. Ad read
    log.info("\n[4/4] Generating ad narration...")
    ad = generate_ad_read("ProFlow AI","$97/month","publish daily content on autopilot",30)
    if ad:
        log.info(f"  Ad: {len(ad)} chars")
        audio = generate_voice(ad, VOICES.get("male_narrator"), "ad_read")
        results.append({"type":"ad","script_len":len(ad),"audio":bool(audio)})
    log.info(f"\nProduced {len(results)} media assets")
    return results

if __name__=="__main__":
    run()
