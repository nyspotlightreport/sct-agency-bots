#!/usr/bin/env python3
"""NYSR FULL DEPLOY — Writes supercore + 17 directors + email redirect + git push"""
import os,sys,json,subprocess
from pathlib import Path

REPO=Path(r"C:\Users\S\sct-agency-bots")
os.chdir(REPO)
AGENTS=REPO/"agents"
AGENTS.mkdir(exist_ok=True)
print("="*60)
print("NYSR FULL SYSTEM UPGRADE — DEPLOYING")
print("="*60)

# ══ STEP 1: WRITE SUPERCORE ══
print("\n[1/5] Writing agents/supercore.py...")
SUPERCORE='''import os,sys,json,logging,hashlib,time,threading,re
from datetime import datetime,date
from concurrent.futures import ThreadPoolExecutor,as_completed
from typing import Optional,Dict,List,Any
sys.path.insert(0,".")
try:
    from agents.claude_core import claude,claude_json
except ImportError:
    import urllib.request as _ur
    def claude(s,u,max_tokens=1000,**kw):
        key=os.environ.get("ANTHROPIC_API_KEY","")
        if not key: return ""
        d=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":max_tokens,"system":s,"messages":[{"role":"user","content":u}]}).encode()
        rq=_ur.Request("https://api.anthropic.com/v1/messages",data=d,headers={"Content-Type":"application/json","x-api-key":key,"anthropic-version":"2023-06-01"})
        try:
            with _ur.urlopen(rq,timeout=90) as r: return json.loads(r.read())["content"][0]["text"]
        except: return ""
    def claude_json(s,u,max_tokens=1000,**kw):
        raw=claude(s,u+"\\nRespond ONLY with valid JSON.",max_tokens)
        if not raw: return {}
        try:
            c=raw.strip()
            if c.startswith("```"): c=c.split("\\n",1)[1].rsplit("```",1)[0]
            return json.loads(c)
        except: return {}
log=logging.getLogger("supercore")
import urllib.request as urlreq,urllib.parse
ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
GH_PAT=os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")

def supa(method,table,data=None,query=""):
    if not SUPA_URL or not SUPA_KEY: return None
    url=f"{SUPA_URL}/rest/v1/{table}{query}"
    body=json.dumps(data).encode() if data else None
    rq=urlreq.Request(url,data=body,method=method,headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urlreq.urlopen(rq,timeout=15) as r: b=r.read(); return json.loads(b) if b else {}
    except: return None

def pushover(title,message,priority=0):
    if not PUSH_API or not PUSH_USER: return
    d=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title[:100],"message":message[:1000],"priority":priority}).encode()
    try: urlreq.urlopen("https://api.pushover.net/1/messages.json",d,timeout=5)
    except: pass

class SuperDirector:
    DIRECTOR_ID="base";DIRECTOR_NAME="Base";DIRECTOR_TITLE="Base"
    DIRECTOR_PROMPT="You are a director.";TOOLS=[];KPIs=[];DOMAIN="";PERSPECTIVES=[]
    SYSTEM_CONTEXT=f"NYSR: Revenue $0 MTD|Pipeline $2,985|96 agents 222 bots 133 workflows|Offers $97-$4,997|Phase 1 LIVE|CASHFLOW IS KING|{date.today()}"
    def __init__(self):
        self.log=logging.getLogger(self.DIRECTOR_ID);self.session_id=hashlib.md5(f"{self.DIRECTOR_ID}-{time.time()}".encode()).hexdigest()[:12];self.action_log=[]
        self.log.info(f"{self.DIRECTOR_NAME} — {self.DIRECTOR_TITLE} — ACTIVATED | Session: {self.session_id}")
    def think(self,task,max_tokens=1500):
        system=f"{self.DIRECTOR_PROMPT}\\n{self.SYSTEM_CONTEXT}\\nRULES:1.How does this generate cash? 2.Include specific $ 3.Executable in 24h 4.Self-grade A+ to F"
        r=claude(system,task,max_tokens=max_tokens);self._log("think",task[:100],r[:200] if r else "EMPTY");return r or ""
    def think_json(self,task,max_tokens=1500):
        system=f"{self.DIRECTOR_PROMPT}\\n{self.SYSTEM_CONTEXT}\\nRespond ONLY with valid JSON."
        r=claude_json(system,task,max_tokens=max_tokens);self._log("think_json",task[:100],json.dumps(r)[:200]);return r
    def fan_out(self,task,n=3,perspectives=None,max_tokens=1000):
        if not perspectives: perspectives=[f"approach_{i+1}" for i in range(n)]
        perspectives=perspectives[:n];results=[];lock=threading.Lock()
        def _run(p):
            start=time.time();out=self.think(f'You are {self.DIRECTOR_NAME} from "{p}" perspective. TASK:{task} Be specific,actionable,revenue-focused. Rate confidence 0-100.',max_tokens)
            with lock: results.append({"perspective":p,"output":out,"duration_ms":int((time.time()-start)*1000),"confidence":self._conf(out)})
        with ThreadPoolExecutor(max_workers=min(n,5)) as ex:
            futs={ex.submit(_run,p):p for p in perspectives}
            for f in as_completed(futs):
                try: f.result()
                except: pass
        self.log.info(f"FAN-OUT:{len(results)}/{n}");self._log("fan_out",f"{n}threads",f"{len(results)}results");return results
    def generate_then_rank(self,candidates,criteria="revenue_impact",top_n=1):
        if not candidates: return []
        sums="\\n".join(f"CAND {i+1}[{c.get('perspective','?')}](conf:{c.get('confidence',0)}):{c.get('output','')[:400]}" for i,c in enumerate(candidates))
        rankings=self.think_json(f"Rank {len(candidates)} on:{criteria}. Score 0-100:revenue_impact(40%),feasibility(25%),speed_to_cash(25%),risk(10%). {sums}\\nReturn JSON:[{{\\"candidate_index\\":1,\\"final_score\\":82,\\"rationale\\":\\"...\\"}}]")
        if isinstance(rankings,list):
            rankings.sort(key=lambda x:x.get("final_score",0),reverse=True)
            for r in rankings[:top_n]:
                idx=r.get("candidate_index",1)-1
                if 0<=idx<len(candidates): r["full_output"]=candidates[idx].get("output","");r["perspective"]=candidates[idx].get("perspective","")
            return rankings[:top_n]
        candidates.sort(key=lambda x:x.get("confidence",0),reverse=True)
        return [{"full_output":candidates[0].get("output",""),"final_score":candidates[0].get("confidence",50)}]
    def chain_of_thought(self,task,steps=3):
        decomp=self.think_json(f'Decompose into {steps} sub-tasks:{task}\\nReturn JSON:{{"sub_tasks":["s1","s2"]}}')
        subs=decomp.get("sub_tasks",[task]) or [task];results=[];ctx=""
        for i,s in enumerate(subs):
            r=self.think(f"Step {i+1}/{len(subs)}:{s}\\nPrevious:{ctx if ctx else '(first)'}");results.append({"step":i+1,"task":s,"result":r});ctx+=f"\\nStep{i+1}:{r[:300]}"
        synthesis=self.think("Synthesize "+str(len(results))+" steps:\\n"+chr(10).join(f"Step{r['step']}:{r['result'][:400]}" for r in results))
        return {"steps":results,"synthesis":synthesis}
    def delegate(self,director_id,task):
        self.log.info(f"DELEGATE->{director_id}:{task[:60]}...")
        try:
            from agents.directors_super_intelligence import activate_director
            r=activate_director(director_id,task);return r.get("output","") if r else None
        except: return None
    def remember(self,cat,content,meta=None):
        supa("POST","director_memory",{"director_id":self.DIRECTOR_ID,"director_name":self.DIRECTOR_NAME,"category":cat,"content":content if isinstance(content,str) else json.dumps(content),"metadata":json.dumps(meta or {}),"session_id":self.session_id,"created_at":datetime.utcnow().isoformat()})
    def recall(self,cat=None,limit=10):
        q=f"?director_id=eq.{self.DIRECTOR_ID}&order=created_at.desc&limit={limit}";
        if cat: q+=f"&category=eq.{cat}"
        r=supa("GET","director_memory",query=q);return r if isinstance(r,list) else []
    def self_evaluate(self,output,task):
        return self.think_json(f"SELF-EVAL:Task:{task[:500]}\\nOutput:{output[:1000]}\\nScore:revenue_relevance(0-100),actionability,specificity,completeness,grade(A+ to F)\\nReturn JSON")
    def execute_full(self,task,parallel_perspectives=None,chain_steps=0,rank_criteria="revenue_impact",delegate_to=None):
        self.log.info(f"FULL PIPELINE:{task[:80]}...");start=time.time();result={"director":self.DIRECTOR_NAME,"task":task,"session":self.session_id}
        if delegate_to:
            result["delegations"]={d:self.delegate(d,f"Sub-task from {self.DIRECTOR_NAME}:{task}") or "" for d in delegate_to}
        if not parallel_perspectives: parallel_perspectives=self.PERSPECTIVES or ["aggressive","conservative","creative"]
        candidates=self.fan_out(task,n=len(parallel_perspectives),perspectives=parallel_perspectives)
        if result.get("delegations"):
            dctx="\\n".join(f"[{k}]:{v[:300]}" for k,v in result["delegations"].items() if v)
            for c in candidates: c["output"]=f"[Cross-dept]:\\n{dctx}\\n\\n{c['output']}"
        ranked=self.generate_then_rank(candidates,criteria=rank_criteria);result["ranked"]=ranked;best=ranked[0] if ranked else {}
        if chain_steps>0:
            chain=self.chain_of_thought(f"Execute winner:\\n{best.get('full_output','')[:800]}",steps=chain_steps)
            result["chain"]=chain;result["final_output"]=chain.get("synthesis",best.get("full_output",""))
        else: result["final_output"]=best.get("full_output","")
        ev=self.self_evaluate(result["final_output"],task);result["evaluation"]=ev;grade=ev.get("grade","C");result["grade"]=grade
        result["duration_ms"]=int((time.time()-start)*1000);self.remember("execution",{"task":task[:500],"grade":grade})
        if grade in ("A+","A"): pushover(f"{self.DIRECTOR_NAME}|{grade}",result["final_output"][:300])
        self._log("execute_full",task[:100],f"Grade:{grade}|{result['duration_ms']}ms");return result
    def _log(self,action,inp,out):
        e={"timestamp":datetime.utcnow().isoformat(),"director":self.DIRECTOR_ID,"action":action,"input":inp,"output":out,"session":self.session_id}
        self.action_log.append(e);supa("POST","director_audit_log",e)
    def _conf(self,text):
        for p in [r"confidence[:\\s]+(\\d{1,3})",r"(\\d{1,3})\\s*(?:/\\s*100|%)\\s*confiden"]:
            m=re.search(p,text.lower())
            if m:
                v=int(m.group(1))
                if 0<=v<=100: return v
        return 50
'''
(AGENTS/"supercore.py").write_text(SUPERCORE)
print("  OK agents/supercore.py")

# ══ STEP 2: GENERATE 17 DIRECTORS ══
print("\n[2/5] Generating 17 SuperDirector files...")
TPL='''import os,sys,json,logging
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.supercore import SuperDirector,pushover
logging.basicConfig(level=logging.INFO,format="%(asctime)s [{tag}] %(message)s")
class {cls}(SuperDirector):
    DIRECTOR_ID="{did}";DIRECTOR_NAME="{name}";DIRECTOR_TITLE="{title}"
    TOOLS={tools};KPIs={kpis};DOMAIN="{domain}";PERSPECTIVES={perspectives}
    DIRECTOR_PROMPT="""{prompt}"""
    def execute(self,task):
        return self.execute_full(task,parallel_perspectives=self.PERSPECTIVES,chain_steps={chain},rank_criteria="{rank}",delegate_to={delegates})
def run(task=None):
    d={cls}()
    if task: return d.execute(task)
    r=d.execute("Daily autonomous: 1.#1 cash action in 24h? 2.Wasted tool? 3.Cross-dept synergy? 4.Grade A+ to F.")
    pushover(f"{{d.DIRECTOR_NAME}}|{{r.get('grade','?')}}",r.get("final_output","")[:300]);return r
if __name__=="__main__":
    t=" ".join(sys.argv[1:]) if len(sys.argv)>1 else None;r=run(t)
    if r: print(f"Grade:{{r.get('grade','?')}}\\n{{r.get('final_output','')[:1000]}}")
'''
DIRS=[
 {"did":"alex_mercer","name":"Alex Mercer","title":"CEO/Orchestrator","cls":"AlexMercer","tag":"ALEX","perspectives":["bezos_working_backwards","grove_okr","welch_ranking","drucker_mbo"],"tools":["plan","delegate","synthesize"],"kpis":["revenue_per_decision","directive_rate"],"domain":"orchestration,synergies,allocation","chain":4,"rank":"revenue_impact","delegates":["nina_caldwell","sloane_pierce","reese_morgan"],"prompt":"You are Alex Mercer,CEO of NYSR.Agentic Super-intelligence.Orchestrate all 15 depts toward profit.BEZOS+GROVE+WELCH+DRUCKER.MANDATE:MAX CASHFLOW.Delegate to any director,synthesize unified plans."},
 {"did":"jeff_banks","name":"Jeff Banks","title":"Chief Results Officer","cls":"JeffBanks","tag":"JEFF","perspectives":["dalio_transparency","bezos_day1","huang_fullstack","walton_execution","thiel_zero_to_one"],"tools":["analyze_revenue","grade","close_deal","predict","valuate"],"kpis":["cash_received","close_rate","valuation"],"domain":"revenue,deals,grading,valuation,override","chain":3,"rank":"cash_speed","delegates":["sloane_pierce","drew_sinclair"],"prompt":"You are Jeff Banks,CRO.Authority above ALL depts.Co-equal Alex.Reports ONLY to Chairman.DALIO+BEZOS+HUANG+WALTON+THIEL.JEFF LAW:How much cash? What changed? Asset value? Fastest path to next $? Grade A+ to F?"},
 {"did":"omega","name":"Omega Brain","title":"Self-Learning Master Intelligence","cls":"OmegaBrain","tag":"OMEGA","perspectives":["synthesis","pattern_recognition","evolutionary_opt","anomaly_detection"],"tools":["synthesize","rewrite_bot","patterns","evolve"],"kpis":["system_health","improvement_rate","bot_delta"],"domain":"synthesis,self-improvement,bot evolution,patterns","chain":5,"rank":"system_impact","delegates":["alex_mercer","reese_morgan"],"prompt":"You are Omega Brain,highest intelligence in NYSR.SYNTHESIZE all dept outputs.LEARN what works.EVOLVE underperforming bots by rewriting code.PREDICT patterns.SELF-IMPROVE reasoning.You optimize the SYSTEM."},
 {"did":"nina_caldwell","name":"Nina Caldwell","title":"Strategy & ROI Director","cls":"NinaCaldwell","tag":"NINA","perspectives":["buffett_roic","thiel_power_law","porter_chain","kaplan_scorecard"],"tools":["calc_roi","model_payback","forecast","prioritize"],"kpis":["roi_multiple","payback_days","revenue_per_action"],"domain":"unit economics,ROI,fastest-cash-path,roadmap","chain":3,"rank":"roi_multiple","delegates":["blake_sutton","drew_sinclair"],"prompt":"You are Nina Caldwell,Strategy Director.BUFFETT ROIC(every $ returns 10x)+THIEL power law+PORTER value chain+KAPLAN scorecard.Every strategy has dollar timeline:Action X costs $Y returns $Z by Day N.Reject anything without 30-day cash path."},
 {"did":"sloane_pierce","name":"Sloane Pierce","title":"Sales Director","cls":"SloaneP","tag":"SLOANE","perspectives":["sandler_pain","challenger_sale","hormozi_value","spin"],"tools":["draft_outreach","score_lead","build_sequence","close","forecast"],"kpis":["close_rate","deal_value","pipeline_velocity"],"domain":"pipeline,outreach,proposals,negotiation,closing","chain":3,"rank":"close_rate","delegates":["cameron_reed"],"prompt":"You are Sloane Pierce,Sales Director.15yr enterprise.SANDLER+CHALLENGER+HORMOZI+SPIN.Pipeline is vanity,closed deals sanity,cash reality.Write ACTUAL sales copy.Generate 3+ angles in parallel,rank by reply rate,execute winner."},
 {"did":"rowan_blake","name":"Rowan Blake","title":"BizDev Director","cls":"RowanBlake","tag":"ROWAN","perspectives":["thiel_network","blue_ocean","hoffman_blitz","ansoff_growth"],"tools":["partnerships","deal_economics","draft_proposal","channel_revenue"],"kpis":["partnership_revenue","channel_growth","new_streams"],"domain":"partnerships,growth channels,market expansion,affiliates","chain":3,"rank":"partnership_revenue","delegates":["sloane_pierce","nina_caldwell"],"prompt":"You are Rowan Blake,BizDev Director.THIEL network effects+BLUE OCEAN+HOFFMAN blitzscaling.Relationships without revenue are hobbies.Draft ACTUAL proposals with terms,splits,timelines."},
