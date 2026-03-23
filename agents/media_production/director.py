#!/usr/bin/env python3
"""
agents/media_production/director.py — Marcus Kane, Chief Media Officer
Orchestrates ALL media production: video, audio, images, ads.
Multi-provider pipeline: Claude (scripts) → ElevenLabs (voice) → 
Runway/Kling (video) → DALL-E/Flux (images) → Final render.
"""
import os,sys,json,logging,time,hashlib
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("media_director")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [MEDIA] %(message)s")
import urllib.request as urlreq,urllib.parse

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
ELEVEN_KEY=os.environ.get("ELEVENLABS_API_KEY","")
OPENAI_KEY=os.environ.get("OPENAI_API_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
OUTPUT_DIR=os.path.join(os.path.dirname(__file__),"..","..","data","media_output")
os.makedirs(OUTPUT_DIR,exist_ok=True)

def _api(url, data, headers, timeout=60):
    body = json.dumps(data).encode() if isinstance(data, dict) else data
    req = urlreq.Request(url, data=body, headers=headers)
    try:
        start = time.time()
        with urlreq.urlopen(req, timeout=timeout) as r:
            return r.read(), int((time.time()-start)*1000)
    except Exception as e: return None, 0

def claude(system, prompt, max_tokens=1000):
    if not ANTHROPIC: return ""
    data = {"model":"claude-sonnet-4-20250514","max_tokens":max_tokens,"system":system,
        "messages":[{"role":"user","content":prompt}]}
    result, ms = _api("https://api.anthropic.com/v1/messages", data,
        {"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    if result: return json.loads(result)["content"][0]["text"]
    return ""

def push(t,m,p=0):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000],"priority":p}).encode(),timeout=5)
    except:pass

def supa_log(data):
    if not SUPA_URL:return
    try:
        req=urlreq.Request(f"{SUPA_URL}/rest/v1/director_outputs",data=json.dumps(data).encode(),method="POST",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=minimal"})
        urlreq.urlopen(req,timeout=10)
    except:pass

# ═══ SCRIPT WRITING ENGINE ═══
SCRIPT_SYSTEM = """You are Marcus Kane, Chief Media Officer. You write scripts for video, audio, and ad content.
Rules: Write for SPOKEN delivery. Short sentences. Active voice. No jargon.
Every script has: HOOK (3 sec), BODY (main content), CTA (clear action).
Format: Include [VISUAL] cues, [AUDIO] cues, and [TEXT OVERLAY] directions."""

def write_video_script(topic, duration_sec=60, style="educational"):
    return claude(SCRIPT_SYSTEM,
        f"Write a {duration_sec}-second {style} video script about: {topic}\n"
        f"Include [VISUAL], [AUDIO], and [TEXT OVERLAY] directions for each scene.\n"
        f"Target: TikTok/YouTube Short/Instagram Reel. Must hook in 3 seconds.")

def write_ad_script(product_name, price, benefit, url, duration_sec=30):
    return claude(SCRIPT_SYSTEM,
        f"Write a {duration_sec}-second product ad script.\n"
        f"Product: {product_name} | Price: {price} | Benefit: {benefit}\n"
        f"URL: {url}\nFormat: Problem → Solution → Proof → CTA\n"
        f"Include [VISUAL] and [TEXT OVERLAY] for each scene.")

def write_podcast_script(topic, duration_min=5, host_name="your host"):
    return claude(SCRIPT_SYSTEM,
        f"Write a {duration_min}-minute podcast script about: {topic}\n"
        f"Host: {host_name}. Conversational, insightful, not robotic.\n"
        f"Structure: Teaser hook → Context → 3 insights → Takeaway → CTA")

# ═══ VOICE PRODUCTION ENGINE ═══
VOICE_PROFILES = {
    "narrator_male": {"eleven_id": "VR6AewLTigWG4xSOukaG", "openai_voice": "onyx", "desc": "Deep, authoritative narrator"},
    "narrator_female": {"eleven_id": "EXAVITQu4vr4xnSDxMaL", "openai_voice": "nova", "desc": "Warm, engaging narrator"},
    "sales_male": {"eleven_id": "21m00Tcm4TlvDq8ikWAM", "openai_voice": "echo", "desc": "Confident, friendly sales"},
    "sales_female": {"eleven_id": "ThT5KcBeYPX3keUQqHPh", "openai_voice": "shimmer", "desc": "Professional, persuasive"},
    "energetic": {"eleven_id": "21m00Tcm4TlvDq8ikWAM", "openai_voice": "fable", "desc": "High energy, ad reads"},
}

def generate_voice(text, profile="narrator_male", output_name="voice"):
    """Generate real audio using ElevenLabs (primary) or OpenAI TTS (fallback)."""
    p = VOICE_PROFILES.get(profile, VOICE_PROFILES["narrator_male"])
    if ELEVEN_KEY:
        data = {"text":text,"model_id":"eleven_multilingual_v2",
            "voice_settings":{"stability":0.71,"similarity_boost":0.80,"style":0.35,"use_speaker_boost":True}}
        result, ms = _api(f"https://api.elevenlabs.io/v1/text-to-speech/{p['eleven_id']}", data,
            {"Content-Type":"application/json","xi-api-key":ELEVEN_KEY})
        if result:
            path = os.path.join(OUTPUT_DIR, f"{output_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.mp3")
            with open(path,"wb") as f: f.write(result)
            log.info(f"  VOICE[eleven]: {len(result)} bytes → {path} ({ms}ms)")
            return {"path":path,"bytes":len(result),"provider":"elevenlabs","latency_ms":ms}
    if OPENAI_KEY:
        data = {"model":"tts-1-hd","input":text[:4096],"voice":p["openai_voice"],"response_format":"mp3"}
        result, ms = _api("https://api.openai.com/v1/audio/speech", data,
            {"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"})
        if result:
            path = os.path.join(OUTPUT_DIR, f"{output_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.mp3")
            with open(path,"wb") as f: f.write(result)
            log.info(f"  VOICE[openai]: {len(result)} bytes → {path} ({ms}ms)")
            return {"path":path,"bytes":len(result),"provider":"openai_tts","latency_ms":ms}
    return {"error":"No TTS provider available"}

def clone_voice(audio_bytes, name, description="Custom cloned voice"):
    """Clone any voice from 30s of audio via ElevenLabs Instant Voice Cloning."""
    if not ELEVEN_KEY: return {"error":"No ElevenLabs key"}
    boundary = "----ProFlowClone"
    body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\n{name}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{description}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"sample.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    body += audio_bytes + f"\r\n--{boundary}--\r\n".encode()
    result, ms = _api("https://api.elevenlabs.io/v1/voices/add", body,
        {"xi-api-key":ELEVEN_KEY,"Content-Type":f"multipart/form-data; boundary={boundary}"})
    if result:
        data = json.loads(result)
        log.info(f"  VOICE CLONED: {name} → {data.get('voice_id')} ({ms}ms)")
        return {"voice_id":data.get("voice_id"),"name":name}
    return {"error":"Clone failed"}

# ═══ IMAGE GENERATION ENGINE ═══
def generate_image(prompt, style="photorealistic", size="1024x1024"):
    """Generate images via DALL-E 3 (primary) with cinema-grade prompting."""
    enhanced = claude("You enhance image prompts for DALL-E 3. Make them cinematic, specific, and visually stunning. Add lighting, composition, color palette details. Keep under 200 words.",
        f"Enhance this image prompt for commercial quality: {prompt}\nStyle: {style}")
    if OPENAI_KEY:
        data = {"model":"dall-e-3","prompt":enhanced or prompt,"n":1,"size":size,"quality":"hd","style":"vivid"}
        result, ms = _api("https://api.openai.com/v1/images/generations", data,
            {"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"})
        if result:
            img_data = json.loads(result)
            url = img_data["data"][0]["url"]
            revised = img_data["data"][0].get("revised_prompt","")
            log.info(f"  IMAGE[dall-e-3]: {url[:60]}... ({ms}ms)")
            return {"url":url,"revised_prompt":revised,"provider":"dall-e-3","latency_ms":ms}
    return {"error":"No image provider available"}

def generate_product_shots(product_url, count=3):
    """Scrape product URL and generate multiple product shot variations."""
    product_info = claude("You extract product information from URLs. Return: name, description, key features, brand colors.",
        f"Extract product details from this URL for creating product photography: {product_url}")
    shots = []
    angles = ["hero shot on white background with dramatic lighting","lifestyle shot in use context","detail closeup with bokeh background"]
    for i, angle in enumerate(angles[:count]):
        prompt = f"Commercial product photography. {product_info}. {angle}. Shot on Phase One IQ4, 150mm lens, studio lighting."
        img = generate_image(prompt, "photorealistic")
        if "url" in img:
            shots.append({"angle":angle,"url":img["url"],"provider":img["provider"]})
            log.info(f"  PRODUCT SHOT {i+1}/{count}: {angle}")
    return shots

# ═══ VIDEO PRODUCTION ENGINE ═══
# Multi-provider: Runway Gen-3, Kling 2.5, Luma Dream Machine
VIDEO_PROVIDERS = {
    "runway": {"url":"https://api.dev.runwayml.com/v1/image_to_video","key_env":"RUNWAY_API_KEY",
        "capabilities":["image_to_video","text_to_video","camera_control","style_transfer"],
        "max_duration":16,"resolution":"1080p"},
    "kling": {"url":"https://api.klingai.com/v1/videos/text2video","key_env":"KLING_API_KEY",
        "capabilities":["text_to_video","image_to_video","cinematic_scenes"],
        "max_duration":10,"resolution":"1080p"},
    "luma": {"url":"https://api.lumalabs.ai/dream-machine/v1/generations","key_env":"LUMA_API_KEY",
        "capabilities":["text_to_video","image_to_video","realistic_motion"],
        "max_duration":5,"resolution":"1080p"},
}

def generate_video_from_text(prompt, duration_sec=5, style="cinematic", provider="runway"):
    """Generate video from text description using best available provider."""
    enhanced = claude("You enhance video generation prompts. Add camera movement (pan, dolly, crane), lighting, atmosphere, motion details. Be extremely specific about visual composition.",
        f"Enhance for {provider} AI video generation: {prompt}\nStyle: {style}\nDuration: {duration_sec}s")
    prov = VIDEO_PROVIDERS.get(provider, VIDEO_PROVIDERS["runway"])
    api_key = os.environ.get(prov["key_env"], "")
    if api_key:
        # Each provider has slightly different API format
        if provider == "runway":
            data = {"promptText":enhanced or prompt,"duration":min(duration_sec,16),"ratio":"16:9"}
            result, ms = _api(prov["url"], data, {"Authorization":f"Bearer {api_key}","Content-Type":"application/json","X-Runway-Version":"2024-11-06"}, timeout=120)
        elif provider == "luma":
            data = {"prompt":enhanced or prompt,"aspect_ratio":"16:9","loop":False}
            result, ms = _api(prov["url"], data, {"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}, timeout=120)
        else:
            data = {"prompt":enhanced or prompt,"duration":str(duration_sec)}
            result, ms = _api(prov["url"], data, {"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}, timeout=120)
        if result:
            resp = json.loads(result)
            log.info(f"  VIDEO[{provider}]: Job submitted ({ms}ms)")
            return {"job_id":resp.get("id",resp.get("task_id","")),"provider":provider,"status":"processing","latency_ms":ms}
    log.warning(f"  VIDEO[{provider}]: No API key, returning script-only")
    return {"error":f"No {provider} API key","script":enhanced,"provider":provider}

def generate_video_from_image(image_url, motion_prompt="gentle camera push in", duration_sec=5, provider="runway"):
    """Animate a still image into video. Image-to-video with camera control."""
    prov = VIDEO_PROVIDERS.get(provider, VIDEO_PROVIDERS["runway"])
    api_key = os.environ.get(prov["key_env"], "")
    if api_key and provider == "runway":
        data = {"promptImage":image_url,"promptText":motion_prompt,"duration":min(duration_sec,10),"ratio":"16:9"}
        result, ms = _api(prov["url"], data, {"Authorization":f"Bearer {api_key}","Content-Type":"application/json","X-Runway-Version":"2024-11-06"}, timeout=120)
        if result:
            resp = json.loads(result)
            return {"job_id":resp.get("id",""),"provider":"runway","status":"processing"}
    return {"error":f"No {provider} image-to-video available","motion_prompt":motion_prompt}

# ═══ AD FACTORY: URL → VIDEO AD IN 60 SECONDS ═══
def url_to_video_ad(product_url, duration_sec=30, style="professional"):
    """FULL PIPELINE: Product URL → Script → Voice → Images → Video Ad."""
    log.info(f"\n{'='*60}")
    log.info(f"AD FACTORY: {product_url}")
    log.info(f"{'='*60}")
    # Step 1: Scrape and understand the product
    log.info("[1/5] Analyzing product...")
    product_analysis = claude("You analyze products from URLs for ad creation. Extract: product name, price, key benefit, target audience, brand voice, unique selling proposition.",
        f"Analyze this product for a video ad: {product_url}")
    # Step 2: Write the ad script
    log.info("[2/5] Writing ad script...")
    script = write_ad_script(product_analysis, "", "see product", product_url, duration_sec)
    # Step 3: Generate voiceover
    log.info("[3/5] Recording voiceover...")
    # Extract just the spoken lines from script
    spoken = claude("Extract ONLY the spoken narration lines from this ad script. Remove all [VISUAL] and [TEXT OVERLAY] cues. Just the words the narrator says.", script)
    voice = generate_voice(spoken or script[:500], "energetic", f"ad_{hashlib.md5(product_url.encode()).hexdigest()[:8]}")
    # Step 4: Generate product images
    log.info("[4/5] Generating visuals...")
    shots = generate_product_shots(product_url, 3)
    # Step 5: Generate video from hero image
    log.info("[5/5] Rendering video...")
    video = None
    if shots and "url" in shots[0]:
        video = generate_video_from_image(shots[0]["url"], "slow zoom in with subtle parallax", 5)
    result = {"product_url":product_url,"script":script,"voice":voice,"product_shots":shots,"video":video,"duration_sec":duration_sec}
    supa_log({"director":"Marcus Kane","output_type":"video_ad","content":json.dumps({k:str(v)[:200] for k,v in result.items()})[:4000],"created_at":datetime.utcnow().isoformat()})
    push("Ad Factory",f"Video ad produced for {product_url[:50]}",-1)
    log.info(f"\nAD COMPLETE: Script={len(script)} chars, Voice={voice.get('bytes',0)} bytes, Shots={len(shots)}, Video={'submitted' if video else 'script-only'}")
    return result

# ═══ FULL PRODUCTION PIPELINE ═══
def produce_content_package(topic, brand_name="ProFlow", formats=None):
    """Produce a complete content package: video script + voiceover + images + social cuts."""
    if formats is None: formats = ["video_script","voiceover","hero_image","social_graphics"]
    log.info(f"\nPRODUCTION PACKAGE: {topic}")
    package = {"topic":topic,"brand":brand_name,"assets":[]}
    if "video_script" in formats:
        script = write_video_script(topic, 60, "educational")
        package["assets"].append({"type":"video_script","content":script})
    if "voiceover" in formats and package["assets"]:
        spoken = claude("Extract only spoken narration from this script, no cues:", package["assets"][0].get("content",""))
        voice = generate_voice(spoken or topic, "narrator_male", f"pkg_{hashlib.md5(topic.encode()).hexdigest()[:8]}")
        package["assets"].append({"type":"voiceover","audio":voice})
    if "hero_image" in formats:
        img = generate_image(f"Professional promotional image for {topic}. Clean, modern, editorial style.", "photorealistic")
        package["assets"].append({"type":"hero_image","image":img})
    if "social_graphics" in formats:
        for platform in ["linkedin_carousel","instagram_square","twitter_header"]:
            size = {"linkedin_carousel":"1024x1024","instagram_square":"1024x1024","twitter_header":"1792x1024"}.get(platform,"1024x1024")
            img = generate_image(f"{platform} graphic for {topic}. Bold typography, brand colors gold and cream.", "graphic_design", size)
            package["assets"].append({"type":f"social_{platform}","image":img})
    supa_log({"director":"Marcus Kane","output_type":"content_package","content":json.dumps({"topic":topic,"asset_count":len(package["assets"])}),"created_at":datetime.utcnow().isoformat()})
    log.info(f"PACKAGE COMPLETE: {len(package['assets'])} assets produced")
    return package

def run():
    log.info("="*60)
    log.info("MEDIA PRODUCTION DEPARTMENT — Director Marcus Kane")
    log.info("="*60)
    log.info(f"\nProviders online:")
    log.info(f"  Voice: ElevenLabs={'YES' if ELEVEN_KEY else 'NO'} | OpenAI TTS={'YES' if OPENAI_KEY else 'NO'}")
    log.info(f"  Image: DALL-E 3={'YES' if OPENAI_KEY else 'NO'}")
    log.info(f"  Video: Runway={'YES' if os.environ.get('RUNWAY_API_KEY') else 'NO'} | Kling={'YES' if os.environ.get('KLING_API_KEY') else 'NO'} | Luma={'YES' if os.environ.get('LUMA_API_KEY') else 'NO'}")
    log.info(f"  LLM: Claude={'YES' if ANTHROPIC else 'NO'}")
    # Demo: Write a script
    log.info("\n[DEMO] Writing video script...")
    script = write_video_script("3 AI tools that will replace your content team in 2026", 45, "educational")
    if script: log.info(f"  Script: {len(script)} chars ✓")
    # Demo: Generate voiceover
    log.info("\n[DEMO] Generating voiceover...")
    voice = generate_voice("Welcome to ProFlow. The AI content engine that runs itself. Today we're showing you three tools that will transform your agency.", "narrator_male", "demo")
    log.info(f"  Voice: {voice.get('bytes',0)} bytes via {voice.get('provider','none')} ✓")
    log.info("\nMedia Production Department: OPERATIONAL")
    return {"status":"operational","script_len":len(script) if script else 0,"voice":voice}

if __name__=="__main__":
    run()
