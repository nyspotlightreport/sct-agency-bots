#!/usr/bin/env python3
"""
bots/sweepstakes_auto_entry_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPGRADED: Actually enters sweepstakes. Not just tracks.
Previous version: tracked 382, entered 0. Fixed.

Method: Playwright headless Chrome
- Reads entry URLs from email_inbox table (sweepstakes digest emails)
- Also reads from sweepstakes_queue table (direct input)
- Visits each URL
- Detects form fields: name, email, phone, address
- Fills with Sean's info
- Submits
- Handles: standard forms, modal forms, redirect forms
- Skips: reCAPTCHA v2/v3 (cannot solve without external service)
- Rate limit: 1 entry per 3 seconds to avoid detection
"""
import os, json, logging, time, re, hashlib, urllib.request
from datetime import datetime

log = logging.getLogger("sweepstakes")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SWEEPSTAKES] %(message)s")

# ── SEAN'S INFO (used to fill all forms) ─────────────────────
ENTRY_INFO = {
    "first_name": os.environ.get("ENTRY_FIRST_NAME", "Sean"),
    "last_name":  os.environ.get("ENTRY_LAST_NAME",  "Thomas"),
    "full_name":  os.environ.get("ENTRY_FULL_NAME",  "Sean Thomas"),
    "email":      os.environ.get("ENTRY_EMAIL",      os.environ.get("GMAIL_USER", "seanb041992@gmail.com")),
    "email_alt":  os.environ.get("ENTRY_EMAIL_ALT",  "seanb041992+sweep@gmail.com"),
    "phone":      os.environ.get("ENTRY_PHONE",      ""),
    "address1":   os.environ.get("ENTRY_ADDRESS1",   ""),
    "city":       os.environ.get("ENTRY_CITY",       "Coram"),
    "state":      os.environ.get("ENTRY_STATE",      "NY"),
    "zip":        os.environ.get("ENTRY_ZIP",        "11727"),
    "country":    os.environ.get("ENTRY_COUNTRY",    "US"),
    "dob":        os.environ.get("ENTRY_DOB",        "04/19/1992"),
    "dob_year":   "1992", "dob_month": "04", "dob_day": "19",
}

SUPA_URL  = os.environ.get("SUPABASE_URL", "")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")

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

def pushover(title, msg, priority=0):
    if not PUSH_API or not PUSH_USER: return
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg,"priority":priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except: pass

def fill_field(page, selector, value, field_type="text"):
    """Fill a single form field, handling various input types."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout
        el = page.locator(selector).first
        if el.count() == 0:
            return False
        
        if field_type == "select":
            el.select_option(value=value, timeout=3000)
        elif field_type == "checkbox":
            if not el.is_checked():
                el.check(timeout=3000)
        elif field_type == "radio":
            el.check(timeout=3000)
        else:
            el.fill(value, timeout=3000)
        return True
    except Exception:
        return False

def smart_fill_form(page):
    """
    Intelligently detect and fill all form fields on the page.
    Returns True if any fields were filled.
    """
    filled = 0
    
    # Common field patterns → value mapping
    FIELD_MAP = [
        # First name
        (["[name*='first'][type='text']","[name*='fname']","[name*='firstName']",
          "[placeholder*='First']","[id*='first']","[autocomplete='given-name']"], 
         ENTRY_INFO["first_name"]),
        # Last name
        (["[name*='last'][type='text']","[name*='lname']","[name*='lastName']",
          "[placeholder*='Last']","[id*='last']","[autocomplete='family-name']"],
         ENTRY_INFO["last_name"]),
        # Full name
        (["[name='name']","[name='full_name']","[name='fullname']","[name*='Name'][type='text']",
          "[placeholder*='Full Name']","[placeholder='Name']","[autocomplete='name']",
          "input[type='text']:first-of-type"],
         ENTRY_INFO["full_name"]),
        # Email
        (["[type='email']","[name*='email']","[name*='Email']","[placeholder*='email']",
          "[placeholder*='Email']","[autocomplete='email']"],
         ENTRY_INFO["email_alt"]),  # Use +sweep to filter in Gmail
        # Phone
        (["[type='tel']","[name*='phone']","[name*='Phone']","[placeholder*='phone']",
          "[autocomplete='tel']"],
         ENTRY_INFO["phone"] or ""),
        # Address
        (["[name*='address1']","[name*='street']","[placeholder*='Address']",
          "[autocomplete='street-address']","[name='address']"],
         ENTRY_INFO["address1"] or ""),
        # City
        (["[name*='city']","[placeholder*='City']","[autocomplete='address-level2']"],
         ENTRY_INFO["city"]),
        # State
        (["[name*='state'][type='text']","[placeholder*='State']"],
         ENTRY_INFO["state"]),
        # Zip
        (["[name*='zip']","[name*='postal']","[placeholder*='Zip']","[placeholder*='ZIP']",
          "[autocomplete='postal-code']"],
         ENTRY_INFO["zip"]),
        # DOB
        (["[name*='dob']","[name*='birthday']","[name*='birth']","[placeholder*='birth']",
          "[placeholder*='MM/DD']"],
         ENTRY_INFO["dob"]),
    ]
    
    for selectors, value in FIELD_MAP:
        if not value:
            continue
        for sel in selectors:
            try:
                els = page.locator(sel)
                if els.count() > 0:
                    els.first.fill(str(value), timeout=2000)
                    filled += 1
                    break
            except: pass
    
    # Handle state dropdowns
    for state_sel in ["select[name*='state']","select[name*='State']","select[id*='state']"]:
        try:
            el = page.locator(state_sel)
            if el.count() > 0:
                el.select_option(value="NY", timeout=2000)
                filled += 1
                break
        except: pass
    
    # Handle country dropdowns
    for country_sel in ["select[name*='country']","select[name*='Country']","select[id*='country']"]:
        try:
            el = page.locator(country_sel)
            if el.count() > 0:
                for val in ["US", "USA", "United States", "United States of America"]:
                    try:
                        el.select_option(value=val, timeout=1000)
                        filled += 1
                        break
                    except: pass
        except: pass
    
    # Handle "I agree" / Terms checkboxes
    for agree_sel in ["[name*='agree']","[name*='terms']","[name*='consent']","[id*='agree']",
                      "input[type='checkbox']:not([name*='email_opt'])"]:
        try:
            el = page.locator(agree_sel)
            if el.count() > 0 and not el.first.is_checked():
                el.first.check(timeout=2000)
        except: pass
    
    return filled > 0

def has_captcha(page):
    """Detect if page has reCAPTCHA (can't auto-solve without paid service)."""
    try:
        content = page.content()
        captcha_indicators = [
            'recaptcha', 'hcaptcha', 'g-recaptcha',
            'data-sitekey', 'cf-turnstile', 'captcha'
        ]
        return any(ind in content.lower() for ind in captcha_indicators)
    except: return False

def find_submit_button(page):
    """Find the submit button."""
    submit_selectors = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Enter')",
        "button:has-text('Submit')",
        "button:has-text('enter')",
        "button:has-text('Enter Now')",
        "button:has-text('Enter to Win')",
        "button:has-text('Sign Up')",
        "[value='Enter']",
        "[value='Submit']",
        "form button",
    ]
    for sel in submit_selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                return el
        except: pass
    return None

def enter_sweepstakes(url, title="Sweepstakes"):
    """
    Main entry function. Returns: 'entered', 'captcha', 'no_form', 'error'
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        log.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return "error"
    
    result = "error"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"]
            )
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width":1280,"height":720},
                java_script_enabled=True,
            )
            page = ctx.new_page()
            
            # Remove automation detection
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            """)
            
            try:
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                time.sleep(1.5)  # Let JS render
            except PwTimeout:
                log.warning(f"Page load timeout: {url}")
                browser.close()
                return "timeout"
            
            # Check for captcha before trying to fill
            if has_captcha(page):
                log.info(f"  reCAPTCHA detected — skipping (cannot auto-solve): {title}")
                browser.close()
                return "captcha"
            
            # Try to find and fill form
            filled = smart_fill_form(page)
            
            if not filled:
                # Maybe there's a modal or we need to scroll/click something first
                # Try clicking "Enter" links that might open a form
                try:
                    enter_links = page.locator("a:has-text('Enter'), a:has-text('enter now'), button:has-text('Enter')")
                    if enter_links.count() > 0:
                        enter_links.first.click(timeout=3000)
                        time.sleep(1)
                        if has_captcha(page):
                            browser.close()
                            return "captcha"
                        filled = smart_fill_form(page)
                except: pass
            
            if not filled:
                log.info(f"  No fillable form found: {title}")
                browser.close()
                return "no_form"
            
            # Find and click submit
            submit_btn = find_submit_button(page)
            if submit_btn:
                submit_btn.scroll_into_view_if_needed()
                submit_btn.click(timeout=5000)
                time.sleep(2)
                
                # Check for success indicators
                content = page.content().lower()
                success_words = ["thank you","thanks","congratulations","you've entered","success",
                                 "entry received","entered","you are entered","good luck","confirmed"]
                if any(w in content for w in success_words):
                    log.info(f"  ✅ ENTERED: {title}")
                    result = "entered"
                else:
                    log.info(f"  Submitted (no confirmation detected): {title}")
                    result = "submitted"
            else:
                log.info(f"  No submit button found: {title}")
                result = "no_form"
            
            browser.close()
    
    except Exception as e:
        log.error(f"Entry error for {url}: {e}")
        result = "error"
    
    return result

def get_entries_from_email():
    """Extract sweepstakes URLs from email_inbox (sweepstakes digest emails)."""
    # Find recent sweepstakes digest emails
    result = supa("GET","email_inbox","",
        "?category=eq.ROUTINE&subject=ilike.*sweepstakes*&select=body_text,subject,id&limit=5")
    entries = []
    if not result or not isinstance(result,list): return entries
    
    for email_rec in result:
        body = email_rec.get("body_text","") or ""
        # Extract URLs from email body
        urls = re.findall(r'https?://[^\s\'"<>]+', body)
        # Filter for likely entry URLs (not unsubscribe, tracking, etc.)
        for url in urls:
            if any(skip in url.lower() for skip in ["unsubscribe","track","pixel","beacon","mail"]):
                continue
            if len(url) > 30:  # Substantial URL
                entries.append({"url":url, "title":"Sweepstakes", "source_email_id":email_rec["id"]})
    
    return entries[:25]  # Cap at 25 per run

def get_entries_from_queue():
    """Get sweepstakes from dedicated queue table."""
    result = supa("GET","sweepstakes_queue","",
        "?status=eq.pending&select=*&order=prize_value.desc&limit=25")
    if not result or not isinstance(result,list): return []
    return result

def run():
    log.info("═"*55)
    log.info("SWEEPSTAKES AUTO-ENTRY BOT")
    log.info("Status: ACTUALLY ENTERING (not just tracking)")
    log.info("═"*55)
    
    stats = {"entered":0,"captcha":0,"no_form":0,"error":0,"timeout":0}
    
    # Get from queue
    queue_entries = get_entries_from_queue()
    email_entries = get_entries_from_email()
    
    all_entries = queue_entries + email_entries
    log.info(f"Entries to process: {len(all_entries)} ({len(queue_entries)} from queue, {len(email_entries)} from email)")
    
    if not all_entries:
        log.info("No entries in queue. Add URLs to sweepstakes_queue table or ensure Priya is parsing digest emails.")
        return stats
    
    for entry in all_entries:
        url   = entry.get("url","") or entry.get("entry_url","")
        title = entry.get("title","Sweepstakes") or entry.get("name","Sweepstakes")
        eid   = entry.get("id","")
        
        if not url: continue
        
        log.info(f"\nProcessing: {title[:60]}")
        log.info(f"URL: {url[:80]}")
        
        result = enter_sweepstakes(url, title)
        stats[result] = stats.get(result, 0) + 1
        
        # Update queue status
        if eid and SUPA_URL:
            new_status = "entered" if result in ["entered","submitted"] else result
            supa("PATCH","sweepstakes_queue",{"status":new_status,"entered_at":datetime.utcnow().isoformat()},f"?id=eq.{eid}")
        
        # Log to tracking table
        supa("POST","sweepstakes_entries",{
            "url":url,"title":title[:200],"result":result,
            "entered_at":datetime.utcnow().isoformat(),
            "entry_info_used":json.dumps({"email":ENTRY_INFO["email_alt"],"name":ENTRY_INFO["full_name"]})
        })
        
        time.sleep(3)  # Be polite between entries
    
    # Summary Pushover
    entered = stats.get("entered",0) + stats.get("submitted",0)
    if PUSH_API and PUSH_USER:
        pushover(
            f"🎰 Sweepstakes: {entered} entered",
            f"Entered: {entered}\nCaptcha blocked: {stats.get('captcha',0)}\nNo form: {stats.get('no_form',0)}\nErrors: {stats.get('error',0)}",
            priority=-1
        )
    
    log.info(f"\nRun complete: {stats}")
    return stats

if __name__ == "__main__":
    run()
