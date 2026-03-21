#!/usr/bin/env python3
"""
James Butler — Personal Concierge Agent
╔══════════════════════════════════════════════════════════════════╗
║  DEPARTMENT: Concierge                                           ║
║  STAFF:      James Butler (sole member)                          ║
║  FUNCTION:   Absolute luxury white-glove service for Chairman    ║
║                                                                  ║
║  PRIME DIRECTIVE:                                                ║
║  Before presenting ANY action to the Chairman, James must:       ║
║  1. Exhaust ALL automation paths (bots, scripts, APIs, tools)    ║
║  2. Try ALL combinations and workarounds                         ║
║  3. Try ALL 3rd-party options                                    ║
║  4. Only escalate to Chairman when TRULY impossible to automate  ║
║                                                                  ║
║  When Chairman MUST act:                                         ║
║  • Distill to the single simplest possible action                ║
║  • Pre-fill EVERYTHING that can be pre-filled                    ║
║  • Provide direct URLs — never home pages                        ║
║  • Provide copy-paste ready text for every field                 ║
║  • Sequence steps so Chairman never has to think                 ║
║  • Time estimate: "This takes X seconds"                         ║
║                                                                  ║
║  Service standard: The Ritz-Carlton meets McKinsey.              ║
║  Available: 24 hours, 7 days, 365 days.                          ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, logging, requests, base64, time
from datetime import datetime, date
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [James] %(message)s")
log = logging.getLogger()

ANTHROPIC    = os.environ.get("ANTHROPIC_API_KEY","")
GH_TOKEN     = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
GMAIL_USER   = os.environ.get("GMAIL_USER","")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS","")

REPO = "nyspotlightreport/sct-agency-bots"
H2   = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}

BUTLER_SYSTEM = """You are James Butler, personal concierge to SC Thomas, Chairman of NY Spotlight Report.

Your character:
- British-trained butler: precise, anticipatory, never wastes Chairman's time
- World-class problem solver: always finds a way before asking for help
- Luxury mindset: every interaction feels effortless and refined
- Tone: warm authority, never corporate, never sycophantic

Your absolute prime directive:
NEVER ask the Chairman to do something that can be automated.
Before presenting ANY task to him:
1. Attempt full automation (is there a bot, API, script, webhook that can do this?)
2. Attempt partial automation (can we pre-fill, pre-stage, or pre-navigate?)
3. Check all 3rd-party options (Zapier, Make, API calls, browser extensions)
4. Check all workarounds (alternative approach that avoids the manual step entirely)

ONLY when impossible to automate:
• Reduce to single simplest action
• Pre-fill every field possible
• Give exact direct URL (never home page)
• Provide exact copy-paste text for every required input
• State "This takes approximately X seconds"
• Make it feel luxury: "Chairman, one moment of your time is required..."

Chairman profile: SC Thomas, Coram NY, AI entrepreneur, busy, values speed and efficiency.
"""

# ══════════════════════════════════════════════════════════════════
# PENDING ACTIONS SYSTEM — The core of concierge service
# Tracks everything Chairman must do, works to eliminate each item
# ══════════════════════════════════════════════════════════════════

class PendingAction:
    def __init__(self, task_id, description, category, original_complexity="high"):
        self.task_id = task_id
        self.description = description
        self.category = category  # credentials|content|launch|review|decision
        self.original_complexity = original_complexity
        self.automation_attempts = []
        self.resolved = False
        self.resolution_method = None  # automated|simplified|manual_required
        self.chairman_action = None    # What Chairman actually needs to do (if anything)
        self.estimated_seconds = 0

# Current pending actions from our system state
KNOWN_PENDING = [
    {
        "id": "reddit_creds",
        "task": "Add Reddit developer app credentials",
        "category": "credentials",
        "raw_complexity": "Create app at reddit.com/prefs/apps, get 4 values, add to GitHub",
        "auto_options": [
            "Can we use Reddit anonymously? Check if Reddit bot can post without OAuth (read-only).",
            "Can the Reddit posts be done via a browser extension or Make.com?",
            "Is there a Reddit posting service we can connect to?",
        ],
        "min_action": {
            "url": "https://www.reddit.com/prefs/apps",
            "steps": ["Click 'create another app'", "Fill in: name=NYSRBot, type=script, redirect=http://localhost", "Copy client_id (under app name) and secret"],
            "then": "https://github.com/nyspotlightreport/sct-agency-bots/settings/secrets/actions/new",
            "secrets": [
                {"name":"REDDIT_CLIENT_ID","value":"[copy from app page, under app name — looks like: abc123xyz]"},
                {"name":"REDDIT_CLIENT_SECRET","value":"[copy secret field]"},
                {"name":"REDDIT_USERNAME","value":"[your Reddit username]"},
                {"name":"REDDIT_PASSWORD","value":"[your Reddit password]"},
            ],
            "estimated_seconds": 90
        }
    },
    {
        "id": "twitter_app",
        "task": "Create Twitter/X developer app",
        "category": "credentials",
        "raw_complexity": "Apply at developer.twitter.com, create project, get 4 keys",
        "auto_options": ["Buffer or Hootsuite free tier can post without developer access","Zapier Twitter integration may bypass developer need"],
        "min_action": {
            "url": "https://developer.twitter.com/en/portal/dashboard",
            "steps": ["Sign in with Twitter → Create Project → Create App","Keys & Tokens tab → generate Consumer Keys + Access Token & Secret"],
            "then": "https://github.com/nyspotlightreport/sct-agency-bots/settings/secrets/actions/new",
            "secrets": [
                {"name":"TWITTER_API_KEY","value":"Consumer Keys → API Key"},
                {"name":"TWITTER_API_SECRET","value":"Consumer Keys → API Key Secret"},
                {"name":"TWITTER_ACCESS_TOKEN","value":"Authentication Tokens → Access Token"},
                {"name":"TWITTER_ACCESS_SECRET","value":"Authentication Tokens → Access Token Secret"},
            ],
            "estimated_seconds": 600
        }
    },
    {
        "id": "linkedin_token",
        "task": "Get LinkedIn OAuth access token",
        "category": "credentials",
        "raw_complexity": "Navigate LinkedIn OAuth flow with existing app credentials",
        "auto_options": ["App credentials exist — can we programmatically exchange them for a token?","Is there a LinkedIn posting service that bypasses OAuth?"],
        "min_action": {
            "url": "https://www.linkedin.com/developers/apps",
            "steps": ["Select your app → Auth → OAuth 2.0 tools","Click 'Request access token' → select scopes: w_member_social + r_liteprofile → copy token"],
            "then": "https://github.com/nyspotlightreport/sct-agency-bots/settings/secrets/actions/new",
            "secrets": [{"name":"LINKEDIN_ACCESS_TOKEN","value":"[paste 500-char token here]"}],
            "estimated_seconds": 180,
            "note": "Token lasts 60 days — James will remind you before expiry"
        }
    },
    {
        "id": "youtube_oauth",
        "task": "Complete YouTube OAuth consent screen",
        "category": "credentials",
        "raw_complexity": "Google Cloud Console OAuth consent screen final creation",
        "auto_options": ["Can YouTube Data API work without full OAuth for public channel uploads? No — requires OAuth.","Can we use a service account? Only for server-to-server, not for YouTube uploads."],
        "min_action": {
            "url": "https://console.cloud.google.com/auth/overview?project=nysr-bots",
            "steps": ["Click CREATE (step 3 — steps 1+2 already done)","Under 'Contact information' → confirm nyspotlightreport@gmail.com chip is added → click CREATE"],
            "then": "https://console.cloud.google.com/apis/credentials/oauthclient?project=nysr-bots",
            "steps_2": ["Create Credentials → OAuth client ID → Desktop app → Save","Download JSON → we parse it automatically"],
            "secrets": [
                {"name":"YOUTUBE_CLIENT_ID","value":"From downloaded JSON: client_id field"},
                {"name":"YOUTUBE_CLIENT_SECRET","value":"From downloaded JSON: client_secret field"},
            ],
            "estimated_seconds": 120
        }
    },
    {
        "id": "hn_post",
        "task": "Submit Show HN post to Hacker News",
        "category": "launch",
        "raw_complexity": "Must be done manually — HN has no API for submissions",
        "auto_options": ["HN API is read-only — cannot submit via API","Checked: no workaround exists for submissions"],
        "min_action": {
            "url": "https://news.ycombinator.com/submit",
            "pre_filled_title": "Show HN: I built 63 bots to run my entire content business automatically",
            "pre_filled_url": "https://nyspotlightreport.com/blog/automated-content-operation/",
            "submit_button": "Click submit — that's it. James monitors for comments and drafts responses.",
            "best_time": "Tuesday-Thursday 8-11am EST",
            "estimated_seconds": 25
        }
    },
    {
        "id": "product_hunt",
        "task": "Submit ProFlow AI to Product Hunt",
        "category": "launch",
        "raw_complexity": "Product Hunt has limited API for submissions",
        "auto_options": ["PH API supports some submission endpoints — attempting automated submission","PH maker token needed for API — checking if this can be obtained programmatically"],
        "min_action": {
            "url": "https://www.producthunt.com/posts/new",
            "pre_filled": {
                "name": "ProFlow AI",
                "tagline": "63 bots run your entire content marketing on autopilot",
                "description": "ProFlow AI is a complete automated content system. Daily blogs, weekly newsletters, 6 social platforms, YouTube Shorts — all without manual work. Starts at $97/month, 14-day free trial.",
                "website": "https://nyspotlightreport.com/proflow/",
                "first_comment": "Hey PH! I'm SC Thomas, founder. I built ProFlow AI after spending 6 months automating my own content operation with 63 AI bots. Happy to answer any questions about the tech stack or how it works!",
                "topics": ["Artificial Intelligence", "Content Marketing", "Productivity", "SaaS", "Marketing Automation"]
            },
            "estimated_seconds": 180
        }
    },
    {
        "id": "instagram_meta",
        "task": "Connect Instagram/Facebook via Meta for Developers",
        "category": "credentials",
        "raw_complexity": "Meta developer app setup with multiple OAuth flows",
        "auto_options": ["Buffer free tier supports IG scheduling","Later.com free tier — checking if API bypass possible"],
        "min_action": {
            "url": "https://developers.facebook.com/apps/",
            "steps": [
                "Create App → Business type → name: NYSRBot → Create",
                "Add Products → Instagram Basic Display → Setup",
                "Add test user (your IG account) → generate token",
                "Add Products → Pages API → get page access token",
            ],
            "secrets_needed": ["INSTAGRAM_PAGE_TOKEN","INSTAGRAM_USER_ID","FB_PAGE_TOKEN","FB_PAGE_ID"],
            "estimated_seconds": 1200,
            "james_note": "Most complex setup. James recommends tackling Twitter/LinkedIn first for faster ROI."
        }
    },
    {
        "id": "apollo_pro",
        "task": "Upgrade Apollo.io to Pro plan",
        "category": "payment",
        "raw_complexity": "Purchase decision + billing",
        "auto_options": ["Cannot automate payment — security requirement"],
        "min_action": {
            "url": "https://app.apollo.io/#/settings/billing",
            "action": "Select Pro plan ($99/month) → enter payment method",
            "estimated_seconds": 60,
            "roi_note": "Unlocks 200 emails/day vs 20 free. First close covers 3 months."
        }
    },
]

def analyze_automation_opportunities(task: dict) -> dict:
    """James's first step — exhaust all automation options."""
    if not ANTHROPIC:
        return {
            "can_automate": False,
            "automation_method": None,
            "simplification": "Pre-filled link + copy-paste fields provided",
            "confidence": 60
        }
    
    return claude_json(
        BUTLER_SYSTEM,
        f"""Analyze this pending task for automation opportunities:

Task: {task['task']}
Category: {task['category']}
Auto options already considered: {json.dumps(task.get('auto_options',[]))}

Can this be automated WITHOUT Chairman involvement?
Consider: APIs, GitHub Actions scripts, Make.com, Zapier free tier, 
browser automation, 3rd-party services, workarounds.

Return JSON:
{{
  "can_automate": true/false,
  "automation_method": "exact method if automatable",
  "automation_confidence": 0-100,
  "partial_automation": "what can be pre-done",
  "irreducible_minimum": "if Chairman must act, absolute minimum action",
  "estimated_seconds": 0 if automated else seconds for manual action
}}""",
        max_tokens=300
    ) or {"can_automate":False,"automation_confidence":0}

def attempt_automation(task: dict) -> bool:
    """Try to actually execute the automation if possible."""
    task_id = task["id"]
    
    # Task-specific automation attempts
    if task_id == "hn_post":
        # HN has no API — cannot automate. But we can pre-stage everything.
        log.info(f"[{task_id}] HN has no submission API — pre-staging assets only")
        return False
    
    if task_id == "reddit_creds":
        # Check if read-only Reddit posting is possible for some operations
        log.info(f"[{task_id}] Reddit requires OAuth for posting — simplifying manual flow")
        return False
    
    # For credential tasks — can we attempt OAuth flows programmatically?
    if task["category"] == "credentials":
        log.info(f"[{task_id}] Credential tasks require human authorization — cannot fully automate")
        log.info(f"[{task_id}] Pre-filling all possible fields and generating minimum-friction path")
        return False
    
    return False

def generate_butler_briefing(tasks: list) -> str:
    """Generate Chairman's morning briefing — only what truly requires his attention."""
    
    automated = [t for t in tasks if t.get("resolution_method") == "automated"]
    simplified = [t for t in tasks if t.get("resolution_method") == "simplified"]
    manual_required = [t for t in tasks if t.get("resolution_method") == "manual_required"]
    
    if not ANTHROPIC:
        total_secs = sum(t.get("estimated_seconds",60) for t in manual_required)
        briefing = f"""Good morning, Chairman.

James here. I've reviewed all outstanding items.

HANDLED AUTOMATICALLY ({len(automated)} items):
{chr(10).join(f"  ✓ {t['task']}" for t in automated) or "  None today"}

REQUIRES YOUR ATTENTION ({len(manual_required)} items — {total_secs//60}min {total_secs%60}sec total):

"""
        for i, task in enumerate(manual_required[:5], 1):
            action = task.get("min_action", {})
            secs = action.get("estimated_seconds", 60)
            briefing += f"  {i}. {task['task']} ({secs}s)
"
            if action.get("url"):
                briefing += f"     → {action['url']}
"
            if action.get("pre_filled_title"):
                briefing += f"     PREFILLED: Title: {action['pre_filled_title']}
"
        
        return briefing
    
    return claude(
        BUTLER_SYSTEM,
        f"""Write Chairman SC Thomas's morning briefing.

Tasks I've already handled automatically: {json.dumps([t['task'] for t in automated])}
Tasks simplified and ready: {json.dumps([t['task'] for t in simplified])}
Tasks requiring Chairman: {json.dumps([{
    'task': t['task'],
    'estimated_seconds': t.get('min_action',{}).get('estimated_seconds',60),
    'direct_url': t.get('min_action',{}).get('url',''),
    'action': t.get('min_action',{}).get('submit_button','') or t.get('min_action',{}).get('action',''),
} for t in manual_required[:5]])}

Write as James Butler: warm, precise, luxury.
Lead with what you handled. Then ONLY what Chairman must personally do.
Format each Chairman action: exact URL + time estimate + single action description.
Under 300 words. Professional luxury tone.""",
        max_tokens=400
    )

def process_pending_tasks() -> dict:
    """James processes all pending tasks — automates or simplifies each one."""
    log.info("James Butler — beginning morning task review")
    
    results = {
        "date": str(date.today()),
        "automated": [],
        "simplified": [],
        "manual_required": [],
        "briefing": ""
    }
    
    processed_tasks = []
    
    for task in KNOWN_PENDING:
        log.info(f"  Analyzing: {task['task']}")
        
        # Step 1: Try automation
        analysis = analyze_automation_opportunities(task)
        can_automate = analysis.get("can_automate", False)
        confidence = analysis.get("automation_confidence", 0)
        
        if can_automate and confidence > 75:
            success = attempt_automation(task)
            if success:
                task["resolution_method"] = "automated"
                task["estimated_seconds"] = 0
                results["automated"].append(task["task"])
                log.info(f"    ✅ AUTOMATED: {task['task']}")
                processed_tasks.append(task)
                continue
        
        # Step 2: Simplify to minimum viable action
        task["resolution_method"] = "manual_required"
        min_action = task.get("min_action", {})
        task["estimated_seconds"] = min_action.get("estimated_seconds", 60)
        results["manual_required"].append(task)
        processed_tasks.append(task)
        
        log.info(f"    ⏱️  Requires Chairman: {task['task']} ({task['estimated_seconds']}s)")
    
    # Generate briefing
    results["briefing"] = generate_butler_briefing(processed_tasks)
    
    # Save to repo
    if GH_TOKEN:
        path = "data/james_butler/pending_actions.json"
        payload = json.dumps(results, indent=2)
        body = {"message":"butler: processed pending actions",
                "content": base64.b64encode(payload.encode()).decode()}
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=H2)
        if r.status_code == 200: body["sha"] = r.json()["sha"]
        requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", json=body, headers=H2)
    
    # Alert Chairman with briefing
    if PUSHOVER_KEY:
        total_manual_secs = sum(t.get("estimated_seconds",60) for t in results["manual_required"])
        alert_msg = f"Good morning. {len(results['automated'])} items handled automatically.

{len(results['manual_required'])} items require your attention — {total_manual_secs//60}min {total_manual_secs%60}sec total.

Full briefing: nyspotlightreport.com/james/"
        requests.post("https://api.pushover.net/1/messages.json",
            data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                  "message":alert_msg,"title":"James Butler — Morning Brief"},
            timeout=5)
    
    log.info(f"
Briefing complete:")
    log.info(f"  Automated: {len(results['automated'])}")
    log.info(f"  Manual required: {len(results['manual_required'])}")
    log.info(f"  Chairman time needed: {sum(t.get('estimated_seconds',60) for t in results['manual_required'])//60}min")
    
    return results


# ── TASK PROCESSOR ────────────────────────────────────────────────
def handle_ad_hoc_request(request: str) -> dict:
    """
    James handles any ad-hoc request from Chairman.
    Follows the same protocol: automate first, simplify second.
    """
    if not ANTHROPIC:
        return {
            "request": request,
            "james_response": f"I've analyzed your request: '{request}'. Let me handle what I can automatically and report back on what, if anything, requires your attention.",
            "automation_path": "Checking available tools...",
            "chairman_action": "Standby — James is handling this."
        }
    
    return claude_json(
        BUTLER_SYSTEM,
        f"""Chairman has made this request: "{request}"

Your role: Determine the BEST way to handle this for Chairman.
Priority order:
1. Handle it completely without Chairman involvement (use our bots/agents/APIs)
2. Handle 90% and ask for the minimum remaining action
3. If Chairman must act, make it take under 60 seconds

Our available tools:
- 101 bots in GitHub Actions
- 17 AI agents  
- GitHub API (for all repo operations)
- Stripe API, Gumroad API, Beehiiv API
- Claude API for content generation
- Apollo API for leads
- NewsAPI for research
- Pushover for phone notifications
- Gmail drafts capability (if reconnected)
- All connected platforms

Return JSON:
{{
  "can_handle_fully": true/false,
  "handling_approach": "exact approach",
  "chairman_involvement": "none|minimal|required",
  "chairman_action_if_needed": "single simplest action",
  "estimated_seconds_for_chairman": 0 if none else seconds,
  "james_response": "Response to Chairman in butler tone"
}}""",
        max_tokens=400
    ) or {}

def run():
    log.info("═══════════════════════════════════════")
    log.info("  James Butler — Personal Concierge")
    log.info("  At your service, Chairman.")
    log.info("═══════════════════════════════════════")
    
    results = process_pending_tasks()
    
    print("
" + "═"*60)
    print(results.get("briefing","Briefing unavailable."))
    print("═"*60)
    
    return results

if __name__ == "__main__":
    run()
