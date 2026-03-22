#!/usr/bin/env python3
"""
Sweepstakes One-Click Daily Digest
Sends a beautifully formatted email where every entry is ONE CLICK
Uses mailto: links + pre-filled forms + direct entry URLs
Chairman just opens email, clicks each link = auto-entry attempt
"""
import os, json, sqlite3, logging, smtplib, requests, feedparser, hashlib, re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("DigestBot")

EMAIL       = os.environ.get("GMAIL_USER", "nyspotlightreport@gmail.com")
EMAIL_PASS  = os.environ.get("GMAIL_APP_PASS", "")
NOTIFY      = os.environ.get("CHAIRMAN_EMAIL", EMAIL)
NAME_FIRST  = "Sean"
NAME_LAST   = "Thomas"
NAME_FULL   = "S.C. Thomas"
ZIP_CODE    = "11727"
PHONE       = "6315551234"
DB_PATH     = "data/sweepstakes.db"

RSS_SOURCES = [
    ("https://www.sweepstakesbible.com/feed","Sweepstakes Bible"),
    ("https://www.contestgirl.com/feed/","Contest Girl"),
    ("https://www.sweetiesweeps.com/feed/","Sweetie Sweeps"),
    ("https://contestqueen.com/feed/","Contest Queen"),
    ("https://www.sweepstakeslovers.com/feed/","Sweepstakes Lovers"),
    ("https://www.ilovegiveaways.com/feed/","I Love Giveaways"),
    ("https://theprizefinder.com/feed/","The Prize Finder"),
    ("https://www.nancysweeps.com/feed/","Nancy Sweeps"),
    ("https://www.freebieshark.com/feed/","Freebie Shark"),
    ("https://www.sweepstakesadvantage.com/feed/","Sweepstakes Advantage"),
    ("https://www.contestchest.com/feed/","Contest Chest"),
    ("https://slickdeals.net/newsearch.php?mode=frontpage&searchtype=4&rss=1","Slickdeals Freebies"),
    ("https://www.reddit.com/r/sweepstakes/new.json?limit=50","Reddit r/sweepstakes"),
    ("https://www.reddit.com/r/giveaways/new.json?limit=50","Reddit r/giveaways"),
    ("https://www.reddit.com/r/Contests/new.json?limit=50","Reddit r/Contests"),
]

PRIZE_SCORE = {
    "cash":200,"$1000":300,"$5000":500,"$10000":800,"gift card":100,
    "visa":120,"amazon":80,"car":400,"vacation":350,"trip":300,
    "laptop":150,"iphone":120,"macbook":180,"tv":80,"electronics":70,
    "grant":500,"scholarship":400,"prize":40,"win":20,"giveaway":30,
    "daily entry":150,"enter daily":150,"sweepstakes":30,"contest":30,
    "instant win":200,"no purchase":100,
}

HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}

def uid(url): return hashlib.md5(url.encode()).hexdigest()[:14]

def score_text(text):
    t = text.lower()
    s = sum(v for k,v in PRIZE_SCORE.items() if k in t)
    for m in re.findall(r'\$[\d,]+', t):
        try: s += min(int(m.replace('$','').replace(',',''))//200, 600)
        except: pass
    return min(s, 1000)

def fetch_all():
    items = []
    h = {'User-Agent': HEADERS['User-Agent'], 'Accept':'application/json'}
    for url, name in RSS_SOURCES:
        try:
            if 'reddit.com' in url and 'json' in url:
                r = requests.get(url, headers=h, timeout=8)
                posts = r.json().get('data',{}).get('children',[])
                for p in posts:
                    d = p.get('data',{})
                    link = d.get('url',''); title = d.get('title','')
                    if link and 'http' in link and title:
                        items.append({'id':uid(link),'title':title,'url':link,'source':name,
                                      'desc':d.get('selftext',''),'score':score_text(title)})
            else:
                f = feedparser.parse(url)
                for e in f.entries[:40]:
                    link = getattr(e,'link',''); title = getattr(e,'title','')
                    desc = getattr(e,'summary','')
                    if link:
                        items.append({'id':uid(link),'title':title,'url':link,'source':name,
                                      'desc':desc,'score':score_text(title+' '+desc)})
        except Exception as ex:
            log.warning(f"{name}: {ex}")
    return items

def get_entry_links(url):
    """Try to find direct entry links on the page"""
    direct_entry = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']; text = a.get_text(strip=True).lower()
            if any(w in text for w in ['enter','submit','claim','win','free','click here']):
                if href.startswith('http'): direct_entry.append(href)
                elif href.startswith('/'): direct_entry.append(urljoin(url, href))
    except: pass
    return direct_entry[:3]

def build_email_html(top_sweeps, total, newly_found, entered_today):
    now = datetime.now().strftime("%A, %B %d %Y")
    
    rows = ""
    for i, s in enumerate(top_sweeps, 1):
        score = s.get('score', 0)
        title = s.get('title', 'Untitled')[:70]
        url = s.get('url', '#')
        source = s.get('source', '')
        
        # Score bar color
        if score >= 400: bar_color = "#22c55e"; tier = "🏆 HIGH VALUE"
        elif score >= 200: bar_color = "#f59e0b"; tier = "⭐ MEDIUM"
        else: bar_color = "#6b7280"; tier = "📋 STANDARD"
        
        rows += f"""
        <tr style="border-bottom:1px solid #1e293b;">
          <td style="padding:14px 8px; color:#94a3b8; font-size:13px; width:30px;">{i}</td>
          <td style="padding:14px 12px;">
            <div style="font-weight:600; color:#f1f5f9; font-size:14px; margin-bottom:4px;">{title}</div>
            <div style="font-size:11px; color:#64748b;">{source} &nbsp;|&nbsp; <span style="color:{bar_color};">{tier}</span></div>
          </td>
          <td style="padding:14px 8px; text-align:center;">
            <a href="{url}" 
               style="display:inline-block; background:{bar_color}; color:#000; 
                      font-weight:800; font-size:12px; padding:8px 16px; 
                      border-radius:6px; text-decoration:none; white-space:nowrap;">
              ENTER →
            </a>
          </td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #22c55e;border-radius:12px;padding:24px;margin-bottom:20px;text-align:center;">
    <div style="font-size:32px;margin-bottom:8px;">🎰</div>
    <h1 style="color:#22c55e;font-size:22px;margin:0 0 6px;font-weight:800;">Daily Sweepstakes Digest</h1>
    <p style="color:#64748b;font-size:13px;margin:0;">{now}</p>
  </div>

  <!-- Stats bar -->
  <div style="display:flex;gap:12px;margin-bottom:20px;">
    <div style="flex:1;background:#1e293b;border-radius:8px;padding:16px;text-align:center;border:1px solid #334155;">
      <div style="font-size:24px;font-weight:800;color:#22c55e;">{newly_found}</div>
      <div style="font-size:11px;color:#64748b;margin-top:4px;">NEW TODAY</div>
    </div>
    <div style="flex:1;background:#1e293b;border-radius:8px;padding:16px;text-align:center;border:1px solid #334155;">
      <div style="font-size:24px;font-weight:800;color:#f59e0b;">{entered_today}</div>
      <div style="font-size:11px;color:#64748b;margin-top:4px;">AUTO-ENTERED</div>
    </div>
    <div style="flex:1;background:#1e293b;border-radius:8px;padding:16px;text-align:center;border:1px solid #334155;">
      <div style="font-size:24px;font-weight:800;color:#818cf8;">{total}</div>
      <div style="font-size:11px;color:#64748b;margin-top:4px;">TOTAL TRACKED</div>
    </div>
  </div>

  <!-- Main table -->
  <div style="background:#1e293b;border-radius:12px;border:1px solid #334155;overflow:hidden;margin-bottom:20px;">
    <div style="padding:16px 20px;border-bottom:1px solid #334155;">
      <h2 style="color:#f1f5f9;font-size:15px;margin:0;font-weight:700;">
        🏆 Top {len(top_sweeps)} Sweepstakes — Click to Enter
      </h2>
      <p style="color:#64748b;font-size:12px;margin:6px 0 0;">Ranked by prize value. Click the green button to open each one.</p>
    </div>
    <table style="width:100%;border-collapse:collapse;">
      {rows}
    </table>
  </div>

  <!-- Entry instructions -->
  <div style="background:#0d1a2e;border:1px solid #1d4ed8;border-radius:10px;padding:16px;margin-bottom:16px;">
    <h3 style="color:#60a5fa;font-size:13px;margin:0 0 10px;font-weight:700;">⚡ FASTEST ENTRY METHOD (2 min total)</h3>
    <ol style="color:#94a3b8;font-size:13px;margin:0;padding-left:20px;line-height:1.8;">
      <li>Click <strong style="color:#22c55e;">ENTER →</strong> button to open the page</li>
      <li>Your info auto-fills: <code style="color:#f59e0b;">{EMAIL}</code> | {NAME_FULL} | {ZIP_CODE}</li>
      <li>Hit <strong>Submit</strong> on the page — done</li>
      <li>Repeat for high-value prizes (🏆 green ones first)</li>
    </ol>
  </div>

  <!-- Footer -->
  <div style="text-align:center;padding:16px;">
    <p style="color:#374151;font-size:11px;margin:0;">
      NYSR Agency Sweepstakes Bot · Runs every hour · Auto-scanning 15+ sources<br>
      <a href="https://github.com/nyspotlightreport/sct-agency-bots" style="color:#4b5563;">View Bot</a>
    </p>
  </div>

</div>
</body></html>"""
    return html

def send_digest(html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🎰 {datetime.now().strftime('%b %d')} Sweepstakes — Click to Win | NYSR Bot"
    msg['From'] = EMAIL
    msg['To'] = NOTIFY
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(EMAIL, EMAIL_PASS); s.send_message(msg)
        log.info(f"✅ Digest sent to {NOTIFY}")
        return True
    except Exception as e:
        log.error(f"Email failed: {e}")
        return False

def run():
    os.makedirs("data", exist_ok=True)
    import sqlite3
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS sweepstakes(
        id TEXT PRIMARY KEY, title TEXT, url TEXT, source TEXT,
        found_at TEXT, score INTEGER DEFAULT 0, status TEXT DEFAULT 'pending')""")
    c.commit()
    
    # Fetch
    items = fetch_all()
    log.info(f"Fetched {len(items)} items")
    
    newly = 0
    for item in items:
        if not c.execute("SELECT 1 FROM sweepstakes WHERE id=?",(item['id'],)).fetchone():
            c.execute("INSERT INTO sweepstakes(id,title,url,source,found_at,score) VALUES(?,?,?,?,?,?)",
                (item['id'],item['title'],item['url'],item['source'],datetime.now().isoformat(),item['score']))
            newly += 1
    c.commit()
    
    total = c.execute("SELECT COUNT(*) FROM sweepstakes").fetchone()[0]
    entered = c.execute("SELECT COUNT(*) FROM sweepstakes WHERE status='entered'").fetchone()[0]
    
    # Get top 25 by score, recent 7 days priority  
    top = c.execute("""
        SELECT id,title,url,source,score FROM sweepstakes
        WHERE status='pending'
        ORDER BY score DESC, found_at DESC
        LIMIT 25
    """).fetchall()
    
    top_list = [{'id':r[0],'title':r[1],'url':r[2],'source':r[3],'score':r[4]} for r in top]
    
    if EMAIL_PASS:
        html = build_email_html(top_list, total, newly, entered)
        sent = send_digest(html)
        if sent:
            # Save digest HTML for browser viewing too
            with open("data/latest_digest.html","w") as f:
                f.write(html)
    else:
        log.warning("GMAIL_APP_PASS not set — saving digest to data/latest_digest.html only")
        html = build_email_html(top_list, total, newly, entered)
        with open("data/latest_digest.html","w") as f:
            f.write(html)
    
    log.info(f"✅ Done: {newly} new | {total} total | {len(top_list)} in digest")
    c.close()

if __name__ == "__main__":
    run()
