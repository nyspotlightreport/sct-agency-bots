#!/usr/bin/env python3
"""
agents/media_production/video_agent.py — Video Production Specialist
Handles: short-form, long-form, product videos, cinematic scenes.
Multi-provider: Runway Gen-3 Alpha, Kling 2.5, Luma Dream Machine.
Storyboarding via Claude, camera control, character consistency.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("video_agent")

CAMERA_MOVES = {
    "push_in": "Slow dolly push toward subject, shallow depth of field",
    "pull_out": "Camera pulls back to reveal wider scene",
    "pan_left": "Smooth horizontal pan left across scene",
    "pan_right": "Smooth horizontal pan right across scene",
    "crane_up": "Crane shot rising upward revealing landscape",
    "crane_down": "Crane shot descending toward subject",
    "orbit": "Camera orbits around subject 180 degrees",
    "static": "Locked tripod, no movement, studio style",
    "handheld": "Subtle handheld movement for documentary feel",
    "tracking": "Camera tracks alongside moving subject",
}

VIDEO_STYLES = {
    "cinematic": "Film-grade visuals, anamorphic lens flare, color graded, 24fps, shallow DOF",
    "documentary": "Natural lighting, handheld camera, authentic feel, 30fps",
    "commercial": "Clean, bright, product-focused, studio lighting, 4K crisp",
    "social_short": "Vertical 9:16, punchy cuts, text overlays, high energy",
    "explainer": "Clean motion graphics, icons, animated text, corporate colors",
    "testimonial": "Medium shot, warm lighting, eye-level, natural background",
    "product_demo": "Macro details, smooth transitions, white/dark background, hero angles",
}

def create_storyboard(topic, duration_sec=60, style="cinematic", scenes=6):
    """Generate a professional storyboard with scene descriptions, camera moves, and timing."""
    from agents.media_production.director import claude
    prompt = f"""Create a {scenes}-scene storyboard for a {duration_sec}-second {style} video about: {topic}

For each scene provide:
- SCENE #: Title (duration in seconds)
- VISUAL: Detailed description of what we see (lighting, composition, colors, subjects)
- CAMERA: Camera movement from this list: {', '.join(CAMERA_MOVES.keys())}
- AUDIO: What we hear (narration text, music mood, sound effects)
- TEXT OVERLAY: Any on-screen text
- TRANSITION: How we move to next scene (cut, dissolve, wipe, zoom)

Make it commercially compelling. Think Super Bowl ad quality."""
    return claude("You are a Hollywood storyboard artist and commercial director.", prompt, 1500)

def generate_scene(scene_description, camera_move="push_in", style="cinematic"):
    """Generate a single video scene using best available provider."""
    from agents.media_production.director import generate_video_from_text
    camera = CAMERA_MOVES.get(camera_move, CAMERA_MOVES["push_in"])
    full_prompt = f"{scene_description}. Camera: {camera}. Style: {VIDEO_STYLES.get(style, VIDEO_STYLES['cinematic'])}"
    return generate_video_from_text(full_prompt, 5, style)

def produce_short_form(topic, platform="tiktok", duration_sec=30):
    """Complete short-form video production: storyboard → scenes → voiceover → assembly."""
    log.info(f"SHORT-FORM: {topic} for {platform} ({duration_sec}s)")
    storyboard = create_storyboard(topic, duration_sec, "social_short", 4)
    from agents.media_production.director import write_video_script, generate_voice
    script = write_video_script(topic, duration_sec, "punchy")
    voice = generate_voice(script[:300] if script else topic, "energetic", f"short_{platform}")
    return {"storyboard":storyboard,"script":script,"voice":voice,"platform":platform,"duration":duration_sec}

def produce_product_video(product_name, features, price, url, duration_sec=30):
    """Product demo video: hero shots → feature highlights → CTA."""
    from agents.media_production.director import generate_product_shots, generate_voice, write_ad_script
    log.info(f"PRODUCT VIDEO: {product_name}")
    script = write_ad_script(product_name, price, features[0] if features else "", url, duration_sec)
    shots = generate_product_shots(url, 3)
    voice = generate_voice(script[:400] if script else product_name, "sales_male", f"product_{product_name[:10]}")
    return {"product":product_name,"script":script,"shots":shots,"voice":voice,"url":url}
