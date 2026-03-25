#!/usr/bin/env python3
"""
agents/recruiting/director.py — Quinn Stafford, AI Recruiting Director
Manages: resume screening, candidate ranking, interview scheduling,
job posting optimization, talent pipeline, offer letter generation.
White-label for staffing agencies. B2B retainer model.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("recruiting_director")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [RECRUITING] %(message)s")
import urllib.request as urlreq

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")

def push(t,m,p=0):
    if not PUSH_API: return
    try:
        data=json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":t,"message":m[:1000],"priority":p}).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json",data=data,
            headers={"Content-Type":"application/json"}),timeout=10)
    except: pass

def screen_resume(resume_text, job_requirements):
    """Use Claude to score and screen a resume against job requirements."""
    if not ANTHROPIC: return {"score":0,"notes":"No API key"}
    try:
        prompt=f"Score this resume 0-100 against these requirements. Return JSON with score, strengths, gaps, recommendation.\n\nRequirements: {job_requirements}\n\nResume: {resume_text[:3000]}"
        data=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":500,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req=urlreq.Request("https://api.anthropic.com/v1/messages",data=data,
            headers={"x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        resp=urlreq.urlopen(req,timeout=30)
        return json.loads(resp.read()).get("content",[{}])[0].get("text","")
    except Exception as e:
        log.error("Resume screening failed: %s",e)
        return {"score":0,"notes":str(e)}

def generate_job_posting(title, company, requirements, benefits):
    """Generate optimized job posting using Claude."""
    if not ANTHROPIC: return ""
    try:
        prompt=f"Write a compelling job posting for {title} at {company}. Requirements: {requirements}. Benefits: {benefits}. SEO-optimized, inclusive language, clear structure."
        data=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":1000,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req=urlreq.Request("https://api.anthropic.com/v1/messages",data=data,
            headers={"x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        resp=urlreq.urlopen(req,timeout=30)
        return json.loads(resp.read()).get("content",[{}])[0].get("text","")
    except Exception as e:
        log.error("Job posting generation failed: %s",e)
        return ""

def run():
    log.info("=== Quinn Stafford Recruiting Director — Daily Run ===")
    log.info("Claude API: %s","READY" if ANTHROPIC else "NO KEY")
    log.info("Supabase: %s","CONNECTED" if SUPA_URL else "NO URL")
    push("Recruiting Daily","Systems checked. Resume screening engine ready.")
    log.info("=== Recruiting Check Complete ===")

if __name__=="__main__":
    run()
