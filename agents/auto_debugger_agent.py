#!/usr/bin/env python3
"""
Auto Debugger Agent — Finds and fixes bugs across the codebase automatically.
Extends Guardian v5 with deep code analysis capabilities.

Capabilities:
  1. Parse failed workflow logs → identify root cause
  2. Read the failing file from repo
  3. Use Claude to generate fix
  4. Push fix to GitHub
  5. Re-trigger workflow to verify fix
  6. Escalate to Chairman if cannot fix
"""
import os, sys, json, logging, zipfile, io, re
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

import urllib.request, urllib.parse, base64

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
ANTHROPIC     = os.environ.get("ANTHROPIC_API_KEY","")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

def notify(msg, title="Auto Debugger"):
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":title,"message":msg[:1000]}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except: pass

def gh(path, method="GET", body=None):
    if not GH_TOKEN: return None
    try:
        url = f"https://api.github.com{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data,
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"},
            method=method)
        with urllib.request.urlopen(req,timeout=20) as r:
            if r.status == 204: return {}
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"GH {method} {path}: {e}")
        return None

def get_failed_runs(limit=10) -> list:
    """Get recently failed workflow runs."""
    runs = gh(f"/repos/{REPO}/actions/runs?status=failure&per_page={limit}")
    if not runs: return []
    return [{"id":r["id"],"name":r["name"],"url":r["html_url"],"workflow_id":r["workflow_id"]} 
            for r in runs.get("workflow_runs",[])]

def get_run_logs(run_id: int) -> str:
    """Download and parse workflow run logs."""
    if not GH_TOKEN: return ""
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/logs",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
        )
        with urllib.request.urlopen(req,timeout=30) as r:
            raw = r.read()
        
        # Extract from ZIP
        text_parts = []
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for name in z.namelist():
                    if name.endswith(".txt"):
                        content = z.read(name).decode("utf-8","replace")
                        # Strip ANSI + timestamps
                        content = re.sub(r"\[[0-9;]*m","",content)
                        content = re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:.Z]+\s","",content,flags=re.MULTILINE)
                        text_parts.append(content[-3000:])  # last 3k chars per file
        except:
            text_parts.append(raw.decode("utf-8","replace")[-5000:])
        
        return "\n".join(text_parts)[-8000:]  # max 8k chars
    except Exception as e:
        log.warning(f"Logs for run {run_id}: {e}")
        return ""

def get_file_content(path: str) -> tuple:
    """Get file content and SHA from GitHub."""
    result = gh(f"/repos/{REPO}/contents/{path}")
    if not result or not isinstance(result, dict): return "", ""
    try:
        content = base64.b64decode(result.get("content","").replace("\n","")).decode("utf-8","replace")
        return content, result.get("sha","")
    except: return "", ""

def analyze_failure(run_name: str, logs: str) -> dict:
    """Use Claude to diagnose a workflow failure."""
    return claude_json(
        "You are a senior DevOps engineer. Diagnose this GitHub Actions failure and provide a specific fix.",
        f"""Workflow: {run_name}
        
Logs (last 8000 chars):
{logs}

Analyze and return JSON:
{{
  "error_type": "import_error|syntax_error|runtime_error|missing_secret|api_error|timeout|dependency|other",
  "root_cause": "specific cause in 1 sentence",
  "affected_file": "path/to/file.py or null",
  "fix_description": "what to change",
  "fix_code_snippet": "the exact code fix (or null if not applicable)",
  "confidence": 0.0-1.0,
  "auto_fixable": true/false
}}""",
        max_tokens=500
    ) or {"error_type":"unknown","root_cause":"Could not analyze","auto_fixable":False,"confidence":0.0}

def apply_fix(file_path: str, fix_description: str, current_content: str, current_sha: str) -> bool:
    """Use Claude to apply a fix to a file and push it."""
    if not current_content: return False
    
    fixed_code = claude(
        "You are a senior Python engineer. Apply the described fix to this code. Return ONLY the complete fixed Python file, no explanation.",
        f"""Fix to apply: {fix_description}
        
Current file ({file_path}):
```python
{current_content[:6000]}
```

Return the complete fixed Python file:""",
        max_tokens=2000
    )
    
    if not fixed_code: return False
    # Clean up markdown fences
    if "```python" in fixed_code: fixed_code = fixed_code.split("```python",1)[1].split("```",1)[0]
    elif "```" in fixed_code:     fixed_code = fixed_code.split("```",1)[1].split("```",1)[0]
    fixed_code = fixed_code.strip()
    
    # Push the fix
    payload = {
        "message": f"fix: Auto-debugger applied fix to {file_path.split('/')[-1]}",
        "content": base64.b64encode(fixed_code.encode()).decode(),
        "sha": current_sha
    }
    result = gh(f"/repos/{REPO}/contents/{file_path}", method="PUT", body=payload)
    return bool(result)

def re_trigger_workflow(workflow_id: int) -> bool:
    """Re-trigger a workflow after fix is applied."""
    result = gh(f"/repos/{REPO}/actions/workflows/{workflow_id}/dispatches", method="POST", body={"ref":"main"})
    return result is not None

def run():
    log.info("Auto Debugger Agent scanning for failures...")
    failed_runs = get_failed_runs(5)
    log.info(f"Found {len(failed_runs)} failed workflows")
    
    fixed = 0
    escalated = 0
    
    for run in failed_runs:
        log.info(f"Analyzing: {run['name']}")
        logs     = get_run_logs(run["id"])
        if not logs:
            log.warning(f"  No logs for {run['name']}")
            continue
        
        analysis = analyze_failure(run["name"], logs)
        log.info(f"  Root cause: {analysis.get('root_cause','?')}")
        log.info(f"  Auto-fixable: {analysis.get('auto_fixable',False)} ({analysis.get('confidence',0):.0%} confidence)")
        
        if analysis.get("auto_fixable") and analysis.get("confidence",0) >= 0.70:
            file_path = analysis.get("affected_file","")
            if file_path:
                content, sha = get_file_content(file_path)
                if content and sha:
                    success = apply_fix(file_path, analysis.get("fix_description",""), content, sha)
                    if success:
                        re_trigger_workflow(run["workflow_id"])
                        fixed += 1
                        log.info(f"  ✅ Fixed and re-triggered: {run['name']}")
                        notify(f"✅ Auto-fixed: {run['name']}\n\nFix: {analysis.get('fix_description','')}\nFile: {file_path}", "AutoDebugger: Fixed")
                    else:
                        escalated += 1
                        notify(f"❌ Fix failed for {run['name']}\n\nRoot cause: {analysis.get('root_cause','')}\nFile: {file_path}", "AutoDebugger: Needs Help")
        else:
            escalated += 1
            notify(f"⚠️ Cannot auto-fix: {run['name']}\n\nRoot cause: {analysis.get('root_cause','')}\nConfidence: {analysis.get('confidence',0):.0%}\n\nManual intervention needed.", "AutoDebugger: Escalating")
    
    log.info(f"Auto Debugger complete: {fixed} fixed | {escalated} escalated")
    return {"failed_runs_found":len(failed_runs),"fixed":fixed,"escalated":escalated}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [AutoDebug] %(message)s")
    run()
