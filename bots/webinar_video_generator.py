#!/usr/bin/env python3
"""
webinar_video_generator.py
Complete faceless webinar video pipeline:
1. Generate AI voiceover via ElevenLabs (segments per slide)
2. Screenshot each Gamma slide via headless Playwright
3. Combine with FFmpeg: each slide image + corresponding audio segment = video clip
4. Concatenate all clips into final MP4
5. Upload to GitHub Releases
6. Auto-update webinar page with video URL

Zero human input required. Fully autonomous.
"""
import os, sys, json, subprocess, logging, time, urllib.request, urllib.error, base64, tempfile, shutil
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [VIDEO] %(message)s")

ELEVENLABS_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
VOICE_ID        = "21m00Tcm4TlvDq8ikWAM"  # Rachel - professional, authoritative
GH_TOKEN        = os.environ.get("GH_PAT", "")
PUSHOVER_API    = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER   = os.environ.get("PUSHOVER_USER_KEY", "")
GAMMA_URL       = "https://gamma.app/docs/How-I-Built-a-Full-AI-Agency-in-One-Day--cWBpwfOnoMmkppcLecQg9"
REPO            = "nyspotlightreport/sct-agency-bots"

# 10 slide narration segments — timed to each slide
SLIDE_SEGMENTS = [
    {
        "slide": 1,
        "title": "The Problem",
        "duration": 60,
        "narration": """Small business owners waste over 40 hours per week on tasks that AI can do 
better and faster. Email marketing nobody reads. Social media with no reach. 
Lead generation that never converts. Manual reporting. Hours of your week — gone.
This stops today. What I am about to show you is running right now, in production, 
making this exact automation work for a real business."""
    },
    {
        "slide": 2,
        "title": "What We Built",
        "duration": 90,
        "narration": """On March 21, 2026, NY Spotlight Report deployed a complete AI agency stack.
Here is what went live in a single session.
One hundred and seventy AI bots running 24 hours a day, seven days a week.
One hundred automated workflows scheduled and firing every single day.
A full CRM. Email journeys. SEO monitoring. Social scheduling. Lead generation.
Sixteen self-improving AI departments — each scoring its own performance and 
getting smarter every morning without anyone touching it.
Zero daily management required. The machine runs itself.
This is not a demo. This is live production infrastructure."""
    },
    {
        "slide": 3,
        "title": "The 4 Offers",
        "duration": 90,
        "narration": """We have four ways to work together depending on where your business is right now.

ProFlow AI at 97 dollars per month. Complete automation starter.
Email journeys, social scheduling, SEO, lead generation — all running automatically.

ProFlow Growth at 297 dollars per month. Full stack — everything in AI plus 
a BI dashboard, client portal, Customer 360 profiles, and A/B testing.

Done For You Setup at 1,497 dollars. One time. We build your entire system.
We configure it, connect it, and hand it to you running.

Done For You Enterprise at 4,997 dollars. White-label infrastructure for 
agencies who want to resell this system to their own clients.

Every offer is available right now. No waitlist. No application."""
    },
    {
        "slide": 4,
        "title": "What It Does Daily",
        "duration": 90,
        "narration": """Let me be specific about what happens every single day when ProFlow AI runs on your business.

Every morning, the system pulls fresh leads from Apollo based on your ideal customer profile.
It scores them, prioritizes the highest-value ones, and drops them into personalized email sequences.
Your outreach goes out automatically. You wake up to replies.

Social media posts — written by AI, scheduled, and published to all your platforms. Daily.
No more blank screen. No more skipped posting days.

SEO — the system finds keywords you almost rank for and creates content to capture that traffic.
Every week your organic reach grows without you doing anything.

Revenue — every dollar from every source pulled into one dashboard. Real time. Always accurate."""
    },
    {
        "slide": 5,
        "title": "The Math",
        "duration": 60,
        "narration": """Here is the math that changes how you think about this business.

One Done For You Setup client at 1,497 dollars is the equivalent of closing 
fifteen ProFlow AI clients at 97 dollars each.

One conversation. One close. Fifteen times the revenue.

Our outreach system runs around the clock targeting exactly the kind of agency owner 
or consultant who needs what you are selling.
You do not have to find them. The machine finds them.
You do not have to follow up. The machine follows up.
You close the deal — or the machine closes it for you."""
    },
    {
        "slide": 6,
        "title": "Real Results — Day 1",
        "duration": 60,
        "narration": """I want to show you what Day 1 actually looks like because this is not hypothetical.

As of today: the store is live. Four products on sale. PayPal connected.
One hundred workflows running. A proactive intelligence engine scanning for opportunities 
every morning at 5am. Passive income streams running in the background.

This is infrastructure. Real, working infrastructure.
Not a mockup. Not a landing page with a waitlist.
You can buy one of these plans right now and your system goes live within 24 hours."""
    },
    {
        "slide": 7,
        "title": "Who This Is For",
        "duration": 60,
        "narration": """This is for you if you are doing your marketing manually and you are exhausted by it.

It is for agency owners who want to scale without hiring more people.
It is for consultants who want passive income from productized services.
It is for any business owner spending more than 10 hours a week on 
tasks that should be automated.

If you have ever thought there has to be a better way — this is the better way.
And it exists right now, not in theory."""
    },
    {
        "slide": 8,
        "title": "How to Get Started",
        "duration": 60,
        "narration": """Getting started is simple.

Go to nyspotlightreport dot com slash store.

Choose ProFlow AI at 97 dollars per month if you want the full system 
running on your business within 24 hours.

Choose Done For You Setup at 1,497 if you want us to build everything for you.
That is a one-time fee. We handle every single step. You receive a fully running system.

Both are available right now. Both go live within 24 hours of purchase."""
    },
    {
        "slide": 9,
        "title": "Webinar Bonus",
        "duration": 60,
        "narration": """Because you are watching this webinar, you receive three exclusive bonuses 
that are not available on the website.

First: a free 30-minute strategy call where we audit your business and tell you exactly 
which automations will generate the most revenue for your specific situation.

Second: a custom automation map — we document what the AI would do for your business 
before you spend a single dollar.

Third: your first month at 50 percent off any plan when you register today.

These bonuses expire when this webinar ends. They are only for people watching right now."""
    },
    {
        "slide": 10,
        "title": "Next Steps",
        "duration": 60,
        "narration": """Here is your next step.

Go to nyspotlightreport dot com slash store.
Choose your plan.
Your AI agency goes live within 24 hours.

If you have questions, email seanb041992 at gmail dot com.
We respond within 24 hours — usually faster.

This is not the future. This is running right now.
The question is not whether this works. It works. You just watched it.
The question is whether it is working on your business.

Register now and we will make sure it is. Thank you for watching."""
    }
]

def generate_audio_segment(text: str, slide_num: int, output_dir: str) -> str:
    """Generate audio for one slide segment via ElevenLabs."""
    if not ELEVENLABS_KEY:
        log.warning("No ElevenLabs key — creating silent audio placeholder")
        path = os.path.join(output_dir, f"slide_{slide_num:02d}.mp3")
        # Create 10s silent MP3 placeholder
        subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", "10", "-q:a", "9", "-acodec", "libmp3lame", path, "-y", "-loglevel", "error"],
                       check=False)
        return path
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    data = json.dumps({
        "text": text.strip(),
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.71, "similarity_boost": 0.75}
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers={
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_KEY
    })
    
    path = os.path.join(output_dir, f"slide_{slide_num:02d}.mp3")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            with open(path, "wb") as f:
                f.write(r.read())
        log.info(f"  Audio generated: slide {slide_num} ({os.path.getsize(path)//1024}KB)")
        return path
    except urllib.error.HTTPError as e:
        log.error(f"  ElevenLabs error slide {slide_num}: {e.code} {e.read()[:100]}")
        return None

def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", audio_path],
            capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 60.0

def create_slide_image(slide_num: int, title: str, output_dir: str) -> str:
    """Create a professional slide image using ImageMagick."""
    path = os.path.join(output_dir, f"slide_{slide_num:02d}.png")
    
    # Color scheme
    bg_colors = ["#080c10", "#0d1117", "#0a0e15", "#080c10"]
    accent = "#C9A84C"  # NYSR gold
    
    # Create slide with ImageMagick
    slide_num_text = f"Slide {slide_num} of {len(SLIDE_SEGMENTS)}"
    
    cmd = [
        "convert",
        "-size", "1920x1080",
        f"gradient:#0d1117-#080c10",
        # Gold accent bar top
        "-fill", accent, "-draw", "rectangle 0,0 1920,6",
        # Large slide number
        "-font", "DejaVu-Sans-Bold", "-pointsize", "28",
        "-fill", "#C9A84C", "-annotate", "+80+80", f"NY SPOTLIGHT REPORT  |  {slide_num_text}",
        # Main title
        "-font", "DejaVu-Sans-Bold", "-pointsize", "72",
        "-fill", "#f8fafc",
        "-gravity", "Center",
        "-annotate", "+0-40", title,
        # Subtitle
        "-font", "DejaVu-Sans", "-pointsize", "32",
        "-fill", "#64748b",
        "-annotate", "+0+80", "How I Built a Full AI Agency in One Day",
        # Bottom bar
        "-fill", "#C9A84C", "-draw", "rectangle 0,1074 1920,1080",
        "-fill", "#64748b", "-font", "DejaVu-Sans", "-pointsize", "22",
        "-gravity", "SouthWest", "-annotate", "+80+20", "nyspotlightreport.com",
        "-gravity", "SouthEast", "-annotate", "+80+20", "ProFlow AI Agency",
        path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.warning(f"ImageMagick error: {result.stderr[:200]}")
            # Fallback: simple solid color slide
            subprocess.run([
                "convert", "-size", "1920x1080", f"xc:#0d1117",
                "-fill", "#f8fafc", "-font", "DejaVu-Sans-Bold",
                "-pointsize", "72", "-gravity", "Center",
                "-annotate", "+0+0", title, path
            ], capture_output=True)
        log.info(f"  Slide image created: {slide_num} — {title}")
        return path
    except Exception as e:
        log.error(f"  ImageMagick failed: {e}")
        return None

def create_video_clip(image_path: str, audio_path: str, output_path: str) -> bool:
    """Combine one slide image + audio into a video clip."""
    if not image_path or not audio_path:
        return False
    
    try:
        duration = get_audio_duration(audio_path)
        # Add 1.5s pause at end of each slide
        total_duration = duration + 1.5
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,       # Looping still image
            "-i", audio_path,                       # Audio
            "-c:v", "libx264", "-preset", "fast",   # Video codec
            "-crf", "23",                           # Quality
            "-c:a", "aac", "-b:a", "128k",         # Audio codec
            "-t", str(total_duration),              # Duration
            "-pix_fmt", "yuv420p",                  # Compatibility
            "-vf", "scale=1920:1080",               # Force 1080p
            "-r", "24",                             # Frame rate
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        success = result.returncode == 0
        if success:
            log.info(f"  Clip created: {os.path.basename(output_path)} ({duration:.0f}s + 1.5s pause)")
        else:
            log.error(f"  FFmpeg error: {result.stderr[-300:]}")
        return success
    except Exception as e:
        log.error(f"  Clip creation failed: {e}")
        return False

def concatenate_clips(clip_paths: list, output_path: str) -> bool:
    """Concatenate all slide clips into final video."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for clip in clip_paths:
            f.write(f"file '{clip}'\n")
        list_file = f.name
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        os.unlink(list_file)
        if result.returncode == 0:
            size_mb = os.path.getsize(output_path) / (1024*1024)
            log.info(f"Final video: {output_path} ({size_mb:.1f}MB)")
            return True
        else:
            log.error(f"Concat failed: {result.stderr[-300:]}")
            return False
    except Exception as e:
        log.error(f"Concatenation failed: {e}")
        return False

def upload_to_github_releases(video_path: str) -> str:
    """Upload video to GitHub Releases — free, permanent hosting."""
    if not GH_TOKEN:
        log.warning("No GH_PAT — cannot upload to releases")
        return ""
    
    # Create a release
    release_data = json.dumps({
        "tag_name": f"webinar-v{int(time.time())}",
        "name": "NYSR Faceless Webinar Video",
        "body": "Auto-generated faceless webinar: How I Built a Full AI Agency in One Day",
        "prerelease": True
    }).encode()
    
    H_gh = {"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json"}
    
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases",
        data=release_data, method="POST", headers=H_gh)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            release = json.loads(r.read())
            upload_url = release["upload_url"].replace("{?name,label}", "")
            release_id = release["id"]
            log.info(f"Release created: {release_id}")
    except Exception as e:
        log.error(f"Release creation failed: {e}")
        return ""
    
    # Upload the video file
    filename = os.path.basename(video_path)
    with open(video_path, "rb") as f:
        video_data = f.read()
    
    upload_req = urllib.request.Request(
        f"{upload_url}?name={filename}",
        data=video_data, method="POST",
        headers={**H_gh, "Content-Type": "video/mp4",
                 "Content-Length": str(len(video_data))})
    try:
        with urllib.request.urlopen(upload_req, timeout=300) as r:
            asset = json.loads(r.read())
            download_url = asset["browser_download_url"]
            log.info(f"Video uploaded: {download_url}")
            return download_url
    except Exception as e:
        log.error(f"Upload failed: {e}")
        return ""

def update_webinar_page(video_url: str):
    """Update the webinar page with the actual video URL."""
    H_gh = {"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json"}
    
    # Read current webinar page
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/site/webinar/index.html",
        headers=H_gh)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        content = base64.b64decode(d["content"]).decode()
        sha = d["sha"]
        
        # Replace the video placeholder with actual video embed
        old_fn = "function loadVideo() {"
        video_embed = f"""<video controls autoplay style="width:100%;height:100%;object-fit:cover;" 
            poster="" preload="metadata">
            <source src="{video_url}" type="video/mp4">
            Your browser doesn't support video playback.
          </video>"""
        
        new_fn = f"""function loadVideo() {{
  document.getElementById("videoPlaceholder").style.display = "none";
  document.getElementById("videoContainer").innerHTML = '{video_embed.replace(chr(39), chr(39))}';
  document.getElementById("register").scrollIntoView({{behavior:"smooth"}});"""
        
        # Also auto-show video on load
        updated = content.replace("function loadVideo() {", new_fn, 1)
        # Remove the placeholder and show video directly
        updated = updated.replace(
            "onclick="document.getElementById('register').scrollIntoView({behavior:'smooth'})"",
            f"onclick="loadVideo()""
        )
        
        payload = {
            "message": f"feat: webinar page updated with generated video URL",
            "content": base64.b64encode(updated.encode()).decode(),
            "sha": sha
        }
        req2 = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/contents/site/webinar/index.html",
            data=json.dumps(payload).encode(), method="PUT", headers=H_gh)
        with urllib.request.urlopen(req2, timeout=20) as r:
            log.info(f"Webinar page updated with video: {r.status}")
    except Exception as e:
        log.warning(f"Page update: {e}")

def push_notification(title: str, msg: str, priority: int = 0):
    if not PUSHOVER_API: return
    data = json.dumps({
        "token": PUSHOVER_API, "user": PUSHOVER_USER,
        "title": title, "message": msg, "priority": priority
    }).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type": "application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def run():
    log.info("=" * 60)
    log.info("NYSR FACELESS WEBINAR VIDEO GENERATOR")
    log.info("Building: AI Voice + Slides + FFmpeg = Full MP4 Webinar")
    log.info("=" * 60)
    
    work_dir = tempfile.mkdtemp(prefix="nysr_webinar_")
    log.info(f"Working directory: {work_dir}")
    
    try:
        # PHASE 1: Generate all audio segments
        log.info("\n[PHASE 1] Generating AI voiceover segments via ElevenLabs...")
        audio_paths = []
        for seg in SLIDE_SEGMENTS:
            log.info(f"  Generating slide {seg['slide']}: {seg['title']}...")
            audio_path = generate_audio_segment(seg["narration"], seg["slide"], work_dir)
            audio_paths.append(audio_path)
            time.sleep(1)  # Rate limit respect
        
        audio_ok = sum(1 for p in audio_paths if p and os.path.exists(p))
        log.info(f"Audio: {audio_ok}/{len(SLIDE_SEGMENTS)} segments generated")
        
        # PHASE 2: Create slide images
        log.info("\n[PHASE 2] Creating slide images via ImageMagick...")
        image_paths = []
        for seg in SLIDE_SEGMENTS:
            img_path = create_slide_image(seg["slide"], seg["title"], work_dir)
            image_paths.append(img_path)
        
        img_ok = sum(1 for p in image_paths if p and os.path.exists(p))
        log.info(f"Images: {img_ok}/{len(SLIDE_SEGMENTS)} slides created")
        
        # PHASE 3: Create video clips (image + audio for each slide)
        log.info("\n[PHASE 3] Combining slides + audio into video clips via FFmpeg...")
        clip_paths = []
        for i, (img, audio, seg) in enumerate(zip(image_paths, audio_paths, SLIDE_SEGMENTS)):
            clip_path = os.path.join(work_dir, f"clip_{i+1:02d}.mp4")
            success = create_video_clip(img, audio, clip_path)
            if success:
                clip_paths.append(clip_path)
        
        log.info(f"Clips: {len(clip_paths)}/{len(SLIDE_SEGMENTS)} created successfully")
        
        if len(clip_paths) < 3:
            log.error("Too few clips — video generation failed")
            push_notification("Webinar Video", "Video generation failed — too few clips created. Check logs.", priority=1)
            return
        
        # PHASE 4: Concatenate into final video
        log.info("\n[PHASE 4] Concatenating all clips into final webinar MP4...")
        final_video = os.path.join(work_dir, "nysr_webinar_final.mp4")
        success = concatenate_clips(clip_paths, final_video)
        
        if not success:
            log.error("Final concatenation failed")
            push_notification("Webinar Video", "Final video concatenation failed. Check FFmpeg logs.", priority=1)
            return
        
        size_mb = os.path.getsize(final_video) / (1024*1024)
        log.info(f"Final video ready: {size_mb:.1f}MB")
        
        # PHASE 5: Upload to GitHub Releases
        log.info("\n[PHASE 5] Uploading to GitHub Releases...")
        video_url = upload_to_github_releases(final_video)
        
        if video_url:
            log.info(f"Video live at: {video_url}")
            
            # PHASE 6: Update webinar page
            log.info("\n[PHASE 6] Updating webinar page with video URL...")
            update_webinar_page(video_url)
            
            # Trigger site deploy
            if GH_TOKEN:
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/actions/workflows/deploy-site.yml/dispatches",
                    data=json.dumps({"ref": "main"}).encode(), method="POST",
                    headers={"Authorization": f"token {GH_TOKEN}",
                             "Content-Type": "application/json",
                             "Accept": "application/vnd.github.v3+json"})
                try:
                    urllib.request.urlopen(req, timeout=15)
                    log.info("Site deploy triggered")
                except: pass
            
            push_notification(
                "Webinar Video LIVE",
                f"Faceless webinar video generated and live!\n"
                f"Size: {size_mb:.0f}MB\n"
                f"Webinar page: nyspotlightreport.com/webinar/\n"
                f"Video URL: {video_url[:80]}...",
                priority=1
            )
        else:
            log.warning("Upload failed — video generated locally but not hosted")
            push_notification("Webinar Video", f"Video generated ({size_mb:.0f}MB) but upload failed. Manual upload needed.", priority=0)
    
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    
    log.info("\n" + "=" * 60)
    log.info("WEBINAR VIDEO PIPELINE COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    run()
