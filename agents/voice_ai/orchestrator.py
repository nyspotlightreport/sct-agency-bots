#!/usr/bin/env python3
"""
agents/voice_ai/orchestrator.py — ProFlow Voice AI Orchestrator
The central brain. Connects STT → LLM → TTS in a low-latency pipeline.
Manages concurrent calls, routing, fallbacks, and session state.
"""
import os,sys,json,logging,time,asyncio,hashlib,threading
from datetime import datetime
from typing import Dict,List,Optional,Any
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("voice_orchestrator")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [VOICE-AI] %(message)s")
import urllib.request as urlreq,urllib.parse

# ═══ PROVIDER CREDENTIALS ═══
ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
ELEVEN_KEY=os.environ.get("ELEVENLABS_API_KEY","")
OPENAI_KEY=os.environ.get("OPENAI_API_KEY","")
DEEPGRAM_KEY=os.environ.get("DEEPGRAM_API_KEY","")
TWILIO_SID=os.environ.get("TWILIO_ACCOUNT_SID","")
TWILIO_TOKEN=os.environ.get("TWILIO_AUTH_TOKEN","")
TWILIO_PHONE=os.environ.get("TWILIO_PHONE_NUMBER","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")

# ═══ PROVIDER CONFIGS ═══
STT_PROVIDERS = {
    "deepgram": {"url":"https://api.deepgram.com/v1/listen","key_env":"DEEPGRAM_API_KEY","latency":"~300ms","languages":29},
    "openai_whisper": {"url":"https://api.openai.com/v1/audio/transcriptions","key_env":"OPENAI_API_KEY","latency":"~800ms","languages":57},
}
TTS_PROVIDERS = {
    "elevenlabs": {"url":"https://api.elevenlabs.io/v1/text-to-speech","key_env":"ELEVENLABS_API_KEY",
        "latency":"~400ms","voices":{"male_pro":"21m00Tcm4TlvDq8ikWAM","female_warm":"EXAVITQu4vr4xnSDxMaL",
        "male_narrator":"VR6AewLTigWG4xSOukaG","female_recep":"ThT5KcBeYPX3keUQqHPh"},"quality":"best"},
    "openai_tts": {"url":"https://api.openai.com/v1/audio/speech","key_env":"OPENAI_API_KEY",
        "latency":"~500ms","voices":{"alloy":"alloy","echo":"echo","fable":"fable","onyx":"onyx","nova":"nova","shimmer":"shimmer"},"quality":"high"},
}
LLM_PROVIDERS = {
    "claude": {"url":"https://api.anthropic.com/v1/messages","key_env":"ANTHROPIC_API_KEY","model":"claude-sonnet-4-20250514","latency":"~600ms"},
    "openai": {"url":"https://api.openai.com/v1/chat/completions","key_env":"OPENAI_API_KEY","model":"gpt-4o","latency":"~700ms"},
}
SUPPORTED_LANGUAGES = ["en","es","fr","de","it","pt","nl","pl","ru","ja","ko","zh","ar","hi","tr","sv","da","no","fi","cs","ro","hu","el","he","th","vi","id","ms","uk"]

# ═══ CORE API FUNCTIONS ═══
def _api_call(url, data, headers, timeout=30):
    """Universal API caller with error handling."""
    body = json.dumps(data).encode() if isinstance(data, dict) else data
    req = urlreq.Request(url, data=body, headers=headers)
    try:
        start = time.time()
        with urlreq.urlopen(req, timeout=timeout) as r:
            result = r.read()
            latency = int((time.time()-start)*1000)
            return result, latency, None
    except Exception as e:
        return None, 0, str(e)[:200]

def transcribe_audio(audio_bytes, language="en", provider="deepgram"):
    """STT: Convert audio to text. Deepgram primary, Whisper fallback."""
    if provider == "deepgram" and DEEPGRAM_KEY:
        result, latency, err = _api_call(
            f"https://api.deepgram.com/v1/listen?model=nova-2&language={language}&smart_format=true",
            audio_bytes,
            {"Authorization":f"Token {DEEPGRAM_KEY}","Content-Type":"audio/wav"})
        if result:
            data = json.loads(result)
            text = data.get("results",{}).get("channels",[{}])[0].get("alternatives",[{}])[0].get("transcript","")
            log.info(f"  STT[deepgram]: '{text[:60]}...' ({latency}ms)")
            return {"text":text,"confidence":data.get("results",{}).get("channels",[{}])[0].get("alternatives",[{}])[0].get("confidence",0),"latency_ms":latency,"provider":"deepgram"}
    # Fallback to Whisper
    if OPENAI_KEY:
        import io
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
        body += audio_bytes + f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-1\r\n--{boundary}--\r\n".encode()
        result, latency, err = _api_call("https://api.openai.com/v1/audio/transcriptions", body,
            {"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":f"multipart/form-data; boundary={boundary}"})
        if result:
            text = json.loads(result).get("text","")
            return {"text":text,"confidence":0.95,"latency_ms":latency,"provider":"whisper"}
    return {"text":"","confidence":0,"latency_ms":0,"provider":"none","error":"No STT provider available"}

def synthesize_speech(text, voice_id=None, provider="elevenlabs", language="en"):
    """TTS: Convert text to audio. ElevenLabs primary, OpenAI fallback."""
    if provider == "elevenlabs" and ELEVEN_KEY:
        vid = voice_id or "21m00Tcm4TlvDq8ikWAM"
        data = {"text":text,"model_id":"eleven_multilingual_v2" if language != "en" else "eleven_monolingual_v1",
            "voice_settings":{"stability":0.71,"similarity_boost":0.80,"style":0.35,"use_speaker_boost":True}}
        result, latency, err = _api_call(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",data,
            {"Content-Type":"application/json","xi-api-key":ELEVEN_KEY})
        if result:
            log.info(f"  TTS[eleven]: {len(result)} bytes ({latency}ms)")
            return {"audio":result,"latency_ms":latency,"provider":"elevenlabs","format":"mp3"}
    if OPENAI_KEY:
        voice = voice_id if voice_id in ("alloy","echo","fable","onyx","nova","shimmer") else "nova"
        data = {"model":"tts-1-hd","input":text,"voice":voice,"response_format":"mp3"}
        result, latency, err = _api_call("https://api.openai.com/v1/audio/speech",data,
            {"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"})
        if result:
            log.info(f"  TTS[openai]: {len(result)} bytes ({latency}ms)")
            return {"audio":result,"latency_ms":latency,"provider":"openai_tts","format":"mp3"}
    return {"audio":None,"latency_ms":0,"provider":"none","error":"No TTS provider"}

def think(system_prompt, conversation, max_tokens=300, provider="claude"):
    """LLM: Generate intelligent response. Claude primary, GPT-4o fallback."""
    if provider == "claude" and ANTHROPIC:
        data = {"model":"claude-sonnet-4-20250514","max_tokens":max_tokens,"system":system_prompt,"messages":conversation}
        result, latency, err = _api_call("https://api.anthropic.com/v1/messages",data,
            {"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
        if result:
            text = json.loads(result)["content"][0]["text"]
            log.info(f"  LLM[claude]: '{text[:60]}...' ({latency}ms)")
            return {"text":text,"latency_ms":latency,"provider":"claude"}
    if OPENAI_KEY:
        msgs = [{"role":"system","content":system_prompt}] + conversation
        data = {"model":"gpt-4o","max_tokens":max_tokens,"messages":msgs}
        result, latency, err = _api_call("https://api.openai.com/v1/chat/completions",data,
            {"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"})
        if result:
            text = json.loads(result)["choices"][0]["message"]["content"]
            return {"text":text,"latency_ms":latency,"provider":"openai"}
    return {"text":"I'd be happy to help you with that.","latency_ms":0,"provider":"fallback"}

# ═══ VOICE CLONING ═══
def clone_voice(audio_bytes, voice_name, description="Custom cloned voice"):
    """Clone a voice from 30+ seconds of audio. Returns voice_id for future use."""
    if not ELEVEN_KEY: return {"error":"No ElevenLabs key","voice_id":None}
    boundary = "----ProFlowVoiceClone"
    body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\n{voice_name}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{description}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"voice_sample.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    body += audio_bytes + f"\r\n--{boundary}--\r\n".encode()
    result, latency, err = _api_call("https://api.elevenlabs.io/v1/voices/add", body,
        {"xi-api-key":ELEVEN_KEY,"Content-Type":f"multipart/form-data; boundary={boundary}"}, timeout=60)
    if result:
        data = json.loads(result)
        log.info(f"  VOICE CLONED: {voice_name} → {data.get('voice_id','?')} ({latency}ms)")
        return {"voice_id":data.get("voice_id"),"name":voice_name,"latency_ms":latency}
    return {"error":err,"voice_id":None}

def list_voices():
    """List all available voices including cloned ones."""
    if not ELEVEN_KEY: return []
    result, _, _ = _api_call("https://api.elevenlabs.io/v1/voices", None,
        {"xi-api-key":ELEVEN_KEY,"Accept":"application/json"})
    if result:
        return [{"id":v["voice_id"],"name":v["name"],"category":v.get("category",""),"labels":v.get("labels",{})}
            for v in json.loads(result).get("voices",[])]
    return []

# ═══ CRM INTEGRATION ═══
def log_call(call_data):
    """Log call to Supabase CRM with full transcript and analysis."""
    if not SUPA_URL: return
    record = {
        "director": "ProFlow Voice AI",
        "output_type": "voice_call",
        "content": json.dumps({
            "call_id": call_data.get("call_id",""),
            "direction": call_data.get("direction","inbound"),
            "phone": call_data.get("phone",""),
            "duration_sec": call_data.get("duration_sec",0),
            "transcript": call_data.get("transcript","")[:3000],
            "outcome": call_data.get("outcome",""),
            "agent_type": call_data.get("agent_type","general"),
            "sentiment": call_data.get("sentiment","neutral"),
            "language": call_data.get("language","en"),
            "total_latency_ms": call_data.get("total_latency_ms",0),
        })[:4000],
        "metrics": json.dumps({
            "stt_latency": call_data.get("stt_latency",0),
            "llm_latency": call_data.get("llm_latency",0),
            "tts_latency": call_data.get("tts_latency",0),
            "total_latency": call_data.get("total_latency_ms",0),
            "turns": call_data.get("turns",0),
        }),
        "created_at": datetime.utcnow().isoformat()
    }
    try:
        req = urlreq.Request(f"{SUPA_URL}/rest/v1/director_outputs", data=json.dumps(record).encode(), method="POST",
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=minimal"})
        urlreq.urlopen(req, timeout=10)
    except Exception:  # noqa: bare-except

        pass
def push(t,m,p=0):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000],"priority":p}).encode(),timeout=5)
    except Exception:  # noqa: bare-except

        pass
from agents.voice_ai.agent_prompts import AGENT_PROMPTS

# ═══ FULL CONVERSATION PIPELINE ═══
class VoiceSession:
    """Manages a single voice conversation with full STT→LLM→TTS pipeline."""
    def __init__(self, agent_type="general", language="en", voice_id=None, caller_info=None):
        self.session_id = hashlib.md5(f"{time.time()}{agent_type}".encode()).hexdigest()[:12]
        self.agent_type = agent_type
        self.language = language
        self.voice_id = voice_id
        self.caller_info = caller_info or {}
        self.conversation = []
        self.transcript = []
        self.turn_count = 0
        self.start_time = time.time()
        self.total_latency = 0
        self.system_prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["general"])
        log.info(f"  SESSION {self.session_id}: {agent_type} agent, lang={language}")

    def process_turn(self, user_audio=None, user_text=None):
        """Process one conversation turn: STT → LLM → TTS."""
        turn_start = time.time()
        stt_lat = 0; llm_lat = 0; tts_lat = 0
        # Step 1: STT (if audio provided)
        if user_audio:
            stt = transcribe_audio(user_audio, self.language)
            user_text = stt["text"]
            stt_lat = stt["latency_ms"]
        if not user_text: return {"error":"No input"}
        self.conversation.append({"role":"user","content":user_text})
        self.transcript.append({"speaker":"user","text":user_text,"timestamp":time.time()-self.start_time})
        # Step 2: LLM thinking
        llm = think(self.system_prompt, self.conversation)
        response_text = llm["text"]
        llm_lat = llm["latency_ms"]
        self.conversation.append({"role":"assistant","content":response_text})
        self.transcript.append({"speaker":"agent","text":response_text,"timestamp":time.time()-self.start_time})
        # Step 3: TTS
        tts = synthesize_speech(response_text, self.voice_id, language=self.language)
        tts_lat = tts["latency_ms"]
        total = int((time.time()-turn_start)*1000)
        self.total_latency += total
        self.turn_count += 1
        log.info(f"  TURN {self.turn_count}: STT={stt_lat}ms LLM={llm_lat}ms TTS={tts_lat}ms TOTAL={total}ms")
        return {
            "response_text": response_text, "audio": tts.get("audio"),
            "stt_ms": stt_lat, "llm_ms": llm_lat, "tts_ms": tts_lat, "total_ms": total,
            "turn": self.turn_count, "user_said": user_text
        }

    def end_session(self):
        """End session, log to CRM, analyze call quality."""
        duration = int(time.time()-self.start_time)
        full_transcript = "\n".join(f"{t['speaker']}: {t['text']}" for t in self.transcript)
        # Analyze call outcome with Claude
        outcome = "completed"
        if self.turn_count > 0:
            analysis = think("You analyze sales calls. Given this transcript, reply with ONE word: 'booked' if meeting was scheduled, 'interested' if prospect showed interest, 'declined' if they said no, 'completed' otherwise.",
                [{"role":"user","content":f"Transcript:\n{full_transcript[:2000]}"}], max_tokens=10)
            outcome = analysis.get("text","completed").strip().lower()
        call_data = {"call_id":self.session_id,"direction":"outbound","agent_type":self.agent_type,
            "duration_sec":duration,"transcript":full_transcript,"outcome":outcome,
            "language":self.language,"total_latency_ms":self.total_latency,"turns":self.turn_count,
            "stt_latency":0,"llm_latency":0,"tts_latency":0}
        log_call(call_data)
        push(f"Voice AI | {self.agent_type}",f"{outcome} | {self.turn_count} turns | {duration}s | {self.caller_info.get('name','Unknown')}",-1)
        log.info(f"  SESSION END: {self.session_id} | {outcome} | {self.turn_count} turns | {duration}s")
        return {"session_id":self.session_id,"outcome":outcome,"turns":self.turn_count,"duration":duration}
