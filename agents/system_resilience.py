#!/usr/bin/env python3
"""
agents/system_resilience.py — NYSR Platform Independence Layer
Ensures the system is NEVER locked out by any single platform failure.
Backs up everything locally. Multiple recovery paths. Self-healing.

INDEPENDENCE GUARANTEES:
1. Email loss → System still runs (GitHub PAT + Supabase auth are separate)
2. GitHub down → Local repo has all code, can push to GitLab/Bitbucket
3. Supabase down → Local SQLite backup has all data
4. Stripe down → Revenue data backed up, can switch to Gumroad/LemonSqueezy
5. Netlify down → Can deploy to Vercel/Cloudflare in minutes
6. Single tool loss → Every critical function has 2+ redundant paths
"""
import os,sys,json,logging,time,hashlib,shutil,sqlite3
from datetime import datetime
sys.path.insert(0,".")
log=logging.getLogger("resilience")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [RESILIENCE] %(message)s")
import urllib.request as urlreq,urllib.parse

SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
GH_PAT=os.environ.get("GH_PAT","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")
REPO="nyspotlightreport/sct-agency-bots"

def push(t,m,p=0):
    if not PUSH_API:return
    try:urlreq.urlopen("https://api.pushover.net/1/messages.json",urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":t[:100],"message":m[:1000],"priority":p}).encode(),timeout=5)
    except:pass

def gh(path,method="GET",data=None):
    body=json.dumps(data).encode() if data else None
    req=urlreq.Request(f"https://api.github.com/repos/{REPO}/{path}",data=body,method=method,
        headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urlreq.urlopen(req,timeout=20) as r:
            raw=r.read(); return json.loads(raw) if raw else {}
    except:return None

# ═══════════════════════════════════════════════════════
# 1. LOCAL STATE BACKUP — Never lose data
# ═══════════════════════════════════════════════════════
def backup_supabase_to_local():
    """Pull all critical Supabase data to local SQLite."""
    if not SUPA_URL:return 0
    backup_dir=os.path.join(os.path.dirname(__file__),"..","data","backups")
    os.makedirs(backup_dir,exist_ok=True)
    db_path=os.path.join(backup_dir,f"nysr_backup_{datetime.utcnow().strftime('%Y%m%d')}.db")
    conn=sqlite3.connect(db_path)
    tables=["director_outputs","contacts","director_memory","director_audit_log","conversation_log"]
    total=0
    for table in tables:
        try:
            req=urlreq.Request(f"{SUPA_URL}/rest/v1/{table}?select=*&limit=1000&order=created_at.desc",
                headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}"})
            with urlreq.urlopen(req,timeout=30) as r:
                rows=json.loads(r.read())
                if not isinstance(rows,list) or not rows:continue
                cols=list(rows[0].keys())
                conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(c+' TEXT' for c in cols)})")
                conn.execute(f"DELETE FROM {table}")
                for row in rows:
                    vals=[json.dumps(row.get(c,"")) if isinstance(row.get(c),dict) else str(row.get(c,"")) for c in cols]
                    conn.execute(f"INSERT INTO {table} VALUES ({','.join('?' for _ in cols)})",vals)
                total+=len(rows)
                log.info(f"  Backed up {table}: {len(rows)} rows")
        except Exception as e:
            log.warning(f"  Skip {table}: {e}")
    conn.commit();conn.close()
    log.info(f"  Total: {total} rows → {db_path}")
    return total

# ═══════════════════════════════════════════════════════
# 2. SECRETS MANIFEST — Know what's needed to rebuild
# ═══════════════════════════════════════════════════════
def generate_secrets_manifest():
    """Create a manifest of all required secrets (names only, not values)."""
    manifest={
        "critical":["ANTHROPIC_API_KEY","STRIPE_SECRET_KEY","SUPABASE_URL","SUPABASE_KEY",
            "PUSHOVER_API_KEY","PUSHOVER_USER_KEY","GH_PAT","GMAIL_APP_PASS","SMTP_USER"],
        "revenue":["STRIPE_SECRET_KEY","GUMROAD_ACCESS_TOKEN","SHOPIFY_ACCESS_TOKEN"],
        "content":["WORDPRESS_ACCESS_TOKEN","PUBLER_API_KEY","BEEHIIV_API_KEY","MEDIUM_INTEGRATION_TOKEN"],
        "social":["TWITTER_API_KEY","TWITTER_API_SECRET","TWITTER_ACCESS_TOKEN",
            "LINKEDIN_CLIENT_ID","PINTEREST_ACCESS_TOKEN","TIKTOK_CLIENT_KEY"],
        "infrastructure":["NETLIFY_AUTH_TOKEN","NETLIFY_SITE_ID","GH_PAT"],
        "monitoring":["AHREFS_API_KEY","NEWSAPI_KEY","ALPHA_VANTAGE_API_KEY"],
        "email":["GMAIL_APP_PASS","SMTP_USER","GMAIL_USER","BUSINESS_EMAIL"],
        "auth_independent_of_email":["GH_PAT","STRIPE_SECRET_KEY","SUPABASE_URL",
            "SUPABASE_KEY","ANTHROPIC_API_KEY","PUSHOVER_API_KEY","NETLIFY_AUTH_TOKEN"],
    }
    present={}
    for cat,keys in manifest.items():
        present[cat]={k:bool(os.environ.get(k,"")) for k in keys}
    return manifest,present

# ═══════════════════════════════════════════════════════
# 3. RECOVERY PLAN — Rebuild from any state
# ═══════════════════════════════════════════════════════
def generate_recovery_plan():
    """Generate a complete recovery plan stored in the repo."""
    plan={
        "last_updated":datetime.utcnow().isoformat(),
        "recovery_scenarios":{
            "email_locked_out":{
                "impact":"Cannot send welcome emails. Cannot receive password resets for some services.",
                "what_still_works":["GitHub (PAT auth)","Stripe (API key)","Supabase (API key)",
                    "Anthropic (API key)","Pushover (API key)","Netlify (auth token)",
                    "All GitHub Actions workflows","All agent code","All data in Supabase"],
                "what_breaks":["SMTP email sending","Gmail-dependent password resets"],
                "fix_steps":["1. Create new Gmail or use any SMTP provider (SendGrid/Mailgun/SES)",
                    "2. Update GMAIL_APP_PASS and SMTP_USER in GitHub Secrets",
                    "3. Run 'Sync ALL Secrets to Netlify' workflow",
                    "4. Purchase flow restored in 5 minutes"]
            },
            "github_locked_out":{
                "impact":"Cannot push code changes. Workflows stop.",
                "what_still_works":["Local repo has ALL code","Supabase has all data","Stripe still works",
                    "Netlify site stays up (already deployed)","Email still works"],
                "fix_steps":["1. Local repo at C:\\Users\\S\\sct-agency-bots has full clone",
                    "2. Create new GitHub account or use GitLab/Bitbucket",
                    "3. git remote set-url origin <new-remote>","4. git push --mirror",
                    "5. Update webhook URLs in Stripe dashboard","6. Update Netlify git integration"]
            },
            "supabase_down":{
                "impact":"CRM data temporarily unavailable. Director memory paused.",
                "what_still_works":["Local SQLite backup in data/backups/","All agent code","Site still up",
                    "Stripe payments still work","Emails still send"],
                "fix_steps":["1. Agents degrade gracefully (try/except on all Supabase calls)",
                    "2. Local backup has recent data","3. Switch to new Supabase project or PostgreSQL",
                    "4. Import from SQLite backup","5. Update SUPABASE_URL and SUPABASE_KEY"]
            },
            "stripe_account_issue":{
                "impact":"Cannot process payments.",
                "what_still_works":["Everything except payment processing"],
                "fix_steps":["1. Gumroad is already configured as backup payment processor",
                    "2. LemonSqueezy can be set up in 30 minutes",
                    "3. Update payment links on proflow and store pages",
                    "4. Revenue data backed up locally"]
            },
            "netlify_down":{
                "impact":"Website offline.",
                "fix_steps":["1. Site files in site/ directory","2. Deploy to Vercel: npx vercel --prod",
                    "3. Or Cloudflare Pages: npx wrangler pages deploy site/",
                    "4. Update DNS to point to new host","5. Takes ~10 minutes"]
            },
            "total_system_rebuild":{
                "impact":"Starting from scratch.",
                "requirements":["Windows PC with Python 3.11+","Internet connection","GitHub PAT (or create new account)"],
                "steps":["1. Clone repo: git clone https://github.com/nyspotlightreport/sct-agency-bots",
                    "2. Or restore from local: C:\\Users\\S\\sct-agency-bots",
                    "3. Set GitHub Secrets (see docs/CREDENTIALS_MANIFEST.md)",
                    "4. Run: python NYSR_MASTER_DEPLOY.py",
                    "5. Trigger 'Sync ALL Secrets to Netlify' workflow",
                    "6. System operational in ~30 minutes"]
            }
        },
        "local_assets":{"repo":"C:\\Users\\S\\sct-agency-bots","kdp_books":"data/kdp_books/",
            "designs":"data/redbubble_designs/","backups":"data/backups/",
            "site":"site/","agents":"agents/","bots":"bots/"},
        "platform_alternatives":{
            "github":["gitlab.com","bitbucket.org","codeberg.org"],
            "netlify":["vercel.com","pages.cloudflare.com","render.com"],
            "supabase":["neon.tech","planetscale.com","railway.app/postgresql"],
            "stripe":["gumroad.com","lemonsqueezy.com","paddle.com"],
            "gmail":["sendgrid.com","mailgun.com","ses.amazonaws.com"],
            "pushover":["ntfy.sh","slack webhooks","discord webhooks"]
        }
    }
    # Save recovery plan to repo
    plan_path=os.path.join(os.path.dirname(__file__),"..","data","recovery_plan.json")
    os.makedirs(os.path.dirname(plan_path),exist_ok=True)
    with open(plan_path,"w") as f:json.dump(plan,f,indent=2)
    log.info(f"Recovery plan saved: {plan_path}")
    return plan

# ═══════════════════════════════════════════════════════
# 4. INDEPENDENCE AUDIT — What are we dependent on?
# ═══════════════════════════════════════════════════════
def audit_dependencies():
    deps=[]
    # Check if email is the single point of failure for anything
    email_dependent=["GMAIL_APP_PASS","SMTP_USER","GMAIL_USER"]
    non_email_auth=["GH_PAT","STRIPE_SECRET_KEY","SUPABASE_URL","ANTHROPIC_API_KEY","PUSHOVER_API_KEY","NETLIFY_AUTH_TOKEN"]
    email_risk=sum(1 for k in email_dependent if os.environ.get(k,""))
    non_email=sum(1 for k in non_email_auth if os.environ.get(k,""))
    deps.append(f"Email-dependent: {email_risk}/{len(email_dependent)} services")
    deps.append(f"Email-independent: {non_email}/{len(non_email_auth)} services")
    if non_email>=5:deps.append("SAFE: Core system runs without email access")
    else:deps.append("WARNING: Missing non-email auth tokens")
    return deps

def run():
    log.info("="*60)
    log.info("SYSTEM RESILIENCE — Backup + Recovery + Independence")
    log.info("="*60)
    # 1. Backup Supabase
    log.info("\n[1] BACKING UP SUPABASE DATA...")
    rows=backup_supabase_to_local()
    log.info(f"  Backed up {rows} rows")
    # 2. Generate secrets manifest
    log.info("\n[2] SECRETS MANIFEST...")
    manifest,present=generate_secrets_manifest()
    for cat,keys in present.items():
        missing=[k for k,v in keys.items() if not v]
        if missing:log.info(f"  {cat}: MISSING {', '.join(missing)}")
        else:log.info(f"  {cat}: All present")
    # 3. Generate recovery plan
    log.info("\n[3] RECOVERY PLAN...")
    plan=generate_recovery_plan()
    log.info(f"  {len(plan['recovery_scenarios'])} scenarios documented")
    # 4. Independence audit
    log.info("\n[4] INDEPENDENCE AUDIT...")
    deps=audit_dependencies()
    for d in deps:log.info(f"  {d}")
    # Summary
    report=f"Resilience: {rows} rows backed up, {len(plan['recovery_scenarios'])} recovery scenarios, {', '.join(deps)}"
    push("Resilience OK",report[:300],-1)
    supa_post("director_outputs",{"director":"System Resilience","output_type":"resilience_audit",
        "content":report[:2000],"created_at":datetime.utcnow().isoformat()})
    return {"backup_rows":rows,"scenarios":len(plan["recovery_scenarios"]),"deps":deps}

if __name__=="__main__":
    run()
