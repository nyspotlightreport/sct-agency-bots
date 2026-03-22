#!/usr/bin/env python3
"""
Documentation Generator Bot — Auto-generates docs from source code.
Reads all agents and bots, generates markdown documentation,
and publishes to site/docs/ for the team and future AI models.
"""
import os, sys, json, logging, base64
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""

import urllib.request

log = logging.getLogger(__name__)
GH_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO     = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")

def gh(path, method="GET", body=None):
    if not GH_TOKEN: return None
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
            data=json.dumps(body).encode() if body else None,
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json",
                     "Content-Type":"application/json"},
            method=method)
        with urllib.request.urlopen(req,timeout=15) as r:
            if r.status == 204: return {}
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"GH {path}: {e}")
        return None

def get_file_content(download_url):
    try:
        with urllib.request.urlopen(download_url,timeout=10) as r:
            return r.read().decode("utf-8","replace")
    except: return ""

def document_file(path, content) -> str:
    """Generate markdown documentation for a Python file."""
    return claude(
        "Generate concise markdown documentation for this Python module. Include: purpose, key functions, parameters, usage example, and environment variables required.",
        f"File: {path}\n\n```python\n{content[:3000]}\n```\n\nGenerate markdown docs (max 400 words):",
        max_tokens=500
    ) or f"## {path.split('/')[-1].replace('.py','')}\n\n*Documentation pending.*"

def run():
    log.info("Doc Generator Bot running...")
    folders = ["agents","bots"]
    docs    = []
    
    for folder in folders:
        files = gh(f"/repos/{REPO}/contents/{folder}")
        if not files or not isinstance(files, list): continue
        for f in files:
            if not f["name"].endswith(".py"): continue
            content = get_file_content(f.get("download_url",""))
            if not content: continue
            doc = document_file(f["path"], content)
            docs.append(f"\n---\n\n# `{f['path']}`\n\n{doc}")
            log.info(f"  Documented: {f['name']}")
    
    # Build master docs index
    master = f"""# NYSR Agency System — Documentation
*Auto-generated {datetime.utcnow().strftime("%Y-%m-%d")} by Doc Generator Bot*

## System Overview
- **Agents:** Intelligent orchestrators with memory and decision-making
- **Bots:** Focused executors that run specific tasks
- **Workflows:** GitHub Actions that schedule and coordinate everything

---
{"".join(docs)}
"""
    
    # Push docs to repo
    doc_result = gh(f"/repos/{REPO}/contents/docs/README.md")
    sha = doc_result.get("sha","") if doc_result and isinstance(doc_result,dict) else ""
    payload = {"message":"docs: Auto-generated system documentation","content":base64.b64encode(master.encode()).decode()}
    if sha: payload["sha"] = sha
    pushed = gh(f"/repos/{REPO}/contents/docs/README.md", method="PUT", body=payload)
    
    log.info(f"Docs generated: {len(docs)} files | Pushed: {bool(pushed)}")
    return {"files_documented": len(docs), "total_chars": len(master)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [DocGen] %(message)s")
    run()
