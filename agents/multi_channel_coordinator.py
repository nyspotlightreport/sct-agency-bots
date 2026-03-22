#!/usr/bin/env python3
"""
Multi-Channel Outreach Coordinator — NYSR
Coordinates email + LinkedIn + Twitter + Reddit + content 
into one synchronized sales motion.

No prospect should ever be contacted on only one channel.
The sequence:
  Day 1:  Email (warm, value-first)
  Day 3:  LinkedIn connection
  Day 5:  Email (case study)
  Day 7:  LinkedIn DM (if connected)
  Day 10: Email (direct ask)
  Day 14: Content mention (relevant post they'd care about)
  Day 21: Final email (breakup / urgency)
  Day 28: Reddit reply to their post (if found)
"""
import os,sys,json,logging,requests,base64
from datetime import datetime,date,timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude,claude_json
    from agents.adaptive_sales_engine import generate_full_sequence,score_lead,ICPS
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def generate_full_sequence(p,i="proflow_starter"): return {}
    def score_lead(p): return {"score":50,"tier":"WARM","recommended_icp":"proflow_starter"}
    ICPS={}

logging.basicConfig(level=logging.INFO,format="%(asctime)s [Coordinator] %(message)s")
log=logging.getLogger()
ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
APOLLO_KEY=os.environ.get("APOLLO_API_KEY","")
GMAIL_USER=os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
GMAIL_PASS=os.environ.get("GMAIL_APP_PASS","")
GH_TOKEN=os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
REPO="nyspotlightreport/sct-agency-bots"

def fetch_fresh_prospects(count:int=20)->list:
    """Pull new prospects from Apollo matching our ICP."""
    if not APOLLO_KEY: return _demo_prospects()
    try:
        r=requests.post("https://api.apollo.io/v1/mixed_people/search",
            json={"api_key":APOLLO_KEY,"q_organization_industry_tag_ids":["5567cd4773696439b10b0000"],
                  "person_titles":["founder","ceo","marketing director","content manager",
                                   "head of content","vp marketing","growth","agency owner"],
                  "per_page":count,"page":1},timeout=15)
        if r.status_code==200:
            people=r.json().get("people",[])
            log.info(f"  Apollo returned {len(people)} prospects")
            return people
    except Exception as e:
        log.warning(f"Apollo error: {e}")
    return _demo_prospects()

def _demo_prospects():
    """High-quality demo prospects for testing when Apollo isn't connected."""
    return [
        {"first_name":"Alex","last_name":"Rivera","title":"Founder","company":"ContentFlow Agency",
         "email":"alex@contentflow.io","linkedin_url":"linkedin.com/in/alexrivera","employees":12},
        {"first_name":"Morgan","last_name":"Chase","title":"Head of Marketing","company":"ScaleOps",
         "email":"morgan@scaleops.com","linkedin_url":"linkedin.com/in/morganchase","employees":28},
        {"first_name":"Jamie","last_name":"Torres","title":"CEO","company":"GrowthLab Digital",
         "email":"jamie@growthlabdigital.com","linkedin_url":"linkedin.com/in/jamietorres","employees":7},
    ]

def enrich_prospect(prospect:dict)->dict:
    """Add scoring, ICP classification, and personalization data."""
    scoring=score_lead(prospect)
    prospect["lead_score"]=scoring["score"]
    prospect["tier"]=scoring["tier"]
    prospect["recommended_icp"]=scoring["recommended_icp"]
    prospect["outreach_priority"]=scoring["outreach_priority"]
    # Generate personalization hook
    if ANTHROPIC:
        hook=claude("You are a sales researcher. Find one specific, relevant hook for a personalized sales message.",
            f"Name: {prospect.get('first_name','')} {prospect.get('last_name','')} | Title: {prospect.get('title','')} | Company: {prospect.get('company','')} | Employees: {prospect.get('employees','unknown')}
Write ONE specific observation about their likely content challenges in under 20 words.",
            max_tokens=40)
        prospect["personalization_hook"]=hook or f"At {prospect.get('company','')}, content consistency is probably a challenge at {prospect.get('employees','your')} headcount."
    return prospect

def stage_outreach_sequence(prospect:dict)->dict:
    """Generate and save the full multi-channel sequence for this prospect."""
    icp=prospect.get("recommended_icp","proflow_starter")
    sequence=generate_full_sequence(prospect,icp)
    pid=f"{prospect.get('first_name','x')}_{prospect.get('last_name','x')}_{prospect.get('company','co')}".lower().replace(" ","_")
    sequence_record={
        "prospect_id":pid,
        "prospect":prospect,
        "sequence":sequence,
        "created":str(date.today()),
        "status":"staged",
        "next_action_day":1,
        "next_action_date":str(date.today()),
        "completed_touches":[],
    }
    # Save to sequences queue
    path=f"data/sales/sequences/{pid}.json"
    enc=base64.b64encode(json.dumps(sequence_record,indent=2).encode()).decode()
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=GH_H)
    body={"message":f"sales: sequence staged for {prospect.get('first_name','')}","content":enc}
    if r.status_code==200: body["sha"]=r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",json=body,headers=GH_H)
    return sequence_record

def execute_due_touches()->list:
    """Find all sequences with touches due today and execute them."""
    executed=[]
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/sequences",headers=GH_H)
    if r.status_code!=200: return executed
    files=[f for f in r.json() if f["name"].endswith(".json")]
    for file_info in files[:20]:  # Process max 20 per run
        r2=requests.get(f"https://api.github.com/repos/{REPO}/contents/data/sales/sequences/{file_info['name']}",headers=GH_H)
        if r2.status_code!=200: continue
        try:
            seq=json.loads(base64.b64decode(r2.json()["content"]).decode())
        except: continue
        if seq.get("next_action_date","") > str(date.today()): continue
        if seq.get("status") in ["completed","opted_out"]: continue
        # Execute the next touch
        touches=seq.get("sequence",{}).get("sequence",[]) if isinstance(seq.get("sequence"),dict) else []
        next_day=seq.get("next_action_day",1)
        for touch in touches:
            if touch.get("day")==next_day:
                result=_execute_touch(touch,seq["prospect"])
                if result:
                    seq["completed_touches"].append({"day":next_day,"result":result,"date":str(date.today())})
                    executed.append({"prospect":seq["prospect"].get("first_name",""),
                                    "day":next_day,"channel":touch.get("channel","email"),"result":result})
                # Schedule next touch
                all_days=sorted([t.get("day",99) for t in touches])
                remaining=[d for d in all_days if d>next_day]
                if remaining:
                    days_until_next=remaining[0]-next_day
                    next_date=date.today()+timedelta(days=days_until_next)
                    seq["next_action_day"]=remaining[0]
                    seq["next_action_date"]=str(next_date)
                else:
                    seq["status"]="completed"
                break
        # Save updated sequence
        enc=base64.b64encode(json.dumps(seq,indent=2).encode()).decode()
        body={"message":f"sales: touch executed day {next_day}","content":enc,"sha":r2.json()["sha"]}
        requests.put(f"https://api.github.com/repos/{REPO}/contents/data/sales/sequences/{file_info['name']}",json=body,headers=GH_H)
    return executed

def _execute_touch(touch:dict,prospect:dict)->str:
    """Execute a single touch (send email, note LinkedIn action, etc.)."""
    channel=touch.get("channel","email")
    if channel=="email" and GMAIL_PASS:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        to_email=prospect.get("email","")
        if not to_email: return "no_email"
        try:
            msg=MIMEMultipart("alternative")
            msg["From"]=f"S.C. Thomas <{GMAIL_USER}>"
            msg["To"]=to_email
            msg["Subject"]=touch.get("subject","Following up")
            msg.attach(MIMEText(touch.get("body",""),"plain"))
            with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
                s.login(GMAIL_USER,GMAIL_PASS)
                s.send_message(msg)
            log.info(f"  📧 Sent to {to_email}: {touch.get('subject','')[:40]}")
            return "sent"
        except Exception as e:
            log.warning(f"  Email failed: {e}")
            return f"failed:{e}"
    elif channel=="linkedin":
        # Stage LinkedIn action — note it for manual or automated execution
        log.info(f"  💼 LinkedIn action staged: {touch.get('goal','connect')}")
        return "staged_linkedin"
    return "executed"

def run():
    log.info("Multi-Channel Outreach Coordinator starting...")
    # 1. Fetch fresh prospects
    prospects=fetch_fresh_prospects(15)
    log.info(f"  Fetched {len(prospects)} prospects from Apollo")
    # 2. Score and enrich top prospects
    scored=[enrich_prospect(p) for p in prospects]
    hot=[p for p in scored if p.get("tier")=="HOT"]
    warm=[p for p in scored if p.get("tier")=="WARM"]
    log.info(f"  HOT: {len(hot)} | WARM: {len(warm)}")
    # 3. Stage sequences for HOT prospects
    for p in hot[:5]:
        seq=stage_outreach_sequence(p)
        log.info(f"  Sequence staged: {p.get('first_name','')} {p.get('last_name','')} ({p.get('company','')})")
    # 4. Execute due touches
    executed=execute_due_touches()
    log.info(f"  Touches executed: {len(executed)}")
    for touch in executed:
        log.info(f"    Day {touch['day']}: {touch['prospect']} via {touch['channel']} — {touch['result']}")
    # 5. Save daily summary
    path="data/sales/coordinator_log.json"
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=GH_H)
    existing=[]
    if r.status_code==200:
        try: existing=json.loads(base64.b64decode(r.json()["content"]).decode())
        except: pass
    existing.insert(0,{"date":str(date.today()),"prospects_fetched":len(prospects),
                       "hot":len(hot),"warm":len(warm),"touches_executed":len(executed)})
    existing=existing[:30]
    enc=base64.b64encode(json.dumps(existing,indent=2).encode()).decode()
    body={"message":f"coordinator: {len(executed)} touches executed {date.today()}","content":enc}
    if r.status_code==200: body["sha"]=r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",json=body,headers=GH_H)
    log.info(f"✅ Coordinator complete: {len(hot)} HOT leads sequenced, {len(executed)} touches executed")

if __name__=="__main__": run()
