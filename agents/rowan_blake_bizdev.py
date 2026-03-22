#!/usr/bin/env python3
"""
Rowan Blake — Business Development Director\nAgentic Super-intelligence for growth channels.\nAutonomous: Scan partnerships → Track affiliate approvals → Identify new channels → Model deal economics
"""
import os, sys, json, logging, urllib.request, urllib.parse, time, base64
from datetime import datetime, date, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s, u, **k): return ""
    def claude_json(s, u, **k): return {}

log = logging.getLogger("rowan")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ROWAN] %(message)s")

ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL  = os.environ.get("SUPABASE_URL", "")
SUPA_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
GH_PAT    = os.environ.get("GH_PAT", "")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY", "")
REPO      = "nyspotlightreport/sct-agency-bots"

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def push(title, msg, p=0):
    if not PUSH_API: return
    try: urllib.request.urlopen("https://api.pushover.net/1/messages.json",
        urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title[:100],"message":msg[:1000],"priority":p}).encode(), timeout=5)
    except: pass

def gh(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        method=method, headers={"Authorization":f"token {GH_PAT}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read())
    except: return None

def save_output(director, otype, content, metrics=None):
    supa("POST", "director_outputs", {"director": director, "output_type": otype,
        "content": str(content)[:2000], "metrics": json.dumps(metrics) if metrics else None,
        "created_at": datetime.utcnow().isoformat()})

def save_to_repo(path, content, msg):
    payload = base64.b64encode(content.encode()).decode()
    existing = gh(f"contents/{path}")
    body = {"message": msg, "content": payload}
    if existing and isinstance(existing, dict) and "sha" in existing:
        body["sha"] = existing["sha"]
    gh(f"contents/{path}", "PUT", body)

SYSTEM = """You are Rowan Blake, BizDev Director. Agentic Super-intelligence. Mental models: Thiel network effects, Metcalfe network value, Ansoff growth matrix, Blue Ocean strategy. Relationships without revenue are hobbies.

Current date: """ + datetime.utcnow().strftime("%Y-%m-%d") + """
MANDATORY: Every output must contain specific dollar amounts, specific actions, and specific timelines.
Revenue target: Day 30 $80-350, Day 60 $300-1,100, Day 90 $900-3,200, Month 12 $2,400-10k/mo.
Offers: ProFlow AI $97/mo, Growth $297/mo, DFY Setup $1,497, DFY Agency $4,997.
CASHFLOW IS KING."""


APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")

def scan_partnership_opportunities():
    """Identify high-value partnership targets using Apollo."""
    opportunities = []
    if APOLLO_KEY:
        try:
            data = json.dumps({"q_organization_keyword_tags":["ai agency","content automation","marketing automation"],
                "page":1,"per_page":10,"organization_num_employees_ranges":["11,50","51,200"]}).encode()
            req = urllib.request.Request("https://api.apollo.io/api/v1/mixed_companies/search",
                data=data, headers={"Content-Type":"application/json","X-Api-Key":APOLLO_KEY})
            with urllib.request.urlopen(req, timeout=15) as r:
                results = json.loads(r.read())
                for org in results.get("organizations", [])[:5]:
                    opportunities.append({"name": org.get("name",""), "domain": org.get("primary_domain",""),
                        "employees": org.get("estimated_num_employees",0), "industry": org.get("industry","")})
        except Exception as e: log.warning(f"Apollo: {e}")
    return opportunities

def track_affiliate_status():
    """Check affiliate program application statuses."""
    affiliates = supa("GET", "affiliate_programs", query="?select=program_name,status,applied_at&order=applied_at.desc") or []
    return {"total": len(affiliates) if isinstance(affiliates, list) else 0,
            "approved": len([a for a in (affiliates if isinstance(affiliates, list) else []) if isinstance(a,dict) and a.get("status")=="approved"]),
            "pending": len([a for a in (affiliates if isinstance(affiliates, list) else []) if isinstance(a,dict) and "pending" in str(a.get("status",""))])}

def run():
    log.info("ROWAN BLAKE — BizDev Director — Activating")
    partners = scan_partnership_opportunities()
    affiliates = track_affiliate_status()
    log.info(f"Partners found: {len(partners)}, Affiliates: {json.dumps(affiliates)}")
    
    plan = claude(SYSTEM,
        f"DAILY BIZDEV INTELLIGENCE\nPartnership targets: {json.dumps(partners[:3])}\n"
        f"Affiliate status: {json.dumps(affiliates)}\n"
        f"Current channels: Apollo outreach, affiliate programs, content partnerships\n\n"
        f"Deliver:\n1. Top partnership to pursue TODAY with specific outreach message\n"
        f"2. Affiliate follow-up actions (which programs to check on)\n"
        f"3. One new revenue channel to test this week\n"
        f"4. Deal economics: projected revenue from top 3 opportunities",
        max_tokens=600) or "API needed"
    
    save_output("Rowan Blake", "daily_bizdev", plan, {"partners": len(partners), **affiliates})
    push("Rowan Blake | BizDev", plan[:300])
    log.info(f"\n{plan}")
    return plan


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
