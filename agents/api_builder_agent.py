#!/usr/bin/env python3
"""
API Builder Agent — Scaffolds Netlify serverless functions from plain English specs.
Given a requirement, generates a complete Netlify function with:
  - Input validation
  - Error handling
  - Authentication (API key or JWT)
  - Supabase data operations
  - Proper HTTP responses
  - CORS headers

Usage:
  ARCHITECT_REQUIREMENT="Build an endpoint that saves newsletter signups to Supabase"
  python agents/api_builder_agent.py
"""
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""

import urllib.request, base64

log = logging.getLogger(__name__)
GH_TOKEN  = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO      = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

API_TEMPLATE_PROMPT = """You are a senior full-stack engineer building Netlify serverless functions in JavaScript.

Generate a complete, production-ready Netlify function based on the requirement.

CONTEXT:
- Netlify Functions (Node.js 18)
- CORS enabled for all origins (we control the frontend)
- Supabase for database (SUPABASE_URL, SUPABASE_KEY env vars)
- No npm packages — use built-in https module + fetch
- Return proper HTTP status codes
- Always include error handling

NETLIFY FUNCTION STRUCTURE:
exports.handler = async (event, context) => {
  // 1. CORS headers
  // 2. Method check
  // 3. Parse body
  // 4. Validate input
  // 5. Business logic
  // 6. Return response
}

SUPABASE HELPER (always include this):
async function supabase(method, table, data, query = "") {
  const url = `${process.env.SUPABASE_URL}/rest/v1/${table}${query}`;
  const resp = await fetch(url, {
    method, headers: {
      "apikey": process.env.SUPABASE_KEY,
      "Authorization": `Bearer ${process.env.SUPABASE_KEY}`,
      "Content-Type": "application/json",
      "Prefer": "return=representation"
    },
    body: data ? JSON.stringify(data) : undefined
  });
  return resp.json();
}

Generate the complete function. No explanation outside the code."""

def architect_api(requirement: str) -> tuple:
    """Generate a Netlify function from requirement."""
    # Get filename
    fname = claude(
        "Generate a kebab-case filename for a Netlify function (no extension). Just the name.",
        f"Requirement: {requirement}",
        max_tokens=15
    )
    fname = (fname or "new-api").strip().strip('"').lower().replace(" ","-").replace("_","-")
    
    code = claude(API_TEMPLATE_PROMPT, f"REQUIREMENT: {requirement}\nFILENAME: {fname}.js\n\nGenerate complete Netlify function:", max_tokens=1500)
    if not code: return "", fname
    if "```javascript" in code: code = code.split("```javascript",1)[1].split("```",1)[0]
    elif "```js" in code: code = code.split("```js",1)[1].split("```",1)[0]
    elif "```" in code: code = code.split("```",1)[1].split("```",1)[0]
    return code.strip(), fname

def push_function(code: str, fname: str) -> bool:
    """Push Netlify function to GitHub."""
    path = f"netlify/functions/{fname}.js"
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/contents/{path}",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        )
        with urllib.request.urlopen(req,timeout=10) as r:
            sha = json.loads(r.read()).get("sha","")
    except: sha = ""
    
    payload = {"message":f"feat: API Builder generated {fname}.js","content":base64.b64encode(code.encode()).decode()}
    if sha: payload["sha"] = sha
    
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization":f"token {GH_TOKEN}","Content-Type":"application/json","Accept":"application/vnd.github+json"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return r.status in [200,201]
    except Exception as e:
        log.error(f"Push failed: {e}")
        return False

def run():
    requirement = os.environ.get("ARCHITECT_REQUIREMENT","")
    if not requirement:
        requirement = "Build an API endpoint that accepts a contact form submission and saves it to Supabase contacts table, then sends a Pushover notification"
    
    log.info(f"Building API: {requirement[:80]}...")
    code, fname = architect_api(requirement)
    
    if not code:
        log.error("API generation failed")
        return {"status":"failed"}
    
    log.info(f"Generated {len(code)} chars → netlify/functions/{fname}.js")
    
    if GH_TOKEN:
        pushed = push_function(code, fname)
        log.info(f"Pushed: {pushed}")
        return {"status":"success","function":fname,"size":len(code),"pushed":pushed}
    return {"status":"generated","function":fname,"size":len(code)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [APIBuilder] %(message)s")
    run()
