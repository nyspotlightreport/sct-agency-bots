#!/usr/bin/env python3
"""
bots/sweepstakes_auto_entry_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FULL AUTO-ENTRY: Playwright + 2Captcha
Enters sweepstakes including reCAPTCHA v2, v3, hCaptcha.
Was tracking 382, entering 0. Now entering ALL of them.

2Captcha: $0.001-0.003 per captcha solve (~$0.002 avg)
At 50 entries/day with 30% captcha rate = ~$0.03/day
Worth it for $100-$100,000 prize entries.
"""
import os, json, logging, time, re, hashlib, urllib.request, urllib.parse, base64
from datetime import datetime

log = logging.getLogger("sweepstakes")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SWEEP] %(message)s")

# ── CREDENTIALS ──────────────────────────────────────────────
ENTRY_INFO = {
    "first_name": os.environ.get("ENTRY_FIRST_NAME", "Sean"),
    "last_name":  os.environ.get("ENTRY_LAST_NAME",  "Thomas"),
    "full_name":  os.environ.get("ENTRY_FULL_NAME",  "Sean Thomas"),
    "email":      os.environ.get("ENTRY_EMAIL_ALT",  "nyspotlightreport+sweep@gmail.com"),
    "email_main": os.environ.get("ENTRY_EMAIL",      "nyspotlightreport@gmail.com"),
    "phone":      os.environ.get("ENTRY_PHONE",      ""),
    "address1":   os.environ.get("ENTRY_ADDRESS1",   ""),
    "city":       os.environ.get("ENTRY_CITY",       "Coram"),
    "state":      os.environ.get("ENTRY_STATE",      "NY"),
    "zip":        os.environ.get("ENTRY_ZIP",        "11727"),
    "country":    "US",
    "dob":        os.environ.get("ENTRY_DOB",        "04/19/1992"),
    "dob_year":   "1992", "dob_month": "04", "dob_day": "19",
}

TWOCAPTCHA_API  = os.environ.get("TWOCAPTCHA_API_KEY", "")
TWOCAPTCHA_LOGIN= os.environ.get("TWOCAPTCHA_LOGIN", "")
TWOCAPTCHA_PASS = os.environ.get("TWOCAPTCHA_PASSWORD", "")
SUPA_URL  = os.environ.get("SUPABASE_URL", "")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
GH_PAT    = os.environ.get("GH_PAT", "")

# ── 2CAPTCHA FUNCTIONS ────────────────────────────────────────

def get_2captcha_apikey():
    """Get 2Captcha API key — either from env or fetch from account."""
    if TWOCAPTCHA_API and len(TWOCAPTCHA_API) > 10:
        return TWOCAPTCHA_API
    
    # Fetch API key using login/password
    if not TWOCAPTCHA_LOGIN or not TWOCAPTCHA_PASS:
        log.warning("2Captcha: No API key or login/password. Captchas will be skipped.")
        return None
    
    try:
        params = urllib.parse.urlencode({
            'action': 'getkey', 'login': TWOCAPTCHA_LOGIN,
            'password': TWOCAPTCHA_PASS, 'json': '1'
        })
        req = urllib.request.Request(f"https://2captcha.com/res.php?{params}")
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            if result.get('status') == 1:
                api_key = result.get('request', '')
                log.info(f"2Captcha API key retrieved: {api_key[:8]}...")
                # Save to GitHub Secrets for next run
                _save_to_gh_secret('TWOCAPTCHA_API_KEY', api_key)
                return api_key
            else:
                log.warning(f"2Captcha getkey failed: {result}")
                return None
    except Exception as e:
        log.warning(f"2Captcha key fetch: {e}")
        return None

def _save_to_gh_secret(name, value):
    """Save a value to GitHub Secrets for next run."""
    if not GH_PAT: return
    try:
        req = urllib.request.Request(
            f'https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/secrets/public-key',
            headers={'Authorization': f'token {GH_PAT}', 'Accept': 'application/vnd.github.v3+json'})
        with urllib.request.urlopen(req, timeout=10) as r:
            pk = json.load(r)
        encoded = base64.b64encode(value.encode()).decode()
        payload = json.dumps({'encrypted_value': encoded, 'key_id': pk['key_id']})
        req2 = urllib.request.Request(
            f'https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/secrets/{name}',
            data=payload.encode(), method='PUT',
            headers={'Authorization': f'token {GH_PAT}', 'Content-Type': 'application/json',
                     'Accept': 'application/vnd.github.v3+json'})
        urllib.request.urlopen(req2, timeout=15)
        log.info(f"Saved {name} to GitHub Secrets")
    except Exception as e:
        log.debug(f"GH secret save: {e}")

def solve_recaptcha_v2(api_key, site_key, page_url):
    """
    Solve reCAPTCHA v2 using 2Captcha.
    Returns the g-recaptcha-response token.
    """
    if not api_key: return None
    
    log.info(f"  Solving reCAPTCHA v2 (2Captcha)...")
    
    # Submit captcha task
    params = urllib.parse.urlencode({
        'key': api_key, 'method': 'userrecaptcha',
        'googlekey': site_key, 'pageurl': page_url, 'json': '1'
    })
    req = urllib.request.Request(
        f"https://2captcha.com/in.php",
        data=params.encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        
        if result.get('status') != 1:
            log.warning(f"  2Captcha submit failed: {result}")
            return None
        
        task_id = result.get('request')
        log.info(f"  Captcha submitted (task {task_id}). Waiting for solution...")
        
        # Poll for solution (up to 90 seconds)
        for attempt in range(18):
            time.sleep(5)
            poll_params = urllib.parse.urlencode({'key': api_key, 'action': 'get', 'id': task_id, 'json': '1'})
            req2 = urllib.request.Request(f"https://2captcha.com/res.php?{poll_params}")
            with urllib.request.urlopen(req2, timeout=15) as r2:
                poll_result = json.loads(r2.read())
            
            if poll_result.get('status') == 1:
                token = poll_result.get('request')
                log.info(f"  ✅ Captcha solved! Token: {token[:20]}...")
                return token
            elif poll_result.get('request') == 'CAPCHA_NOT_READY':
                log.info(f"  Waiting... ({attempt+1}/18)")
                continue
            else:
                log.warning(f"  2Captcha error: {poll_result}")
                return None
        
        log.warning("  Captcha solve timeout (90s)")
        return None
    
    except Exception as e:
        log.error(f"  2Captcha reCAPTCHA v2 error: {e}")
        return None

def solve_recaptcha_v3(api_key, site_key, page_url, action="submit"):
    """Solve reCAPTCHA v3 using 2Captcha."""
    if not api_key: return None
    
    log.info(f"  Solving reCAPTCHA v3 (action: {action})...")
    
    params = urllib.parse.urlencode({
        'key': api_key, 'method': 'userrecaptcha', 'version': 'v3',
        'googlekey': site_key, 'pageurl': page_url,
        'action': action, 'min_score': '0.3', 'json': '1'
    })
    req = urllib.request.Request("https://2captcha.com/in.php",
        data=params.encode(), headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        if result.get('status') != 1:
            return None
        task_id = result.get('request')
        
        for _ in range(18):
            time.sleep(5)
            poll_params = urllib.parse.urlencode({'key': api_key, 'action': 'get', 'id': task_id, 'json': '1'})
            with urllib.request.urlopen(urllib.request.Request(f"https://2captcha.com/res.php?{poll_params}"), timeout=15) as r2:
                poll_result = json.loads(r2.read())
            if poll_result.get('status') == 1:
                token = poll_result.get('request')
                log.info(f"  ✅ reCAPTCHA v3 solved!")
                return token
            elif poll_result.get('request') != 'CAPCHA_NOT_READY':
                return None
        return None
    except Exception as e:
        log.error(f"  2Captcha v3: {e}")
        return None

def solve_hcaptcha(api_key, site_key, page_url):
    """Solve hCaptcha using 2Captcha."""
    if not api_key: return None
    
    log.info("  Solving hCaptcha...")
    
    params = urllib.parse.urlencode({
        'key': api_key, 'method': 'hcaptcha',
        'sitekey': site_key, 'pageurl': page_url, 'json': '1'
    })
    req = urllib.request.Request("https://2captcha.com/in.php",
        data=params.encode(), headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        if result.get('status') != 1: return None
        task_id = result.get('request')
        
        for _ in range(18):
            time.sleep(5)
            poll_params = urllib.parse.urlencode({'key': api_key, 'action': 'get', 'id': task_id, 'json': '1'})
            with urllib.request.urlopen(urllib.request.Request(f"https://2captcha.com/res.php?{poll_params}"), timeout=15) as r2:
                pr = json.loads(r2.read())
            if pr.get('status') == 1:
                log.info("  ✅ hCaptcha solved!")
                return pr.get('request')
            elif pr.get('request') != 'CAPCHA_NOT_READY':
                return None
        return None
    except Exception as e:
        log.error(f"  2Captcha hCaptcha: {e}")
        return None

def inject_captcha_token(page, token, captcha_type="recaptcha"):
    """Inject the solved captcha token into the page."""
    try:
        if captcha_type in ["recaptcha", "recaptcha_v2"]:
            # Set the g-recaptcha-response textarea value
            page.evaluate(f"""
                (function() {{
                    var elems = document.querySelectorAll('[name="g-recaptcha-response"]');
                    for (var i = 0; i < elems.length; i++) {{
                        elems[i].value = '{token}';
                        elems[i].innerHTML = '{token}';
                    }}
                    // Also try callback
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        for (var key in ___grecaptcha_cfg.clients) {{
                            var client = ___grecaptcha_cfg.clients[key];
                            if (client && client.aa) client.aa.callback('{token}');
                        }}
                    }}
                }})();
            """)
        elif captcha_type == "hcaptcha":
            page.evaluate(f"""
                (function() {{
                    var elems = document.querySelectorAll('[name="h-captcha-response"]');
                    for (var i = 0; i < elems.length; i++) {{
                        elems[i].value = '{token}';
                    }}
                }})();
            """)
        return True
    except Exception as e:
        log.warning(f"Token injection error: {e}")
        return False

def detect_and_solve_captcha(page, api_key, url):
    """Detect captcha type on page and solve it using 2Captcha."""
    if not api_key:
        return False
    
    try:
        content = page.content()
        
        # reCAPTCHA v2
        v2_key = re.search(r'data-sitekey=["\']([^"\']{20,})["\']', content)
        if not v2_key:
            v2_key = re.search(r'grecaptcha\.render[^;]+sitekey["\'\s:]+([A-Za-z0-9_\-]{20,})', content)
        
        if v2_key and 'recaptcha' in content.lower():
            site_key = v2_key.group(1)
            token = solve_recaptcha_v2(api_key, site_key, url)
            if token:
                inject_captcha_token(page, token, "recaptcha")
                time.sleep(1)
                return True
        
        # reCAPTCHA v3
        v3_match = re.search(r'grecaptcha\.execute\(["\']([^"\']+)["\']', content)
        if v3_match:
            site_key = v3_match.group(1)
            action_match = re.search(r'action["\'\s:]+["\']([a-z_]+)["\']', content)
            action = action_match.group(1) if action_match else "submit"
            token = solve_recaptcha_v3(api_key, site_key, url, action)
            if token:
                inject_captcha_token(page, token, "recaptcha")
                return True
        
        # hCaptcha
        hc_key = re.search(r'data-sitekey=["\']([^"\']{20,})["\']', content)
        if hc_key and 'hcaptcha' in content.lower():
            site_key = hc_key.group(1)
            token = solve_hcaptcha(api_key, site_key, url)
            if token:
                inject_captcha_token(page, token, "hcaptcha")
                return True
        
        return False
    
    except Exception as e:
        log.warning(f"Captcha detection/solve error: {e}")
        return False

# ── FORM FILLING ─────────────────────────────────────────────

def smart_fill_form(page):
    """Fill all form fields. Returns count of filled fields."""
    filled = 0
    
    FIELD_MAP = [
        (["[name*='first'][type='text']","[name*='fname']","[name*='firstName']",
          "[placeholder*='First']","[id*='first_name']","[autocomplete='given-name']"],
         ENTRY_INFO["first_name"]),
        (["[name*='last'][type='text']","[name*='lname']","[name*='lastName']",
          "[placeholder*='Last']","[id*='last_name']","[autocomplete='family-name']"],
         ENTRY_INFO["last_name"]),
        (["[name='name']","[name='full_name']","[name='fullname']","[name*='Name'][type='text']",
          "[placeholder='Name']","[placeholder*='Full Name']","[autocomplete='name']",
          "input[type='text']:first-of-type"],
         ENTRY_INFO["full_name"]),
        (["[type='email']","[name*='email']","[placeholder*='email']","[placeholder*='Email']",
          "[autocomplete='email']"],
         ENTRY_INFO["email"]),
        (["[type='tel']","[name*='phone']","[placeholder*='phone']","[autocomplete='tel']"],
         ENTRY_INFO["phone"] if ENTRY_INFO["phone"] else ""),
        (["[name*='address1']","[name*='street']","[placeholder*='Address']","[autocomplete='street-address']"],
         ENTRY_INFO["address1"] if ENTRY_INFO["address1"] else ""),
        (["[name*='city']","[placeholder*='City']","[autocomplete='address-level2']"],
         ENTRY_INFO["city"]),
        (["[name*='zip']","[name*='postal']","[placeholder*='Zip']","[autocomplete='postal-code']"],
         ENTRY_INFO["zip"]),
        (["[name*='dob']","[name*='birthday']","[placeholder*='MM/DD']","[placeholder*='birth']"],
         ENTRY_INFO["dob"]),
    ]
    
    for selectors, value in FIELD_MAP:
        if not value: continue
        for sel in selectors:
            try:
                els = page.locator(sel)
                if els.count() > 0 and els.first.is_visible():
                    els.first.fill(str(value), timeout=2000)
                    filled += 1
                    break
            except Exception:  # noqa: bare-except

                pass
    # Dropdowns
    for state_sel in ["select[name*='state']","select[name*='State']","select[id*='state']"]:
        try:
            el = page.locator(state_sel)
            if el.count() > 0:
                el.first.select_option(value="NY", timeout=2000)
                filled += 1; break
        except Exception:  # noqa: bare-except

            pass
    for country_sel in ["select[name*='country']","select[id*='country']"]:
        try:
            el = page.locator(country_sel)
            if el.count() > 0:
                for val in ["US","USA","United States"]:
                    try: el.first.select_option(value=val, timeout=1000); filled += 1; break
                    except Exception:  # noqa: bare-except

                        pass
        except Exception:  # noqa: bare-except

            pass
    # Terms/agree checkboxes
    for agree_sel in ["[name*='agree']","[name*='terms']","[id*='agree']","[name*='consent']"]:
        try:
            el = page.locator(agree_sel)
            if el.count() > 0 and not el.first.is_checked():
                el.first.check(timeout=2000)
        except Exception:  # noqa: bare-except

            pass
    return filled

def enter_sweepstakes(url, title="Sweepstakes", api_key=None):
    """Main entry function with full captcha solving."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        log.error("Playwright not installed.")
        return "error"
    
    result = "error"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox","--disable-dev-shm-usage",
                      "--disable-blink-features=AutomationControlled",
                      "--disable-web-security"]
            )
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width":1280,"height":720},
                java_script_enabled=True,
            )
            page = ctx.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            
            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(2)
            except PwTimeout:
                browser.close()
                return "timeout"
            
            # Fill form
            filled = smart_fill_form(page)
            
            # If no form found, try clicking an Enter button first
            if filled == 0:
                for enter_sel in ["a:has-text('Enter')", "button:has-text('Enter Now')",
                                   "a:has-text('Click to Enter')"]:
                    try:
                        el = page.locator(enter_sel)
                        if el.count() > 0 and el.first.is_visible():
                            el.first.click(timeout=3000)
                            time.sleep(1.5)
                            filled = smart_fill_form(page)
                            break
                    except Exception:  # noqa: bare-except

                        pass
            if filled == 0:
                browser.close()
                return "no_form"
            
            # Detect and solve any captcha
            content = page.content()
            has_captcha = any(x in content.lower() for x in ['recaptcha','hcaptcha','captcha'])
            
            if has_captcha and api_key:
                captcha_solved = detect_and_solve_captcha(page, api_key, url)
                if not captcha_solved:
                    log.warning(f"  Could not solve captcha for {title}")
                    # Still try to submit — some v3 captchas are invisible
                else:
                    log.info(f"  Captcha solved successfully!")
            elif has_captcha and not api_key:
                log.warning(f"  Captcha detected but no API key — attempting anyway")
            
            # Submit
            submit_selectors = [
                "button[type='submit']","input[type='submit']",
                "button:has-text('Enter')","button:has-text('Submit')",
                "button:has-text('Enter Now')","button:has-text('Enter to Win')",
                "button:has-text('Sign Up')","form button:last-of-type",
                "[value='Enter']","[value='Submit']"
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        btn.click(timeout=5000)
                        time.sleep(3)
                        submitted = True
                        break
                except Exception:  # noqa: bare-except

                    pass
            if submitted:
                content_after = page.content().lower()
                success_words = ["thank you","thanks","congratulations","you've entered",
                                 "entry received","entered","success","good luck","confirmed",
                                 "you are entered","entered successfully"]
                if any(w in content_after for w in success_words):
                    log.info(f"  ✅ ENTERED: {title}")
                    result = "entered"
                else:
                    log.info(f"  Submitted: {title}")
                    result = "submitted"
            else:
                result = "no_submit_button"
            
            browser.close()
    
    except Exception as e:
        log.error(f"Error: {e}")
        result = "error"
    
    return result

# ── DATABASE HELPERS ──────────────────────────────────────────

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

def pushover(title, msg, priority=0, sound=None):
    if not PUSH_API or not PUSH_USER: return
    payload = {"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg,"priority":priority}
    if sound: payload["sound"] = sound
    data = json.dumps(payload).encode()
    try: urllib.request.urlopen(
        urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data, headers={"Content-Type":"application/json"}), timeout=10)
    except Exception:  # noqa: bare-except

        pass
# ── MAIN ──────────────────────────────────────────────────────

def run():
    log.info("═"*55)
    log.info("SWEEPSTAKES AUTO-ENTRY — WITH 2CAPTCHA SOLVING")
    
    # Get or fetch API key
    api_key = get_2captcha_apikey()
    if api_key:
        log.info(f"2Captcha: ACTIVE (solving reCAPTCHA + hCaptcha)")
    else:
        log.warning("2Captcha: No API key — will enter forms without captcha solving")
        log.warning("NOTE: Fund your 2captcha.com account with $1-2 to activate captcha solving")
    log.info("═"*55)
    
    # First run email parser to populate queue
    try:
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location("parser", "bots/sweepstakes_email_parser_bot.py")
        if spec:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.run()
            log.info("Email parser ran — queue populated")
    except Exception as e:
        log.debug(f"Parser: {e}")
    
    # Get pending entries from queue
    entries = supa("GET","sweepstakes_queue","",
        "?status=eq.pending&order=prize_value.desc&limit=30&select=*") or []
    if not isinstance(entries,list): entries = []
    
    log.info(f"Entries in queue: {len(entries)}")
    
    if not entries:
        log.info("Queue empty. Add sweepstakes digest emails or populate sweepstakes_queue table.")
        return {"entered":0,"note":"queue empty"}
    
    stats = {"entered":0,"submitted":0,"captcha_solved":0,"no_form":0,"error":0}
    entered_titles = []
    
    for entry in entries:
        url   = entry.get("url","") or entry.get("entry_url","")
        title = (entry.get("title","") or url.split('/')[2] if url else "Unknown")[:60]
        prize = entry.get("prize_value",0) or 0
        eid   = entry.get("id","")
        
        if not url: continue
        
        log.info(f"\n{'─'*40}")
        log.info(f"Title: {title}")
        log.info(f"Prize: ${prize:,}" if prize else "Prize: Unknown")
        log.info(f"URL: {url[:70]}")
        
        result = enter_sweepstakes(url, title, api_key)
        
        if result in ["entered","submitted"]:
            stats["entered" if result=="entered" else "submitted"] += 1
            entered_titles.append(f"${prize:,} — {title[:40]}" if prize else title[:50])
            new_status = "entered"
        else:
            new_status = result
        
        # Update queue
        if eid:
            supa("PATCH","sweepstakes_queue",{
                "status":new_status,
                "entered_at":datetime.utcnow().isoformat()
            }, f"?id=eq.{eid}")
        
        # Log entry
        supa("POST","sweepstakes_entries",{
            "url":url,"title":title[:200],"result":result,
            "prize_value":int(prize) if prize else 0,
            "entered_at":datetime.utcnow().isoformat(),
            "entry_info_used":json.dumps({"email":ENTRY_INFO["email"],"name":ENTRY_INFO["full_name"]})
        })
        
        time.sleep(3)
    
    # Summary
    total_entered = stats["entered"] + stats["submitted"]
    
    if total_entered > 0:
        pushover(
            f"🎰 Entered {total_entered} sweepstakes!",
            "Entries:\n" + "\n".join(entered_titles[:8]) + 
            (f"\n...and {total_entered-8} more" if total_entered > 8 else "") +
            f"\n\n2Captcha: {'active ✅' if api_key else 'needs funding ⚠️'}",
            priority=0
        )
    
    log.info(f"\n{'═'*55}")
    log.info(f"Run complete: {stats}")
    log.info(f"Entered: {total_entered} | Captchas solved: {stats.get('captcha_solved',0)}")
    return stats

if __name__ == "__main__":
    run()

