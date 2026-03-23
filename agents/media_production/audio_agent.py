#!/usr/bin/env python3
"""
agents/media_production/audio_agent.py — Audio Production Specialist
Handles: Podcasts, voiceovers, ad reads, music, sound design.
Voice cloning, multilingual narration, emotional voice control.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("audio_agent")

PODCAST_FORMATS = {
    "solo": {"speakers":1,"style":"Authoritative thought leadership monologue"},
    "interview": {"speakers":2,"style":"Host asks questions, guest provides expertise"},
    "roundtable": {"speakers":3,"style":"Multiple experts discuss a topic"},
    "narrative": {"speakers":1,"style":"Story-driven, documentary style with atmosphere"},
}

MUSIC_MOODS = {
    "corporate": "Clean, uplifting, professional. Soft piano, light strings.",
    "energetic": "High tempo, driving beat, electronic. Perfect for product reveals.",
    "emotional": "Warm, heartfelt, inspiring. Acoustic guitar, gentle vocals.",
    "cinematic": "Epic, building. Orchestral swells, dramatic percussion.",
    "minimal": "Subtle background texture. Ambient pads, very low-key.",
}

def produce_podcast_episode(topic, format_type="solo", duration_min=5, host_name="Sean Thomas"):
    """Full podcast production: script → voice → music bed → master."""
    from agents.media_production.director import claude, generate_voice, write_podcast_script
    log.info(f"PODCAST: {topic} ({format_type}, {duration_min}min)")
    fmt = PODCAST_FORMATS.get(format_type, PODCAST_FORMATS["solo"])
    script = write_podcast_script(topic, duration_min, host_name)
    voice = generate_voice(script[:1000] if script else topic, "narrator_male", f"podcast_{topic[:15].replace(' ','_')}")
    return {"topic":topic,"format":format_type,"script":script,"voice":voice,"duration_min":duration_min}

def produce_ad_read(product, price, benefit, duration_sec=30, voice_profile="energetic"):
    """Radio/podcast ad read with professional voice."""
    from agents.media_production.director import claude, generate_voice
    script = claude("Write a punchy radio ad. Hook in 3 seconds. Problem→Solution→CTA. Sound natural not salesy.",
        f"Product: {product}. Price: {price}. Benefit: {benefit}. Duration: {duration_sec}s. End with nyspotlightreport.com")
    voice = generate_voice(script or f"{product} for {price}", voice_profile, f"ad_{product[:10]}")
    return {"script":script,"voice":voice,"duration_sec":duration_sec}

def produce_voiceover(text, voice_profile="narrator_male", language="en"):
    """Professional voiceover for any content."""
    from agents.media_production.director import generate_voice
    return generate_voice(text, voice_profile, f"vo_{language}_{datetime.utcnow().strftime('%H%M')}")

SUPPORTED_LANGUAGES = {
    "en":"English","es":"Spanish","fr":"French","de":"German","it":"Italian",
    "pt":"Portuguese","nl":"Dutch","pl":"Polish","ru":"Russian","ja":"Japanese",
    "ko":"Korean","zh":"Chinese","ar":"Arabic","hi":"Hindi","tr":"Turkish",
    "sv":"Swedish","da":"Danish","no":"Norwegian","fi":"Finnish","cs":"Czech",
    "ro":"Romanian","hu":"Hungarian","el":"Greek","he":"Hebrew","th":"Thai",
    "vi":"Vietnamese","id":"Indonesian","ms":"Malay","uk":"Ukrainian",
}

def produce_multilingual(text, voice_profile="narrator_female", languages=None):
    """Generate voiceover in multiple languages from a single script."""
    from agents.media_production.director import claude, generate_voice
    if languages is None: languages = ["en","es","fr","de"]
    results = {}
    for lang in languages:
        if lang != "en":
            translated = claude(f"Translate this to {SUPPORTED_LANGUAGES.get(lang,lang)}. Keep it natural, not literal:", text)
        else:
            translated = text
        voice = generate_voice(translated or text, voice_profile, f"multi_{lang}")
        results[lang] = {"text":translated,"voice":voice}
        log.info(f"  {SUPPORTED_LANGUAGES.get(lang,lang)}: {voice.get('bytes',0)} bytes")
    return results
