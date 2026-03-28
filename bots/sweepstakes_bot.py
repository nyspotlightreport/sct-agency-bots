# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
🎰 NYSR Sweepstakes Hunter Bot v2.0
Scans 15+ sources every hour, auto-enters all free sweepstakes/giveaways/contests/grants
Part of the ProFlow / NYSR passive income stack
"""
import os, json, time, sqlite3, logging, hashlib, re, smtplib
import requests, feedparser
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger("SweepBot")

# AG-NUCLEAR-GMAIL-ZERO-20260328: EMAIL       = os.environ.get("GMAIL_USER", "nyspotlightreport@gmail.com")
# AG-NUCLEAR-GMAIL-ZERO-20260328: EMAIL_PASS  = os.environ.get("GMAIL_APP_PASS", "")
NOTIFY      = os.environ.get("CHAIRMAN_EMAIL", EMAIL)
NAME        = os.environ.get("ENTRY_NAME", "S.C. Thomas")
ENTRY_EMAIL = os.environ.get("SWEEPS_EMAIL", EMAIL)
ZIP_CODE    = os.environ.get("ENTRY_ZIP", "11727")
DB_PATH     = "data/sweepstakes.db"
MAX_PER_RUN = 300

RSS_SOURCES = [
    ("https://www.sweepstakesbible.com/feed","Sweepstakes Bible"),
    ("https://www.contestgirl.com/feed/","Contest Girl"),
    ("https://www.sweetiesweeps.com/feed/","Sweetie Sweeps"),
    ("https://contestqueen.com/feed/","Contest Queen"),
    ("https://www.sweepstakeslovers.com/feed/","Sweepstakes Lovers"),
    ("https://www.contestchest.com/feed/","Contest Chest"),
    ("https://www.ilovegiveaways.com/feed/","I Love Giveaways"),
    ("https://theprizefinder.com/feed/","The Prize Finder"),
    ("https://www.competitiondatabase.co.uk/feed/","Competition Database"),
    ("https://nationalcompetitions.co.uk/feed/","National Competitions"),
    ("https://www.sweepstakesadvantage.com/feed/","Sweepstakes Advantage"),
    ("https://www.findabetterway.net/feed/","Find A Better Way"),
    ("https://www.nancysweeps.com/feed/","Nancy Sweeps"),
    ("https://www.freebieshark.com/feed/","Freebie Shark"),
    ("https://slickdeals.net/newsearch.php?mode=frontpage&searchtype=4&rss=1","Slickdeals Freebies"),
]

SCRAPE_SOURCES = [
    ("https://www.reddit.com/r/sweepstakes/new.json?limit=50","Reddit Sweepstakes","reddit"),
    ("https://www.reddit.com/r/giveaways/new.json?limit=50","Reddit Giveaways","reddit"),
    ("https://www.reddit.com/r/Contests/new.json?limit=50","Reddit Contests","reddit"),
]

PRIZE_SCORE = {
    "cash":100,"$":50,"gift card":60,"visa":70,"amazon":50,"car":250,"vacation":200,
    "trip":180,"laptop":90,"iphone":80,"macbook":100,"tv":60,"electronics":50,
    "grant":300,"scholarship":200,"prize":30,"win":10,"free":10,"giveaway":20,
}

HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}

def init_db():
    os.makedirs("data", exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS sweepstakes(
        id TEXT PRIMARY KEY, title TEXT, url TEXT, source TEXT,
        found_at TEXT, entered_at TEXT, method TEXT,
        score INTEGER DEFAULT 0, status TEXT DEFAULT 'pending', notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS entries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sweep_id TEXT, ts TEXT, method TEXT, success INTEGER, resp TEXT)""")
    c.commit()
    return c

def score(text):
    t = text.lower()
    s = sum(v for k,v in PRIZE_SCORE.items() if k in t)
    for m in re.findall(r'\$[\d,]+', t):
        try: s += min(int(m.replace('$','').replace(',',''))//100, 500)
        except Exception:  # noqa: bare-except

            pass
    return s

def uid(url): return hashlib.md5(url.encode()).hexdigest()[:14]

def fetch_rss():
    items = []
    for url, name in RSS_SOURCES:
        try:
            f = feedparser.parse(url)
            for e in f.entries[:40]:
                link = getattr(e,'link','')
                title = getattr(e,'title','')
                desc = getattr(e,'summary','')
                if link:
                    items.append({'id':uid(link),'title':title,'url':link,'source':name,
                                  'score':score(title+' '+desc)})
            log.info(f"RSS {name}: {len(f.entries)} found")
        except Exception as ex:
            log.warning(f"RSS {name} failed: {ex}")
    return items

def fetch_reddit():
    items = []
    for url, name, _ in SCRAPE_SOURCES:
        try:
            r = requests.get(url, headers={**HEADERS,'Accept':'application/json'}, timeout=8)
            posts = r.json().get('data',{}).get('children',[])
            for p in posts:
                d = p.get('data',{})
                link = d.get('url','')
                title = d.get('title','')
                if link and ('http' in link):
                    items.append({'id':uid(link),'title':title,'url':link,'source':name,'score':score(title)})
        except Exception as ex:
            log.warning(f"Reddit {name} failed: {ex}")
    return items

def try_entry(url, title):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find all forms with email fields
        for form in soup.find_all('form'):
            inputs = form.find_all('input')
            email_fields = [i for i in inputs if
                i.get('type','').lower()=='email' or
                'email' in i.get('name','').lower() or
                'email' in i.get('placeholder','').lower()]
            if not email_fields: continue
            action = form.get('action', url)
            if not action.startswith('http'): action = urljoin(url, action)
            method = form.get('method','post').lower()
            data = {}
            for inp in inputs:
                n = inp.get('name','')
                if not n: continue
                t = inp.get('type','text').lower()
                if t in ('submit','button','image'): continue
                if t == 'hidden': data[n] = inp.get('value','')
                elif t=='email' or 'email' in n.lower(): data[n] = ENTRY_EMAIL
                elif 'first' in n.lower(): data[n] = NAME.split()[0]
                elif 'last' in n.lower(): data[n] = NAME.split()[-1]
                elif 'name' in n.lower(): data[n] = NAME
                elif 'zip' in n.lower() or 'postal' in n.lower(): data[n] = ZIP_CODE
                else: data[n] = inp.get('value','')
            if ENTRY_EMAIL in data.values():
                fn = requests.post if method=='post' else requests.get
                kw = {'data':data} if method=='post' else {'params':data}
                r2 = fn(action, headers=HEADERS, timeout=10, **kw)
                return True, f"form-{method}", f"{r2.status_code}"
        return False, "no-form", ""
    except Exception as e:
        return False, "error", str(e)[:80]

def run():
    c = init_db()
    all_items = fetch_rss() + fetch_reddit()
    log.info(f"Total found: {len(all_items)}")
    # Save new
    new = 0
    for item in all_items:
        if not c.execute("SELECT 1 FROM sweepstakes WHERE id=?",(item['id'],)).fetchone():
            c.execute("INSERT INTO sweepstakes(id,title,url,source,found_at,score) VALUES(?,?,?,?,?,?)",
                (item['id'],item['title'],item['url'],item['source'],datetime.now().isoformat(),item['score']))
            new += 1
    c.commit()
    log.info(f"New sweepstakes saved: {new}")
    # Enter pending, highest score first
    pending = c.execute(
        "SELECT id,title,url,score FROM sweepstakes WHERE status='pending' ORDER BY score DESC LIMIT ?",
        (MAX_PER_RUN,)).fetchall()
    entered = 0
    for sid, title, url, sc in pending:
        ok, method, resp = try_entry(url, title)
        c.execute("UPDATE sweepstakes SET entered_at=?,method=?,status=? WHERE id=?",
            (datetime.now().isoformat(), method, 'entered' if ok else 'attempted', sid))
        c.execute("INSERT INTO entries(sweep_id,ts,method,success,resp) VALUES(?,?,?,?,?)",
            (sid, datetime.now().isoformat(), method, int(ok), resp))
        if ok: entered += 1
        time.sleep(0.3)
    c.commit()
    log.info(f"✅ Entered: {entered}/{len(pending)}")
    # Stats
    total = c.execute("SELECT COUNT(*) FROM sweepstakes").fetchone()[0]
    total_entered = c.execute("SELECT COUNT(*) FROM sweepstakes WHERE status='entered'").fetchone()[0]
    log.info(f"📊 DB: {total} total, {total_entered} entered")
    # Send daily digest at midnight
    if datetime.now().hour == 0 and EMAIL_PASS:
        top = c.execute(
            "SELECT title,url,score FROM sweepstakes WHERE status IN ('pending','attempted') ORDER BY score DESC LIMIT 30"
        ).fetchall()
        rows = "".join(f"<tr><td>{r[0][:70]}</td><td>${r[2]}</td><td><a href='{r[1]}'>Enter</a></td></tr>" for r in top)
        body = f"""<h2>🎰 Sweepstakes Bot Report — {datetime.now().strftime('%b %d %Y')}</h2>
<p>Auto-entered today: <strong>{entered}</strong> | Total in DB: {total} | Total entered ever: {total_entered}</p>
<h3>Top Pending (enter manually for best odds):</h3>
<table border='1' cellpadding='6'><tr><th>Title</th><th>Score</th><th>Link</th></tr>{rows}</table>"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🎰 Sweeps: {entered} auto-entered | {total} tracked"
        msg['From'], msg['To'] = EMAIL, NOTIFY
        msg.attach(MIMEText(body, 'html'))
        try:
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP('[GMAIL-SMTP-REDACTED]', 587) as s:
# AG-NUCLEAR-GMAIL-ZERO-20260328:                 s.starttls(); s.login(EMAIL, EMAIL_PASS); s.send_message(msg)
            log.info("📧 Digest sent")
        except Exception as e:
            log.warning(f"Email failed: {e}")
    c.close()

if __name__ == "__main__":
    run()
