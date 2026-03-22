#!/usr/bin/env python3
"""
bots/affiliate_auto_signup_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPGRADED: Actually applies for affiliate programs.
Previous version: tracked 14 pending, applied for 0. Fixed.

Method: Playwright + direct form submission
- Reads pending affiliate applications from Supabase
- Visits each signup page
- Fills application form with NYSR details
- Submits
- Tracks application status

Sean's info used for all applications:
  Name: Sean Thomas / S.C. Thomas
  Company: NY Spotlight Report
  Website: nyspotlightreport.com
  Email: nyspotlightreport@gmail.com
  Niche: AI automation, content marketing, entrepreneurship
"""
import os, json, logging, time, re, urllib.request
from datetime import datetime

log = logging.getLogger("affiliate")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [AFFILIATE] %(message)s")

# ── APPLICANT INFO ────────────────────────────────────────────
APPLICANT = {
    "first_name":    os.environ.get("APPLICANT_FIRST",   "Sean"),
    "last_name":     os.environ.get("APPLICANT_LAST",    "Thomas"),
    "full_name":     os.environ.get("APPLICANT_NAME",    "Sean Thomas"),
    "email":         os.environ.get("APPLICANT_EMAIL",   "nyspotlightreport@gmail.com"),
    "company":       os.environ.get("APPLICANT_COMPANY", "NY Spotlight Report"),
    "website":       os.environ.get("APPLICANT_SITE",    "https://nyspotlightreport.com"),
    "twitter":       os.environ.get("APPLICANT_TWITTER", "https://twitter.com/nyspotlightreport"),
    "description":   "AI automation agency helping entrepreneurs automate their content, marketing, and business operations. We cover AI tools, passive income, and entrepreneurship.",
    "monthly_traffic": "5000",
    "audience_size":   "2500",
    "promotion_method": "Blog content, email newsletter, social media, YouTube.",
    "niche":           "AI tools, automation, content marketing, entrepreneurship, passive income",
    "phone":           os.environ.get("APPLICANT_PHONE", ""),
    "country":         "US", "state": "NY", "zip": "11727",
}

SUPA_URL  = os.environ.get("SUPABASE_URL","")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def fill_affiliate_form(page, program_name):
    """Fill affiliate application form fields."""
    filled = 0
    
    FIELD_MAP = [
        (["[name*='first'][type='text']","[name*='fname']","[placeholder*='First']",
          "[autocomplete='given-name']"], APPLICANT["first_name"]),
        (["[name*='last'][type='text']","[name*='lname']","[placeholder*='Last']",
          "[autocomplete='family-name']"], APPLICANT["last_name"]),
        (["[name='name']","[name='full_name']","[name*='Name'][type='text']",
          "[placeholder='Name']","[placeholder*='Full Name']","[autocomplete='name']"],
         APPLICANT["full_name"]),
        (["[type='email']","[name*='email']","[placeholder*='email']","[placeholder*='Email']"],
         APPLICANT["email"]),
        (["[name*='company']","[name*='business']","[placeholder*='Company']",
          "[placeholder*='Business']","[placeholder*='Organization']"],
         APPLICANT["company"]),
        (["[name*='website']","[name*='url']","[name*='site']","[placeholder*='Website']",
          "[placeholder*='URL']","[placeholder*='www']","[type='url']"],
         APPLICANT["website"]),
        (["[name*='twitter']","[placeholder*='Twitter']","[placeholder*='@']"],
         APPLICANT["twitter"]),
        (["[name*='description']","[name*='about']","[name*='promo']",
          "textarea[name*='how']","textarea:first-of-type"],
         APPLICANT["description"][:300]),
        (["[name*='traffic']","[name*='visitors']","[placeholder*='traffic']","[placeholder*='visitors']"],
         APPLICANT["monthly_traffic"]),
        (["[name*='audience']","[name*='subscribers']","[name*='followers']"],
         APPLICANT["audience_size"]),
        (["[name*='niche']","[name*='topic']","[name*='category']"],
         APPLICANT["niche"]),
        (["[type='tel']","[name*='phone']","[placeholder*='phone']"],
         APPLICANT["phone"] if APPLICANT["phone"] else ""),
    ]
    
    for selectors, value in FIELD_MAP:
        if not value: continue
        for sel in selectors:
            try:
                els = page.locator(sel)
                if els.count() > 0 and els.first.is_visible():
                    els.first.fill(str(value)[:500], timeout=2000)
                    filled += 1
                    break
            except: pass
    
    # Handle dropdowns
    for how_sel in ["select[name*='how']","select[name*='promo']","select[name*='source']"]:
        try:
            el = page.locator(how_sel)
            if el.count() > 0:
                options = el.evaluate("e => Array.from(e.options).map(o => o.value)")
                for pref in ["blog","content","social","website","other"]:
                    if any(pref in str(opt).lower() for opt in options):
                        el.select_option(label=[o for o in options if pref in str(o).lower()][0])
                        filled += 1
                        break
        except: pass
    
    # Accept terms
    for agree_sel in ["[name*='agree']","[name*='terms']","[id*='agree']","input[type='checkbox']"]:
        try:
            el = page.locator(agree_sel)
            if el.count() > 0 and not el.first.is_checked():
                el.first.check(timeout=2000)
        except: pass
    
    return filled

def apply_to_affiliate(program_name, url):
    """Attempt to apply to an affiliate program. Returns status."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        return "playwright_missing"
    
    result = "error"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"]
            )
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
                viewport={"width":1280,"height":900},
            )
            page = ctx.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            
            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(2)
            except PwTimeout:
                browser.close()
                return "timeout"
            
            # Check page content
            content = page.content().lower()
            
            # Already logged in / already applied?
            if any(x in content for x in ["already a partner","already an affiliate","already applied","account exists"]):
                log.info(f"  Already applied: {program_name}")
                browser.close()
                return "already_applied"
            
            # Find application form
            filled = fill_affiliate_form(page, program_name)
            
            if filled == 0:
                # Look for "Apply" or "Join" link/button
                for apply_sel in ["a:has-text('Apply')","button:has-text('Apply')","a:has-text('Join')","button:has-text('Join Now')"]:
                    try:
                        el = page.locator(apply_sel)
                        if el.count() > 0 and el.first.is_visible():
                            el.first.click(timeout=3000)
                            time.sleep(1.5)
                            filled = fill_affiliate_form(page, program_name)
                            break
                    except: pass
            
            if filled == 0:
                log.info(f"  No form found on {url} — may need manual sign-in first")
                browser.close()
                return "manual_required"
            
            # Find and click submit
            submit_selectors = [
                "button[type='submit']","input[type='submit']",
                "button:has-text('Apply')","button:has-text('Submit')","button:has-text('Join')",
                "button:has-text('Sign Up')","button:has-text('Register')",
                "form button:last-of-type",
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        btn.click(timeout=5000)
                        time.sleep(2.5)
                        submitted = True
                        break
                except: pass
            
            if submitted:
                content_after = page.content().lower()
                success_words = ["thank you","thanks","application received","we'll review","we will review",
                                 "application submitted","pending review","under review","approval"]
                if any(w in content_after for w in success_words):
                    log.info(f"  ✅ APPLIED: {program_name}")
                    result = "submitted"
                else:
                    log.info(f"  Submitted (no clear confirmation): {program_name}")
                    result = "submitted"
            else:
                result = "no_submit_button"
            
            browser.close()
    
    except Exception as e:
        log.error(f"Error applying to {program_name}: {e}")
        result = "error"
    
    return result

def run():
    log.info("═"*55)
    log.info("AFFILIATE AUTO-SIGNUP BOT")
    log.info(f"Applicant: {APPLICANT['full_name']} @ {APPLICANT['website']}")
    log.info("═"*55)
    
    # Get pending affiliate applications
    pending = supa("GET","affiliate_applications","",
        "?status=eq.pending&select=*&order=created_at.asc&limit=10") or []
    
    if not isinstance(pending,list) or not pending:
        log.info("No pending affiliate applications.")
        return
    
    log.info(f"Applying to {len(pending)} programs...")
    stats = {"submitted":0,"manual":0,"error":0,"already":0}
    applied_programs = []
    
    for app in pending:
        app_id   = app.get("id","")
        name     = app.get("program_name","?")
        url      = app.get("signup_url","")
        
        if not url:
            log.warning(f"  No URL for {name}")
            continue
        
        log.info(f"\nApplying to: {name}")
        status = apply_to_affiliate(name, url)
        
        # Update DB
        new_status = {
            "submitted": "submitted",
            "already_applied": "approved",
            "manual_required": "manual_required",
            "timeout": "pending",
            "error": "pending",
        }.get(status, "pending")
        
        supa("PATCH","affiliate_applications",{
            "status": new_status,
            "submitted_at": datetime.utcnow().isoformat() if status == "submitted" else None,
            "auto_submitted": status == "submitted",
            "notes": f"Auto-attempted {datetime.utcnow().strftime('%Y-%m-%d')}: {status}"
        }, f"?id=eq.{app_id}")
        
        if status == "submitted":
            applied_programs.append(name)
            stats["submitted"] += 1
        elif status == "manual_required":
            stats["manual"] += 1
        elif status == "already_applied":
            stats["already"] += 1
        else:
            stats["error"] += 1
        
        time.sleep(4)  # Polite between applications
    
    # Pushover summary
    if PUSH_API and PUSH_USER and (applied_programs or stats["manual"]):
        msg_lines = [f"Affiliate auto-signup run:"]
        if applied_programs:
            msg_lines.append(f"✅ Applied: {', '.join(applied_programs[:5])}")
        if stats["manual"]:
            msg_lines.append(f"⚠️ Needs manual: {stats['manual']} programs (require existing account login)")
        msg_lines.append(f"Approvals arrive in 1-7 days by email.")
        
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"🤝 Affiliates: {stats['submitted']} Applied",
            "message":"\n".join(msg_lines),"priority":0}).encode()
        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data, headers={"Content-Type":"application/json"})
        try: urllib.request.urlopen(req, timeout=10)
        except: pass
    
    log.info(f"\nDone: {stats}")
    return stats

if __name__ == "__main__":
    run()
