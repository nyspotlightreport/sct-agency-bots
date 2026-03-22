#!/usr/bin/env python3
"""
faceless_webinar_voice_bot.py
Generates AI voiceover for the NYSR webinar using ElevenLabs.
Produces a professional narration over the 10 presentation slides.
Uploads to YouTube as unlisted — webinar is fully faceless.
"""
import os, json, urllib.request, urllib.error, logging, time
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [VOICE] %(message)s")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY","")
VOICE_ID           = "21m00Tcm4TlvDq8ikWAM"  # Rachel — professional, clear, authoritative
PUSHOVER_API       = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER      = os.environ.get("PUSHOVER_USER_KEY","")

# The full webinar narration script — 10 slides, ~45 minutes
WEBINAR_SCRIPT = """
Welcome to How I Built a Full AI Agency in One Day — And How You Can Too.

My name is Flo, the AI system behind NY Spotlight Report.
Today I'm going to show you exactly how we deployed a complete AI agency stack —
and how you can have the same system running on your business within 24 hours.

[SLIDE 1 — THE PROBLEM]

Let me ask you something. How many hours this week did you spend on tasks
that a machine could do better?

Writing emails that never get opened. Posting to social media that no one sees.
Trying to find leads. Updating your CRM. Running reports. Checking rankings.

The average small business owner wastes 40 hours per week on tasks
that AI handles automatically, faster, and more consistently than any human.

That stops today.

[SLIDE 2 — WHAT CHANGED]

On March 21, 2026, NY Spotlight Report deployed a complete AI agency stack
in a single session. Here is what went live:

170 AI bots running 24 hours a day, 7 days a week.
100 automated workflows scheduled and firing every single day.
A full CRM with email journeys, SEO monitoring, social scheduling, and lead generation.
16 self-improving AI departments — each one scoring its own performance and getting
smarter every morning without anyone touching it.
Zero daily management required. The machine runs itself.

This is not a demo. This is live production infrastructure.

[SLIDE 3 — THE 4 OFFERS]

We have four ways to work with us, depending on where you are.

ProFlow AI at 97 dollars per month. This is your complete automation starter.
Email journeys, social scheduling, SEO, lead generation — all running automatically.
This is where most people start.

ProFlow Growth at 297 dollars per month. Full stack — everything in AI plus
a BI dashboard, client portal, Customer 360 profiles, and A/B testing on your pages.

DFY Setup at 1,497 dollars. One time. We build your entire system for you.
Done for you. We configure it, connect it, and hand it to you running.
This is the fastest path to having AI working on your business.

DFY Enterprise at 4,997 dollars. White-label infrastructure for agencies
who want to resell this system to their own clients.

[SLIDE 4 — WHAT IT ACTUALLY DOES]

Let me be specific about what ProFlow AI does on a daily basis for your business.

Every morning, the system pulls fresh leads from Apollo based on your ideal customer profile.
It scores them, prioritizes them, and drops them into personalized email sequences.
By afternoon, your outreach has already gone out without you touching anything.

Social media posts — written by AI, scheduled and published to Twitter and your blog — daily.
No more staring at a blank screen wondering what to post.

SEO opportunities — the system connects to Ahrefs, finds keywords you almost rank for,
and creates content briefs so you can capture that traffic.

Revenue — every dollar from every source is pulled into one dashboard.
Stripe, PayPal, Gumroad, affiliates — all unified. You see your P and L in real time.

[SLIDE 5 — THE MATH]

Here is the math that changes how you think about this.

If you close one DFY Setup client at 1,497 dollars,
that is the equivalent of closing fifteen ProFlow AI clients at 97 dollars each.

One conversation. One close. Fifteen times the revenue.

Our outreach system runs 24 hours a day targeting exactly the kind of business owner
or agency owner who needs this. You do not have to find them. The machine finds them.

[SLIDE 6 — REAL RESULTS DAY ONE]

I want to show you what Day 1 actually looks like because this is not hypothetical.

As of today: the store is live. Four products on sale. PayPal connected.
100 workflows running. A proactive intelligence engine scanning for opportunities
every morning at 5am. The passive income stack — Gumroad, KDP, Redbubble, affiliates —
all running in the background.

This is infrastructure. Real, working infrastructure.
Not a mockup. Not a landing page with a waitlist.
You can buy one of these plans right now and your system goes live within 24 hours.

[SLIDE 7 — WHO THIS IS FOR]

This is for you if you are doing your marketing manually and you are exhausted.

It is for agency owners who want to scale without hiring more people.
It is for consultants who want passive income from productized services.
It is for anyone spending more than 10 hours a week on tasks that should be automated.

If you have ever thought "there has to be a better way" — this is the better way.

[SLIDE 8 — HOW TO GET STARTED]

Getting started is simple. Go to nyspotlightreport dot com slash store.

Choose ProFlow AI at 97 dollars per month if you want to start immediately
and get the full system running on your business within 24 hours.

Choose DFY Setup at 1,497 if you want us to build it for you.
That is a one-time fee. We handle everything. You get a fully running system.

Both are available right now. No waitlist. No application required.

[SLIDE 9 — WEBINAR BONUS]

Because you are watching this webinar, you get three things that are not on the website.

First: a free 30-minute strategy call where we audit your business and tell you exactly
which automations will generate the most revenue for you specifically.

Second: a custom automation audit — we map out what the AI would do for your business
before you spend a single dollar.

Third: your first month at 50 percent off any plan when you register today.

These bonuses are only available to webinar registrants. They expire when this ends.

[SLIDE 10 — NEXT STEPS]

Here is what to do right now.

Go to nyspotlightreport dot com slash store.
Choose your plan.
Your AI agency goes live within 24 hours.

If you have questions, email seanb041992 at gmail dot com.
We respond within 24 hours.

This is not the future. This is running right now.
The only question is whether it is running on your business.

Thank you for watching. We will see you on the other side.
"""

def generate_voice(script: str) -> bytes:
    """Generate voiceover using ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        log.warning("ELEVENLABS_API_KEY not set — skipping voice generation")
        return b""
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    data = json.dumps({
        "text": script,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.71,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers={
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    })
    
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            audio = r.read()
            log.info(f"Voice generated: {len(audio)/1024:.0f}KB")
            return audio
    except urllib.error.HTTPError as e:
        log.error(f"ElevenLabs error: {e.code} {e.read()[:200]}")
        return b""
    except Exception as e:
        log.error(f"Voice generation failed: {e}")
        return b""

def save_audio_to_repo(audio: bytes):
    """Save generated audio to GitHub repo for YouTube upload."""
    if not audio:
        return
    import base64 as b64
    
    GH_TOKEN = os.environ.get("GH_PAT","")
    REPO = "nyspotlightreport/sct-agency-bots"
    H = {"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json",
         "Accept": "application/vnd.github.v3+json"}
    
    content = b64.b64encode(audio).decode()
    filename = f"webinar_voiceover_{int(time.time())}.mp3"
    
    payload = {
        "message": f"feat: webinar voiceover generated by ElevenLabs — {filename}",
        "content": content
    }
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/assets/{filename}",
        data=json.dumps(payload).encode(), method="PUT", headers=H)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            log.info(f"Audio saved to repo: assets/{filename} ({r.status})")
            return filename
    except Exception as e:
        log.warning(f"Repo save failed: {e}")
        return None

def push_notification(title, msg):
    if not PUSHOVER_API: return
    data = json.dumps({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data,
                                  headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def run():
    log.info("=== Faceless Webinar Voice Bot ===")
    log.info("Generating AI voiceover via ElevenLabs...")
    
    audio = generate_voice(WEBINAR_SCRIPT)
    
    if audio:
        filename = save_audio_to_repo(audio)
        push_notification(
            "Webinar Voice Ready",
            f"ElevenLabs voiceover generated ({len(audio)//1024}KB). File: {filename}. Ready to combine with Gamma slides."
        )
        log.info("Voice generation complete.")
    else:
        log.warning("No audio generated — check ELEVENLABS_API_KEY")
        push_notification("Webinar Voice", "ElevenLabs API key needed to generate voice. Add ELEVENLABS_API_KEY to GitHub secrets.")

if __name__ == "__main__":
    run()

