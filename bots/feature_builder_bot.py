#!/usr/bin/env python3
"""
Feature Builder Bot — Translates feature requests into working code.
Parses FEATURE_REQUEST env var or GitHub issues labeled "build-me",
architects the solution, and deploys via Code Architect Agent.
This is the "build it for me" bot — Chairman describes feature, bot delivers.
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.code_architect_agent import architect_bot, push_to_repo
    from agents.api_builder_agent import architect_api, push_function
except Exception as e:
    print(f"Import partial: {e}")
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def architect_bot(r,t): return None
    def architect_api(r): return None, None

import urllib.request, urllib.parse

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

def notify(msg, title="Feature Builder"):
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def plan_feature(requirement: str) -> dict:
    """Use Claude to decompose a feature into implementation plan."""
    return claude_json(
        "You are a senior software architect. Plan the implementation of a new feature for an AI agency automation system.",
        f"""Feature request: {requirement}

Analyze and return JSON:
{{
  "summary": "1-sentence summary",
  "components": [
    {{"type": "bot|agent|api|page", "name": "component name", "purpose": "what it does"}}
  ],
  "estimated_files": 1-5,
  "complexity": "simple|moderate|complex",
  "implementation_order": ["component 1", "component 2"],
  "risks": ["risk 1"]
}}""",
        max_tokens=400
    ) or {"summary": requirement, "components": [{"type":"bot","name":"new_feature_bot","purpose":requirement}], "estimated_files":1, "complexity":"simple"}

def build_feature(requirement: str) -> dict:
    """Build a complete feature from a requirement string."""
    log.info(f"Planning feature: {requirement[:80]}...")
    plan = plan_feature(requirement)
    log.info(f"Plan: {plan.get('complexity','')} complexity | {len(plan.get('components',[]))} components")
    
    built = []
    for component in plan.get("components",[])[:3]:  # Max 3 components per run
        comp_type = component.get("type","bot")
        comp_name = component.get("name","new_feature")
        purpose   = component.get("purpose","")
        
        if comp_type == "api":
            code, fname = architect_api(purpose)
            if code:
                pushed = push_function(code, fname)
                built.append({"type":"api","name":fname,"pushed":pushed})
                log.info(f"  Built API: {fname} (pushed: {pushed})")
        else:
            output_type = "agent" if comp_type == "agent" else "bot"
            result = architect_bot(purpose, output_type)
            if result:
                code, filename, prefix = result
                path = f"{prefix}/{filename}.py"
                pushed = push_to_repo(code, path)
                built.append({"type":comp_type,"name":filename,"path":path,"pushed":pushed})
                log.info(f"  Built {comp_type}: {filename} (pushed: {pushed})")
    
    return {"requirement":requirement,"plan":plan,"built":built,"success":len(built)>0}

def get_build_requests() -> list:
    """Get feature requests from GitHub issues."""
    if not GH_TOKEN: return []
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues?labels=build-me&state=open&per_page=5",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        )
        with urllib.request.urlopen(req,timeout=10) as r:
            issues = json.loads(r.read())
        return [{"id":i["number"],"title":i["title"],"body":i.get("body","")} for i in (issues or [])]
    except: return []

def run():
    log.info("Feature Builder Bot running...")
    
    # Get requirement from env var or GitHub issues
    requirement = os.environ.get("FEATURE_REQUEST","")
    requests = []
    
    if requirement:
        requests.append({"title":requirement,"body":""})
    else:
        requests = get_build_requests()
    
    if not requests:
        log.info("No feature requests found. Set FEATURE_REQUEST env var or create GitHub issue with 'build-me' label.")
        return {"status":"idle","requests_found":0}
    
    built_count = 0
    for req in requests[:2]:  # Max 2 per run
        full_req = req["title"] + (f"\n\nDetails: {req['body'][:500]}" if req.get("body") else "")
        result   = build_feature(full_req)
        if result["success"]:
            built_count += 1
            notify(f"🏗️ Feature built: {result['requirement'][:60]}\n\nComponents: {len(result['built'])}\n" +
                   "\n".join([f"• {c['type']}: {c['name']}" for c in result['built']]),
                   "Feature Builder: Done")
        else:
            notify(f"❌ Feature build failed: {req['title'][:60]}", "Feature Builder: Failed")
    
    log.info(f"Feature Builder: {built_count} features built")
    return {"features_built":built_count,"requests_processed":len(requests)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [FeatBuilder] %(message)s")
    run()
