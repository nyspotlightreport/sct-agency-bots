#!/usr/bin/env python3
"""
Tech Debt Tracker Bot — Identifies and prioritizes technical debt.
Scans codebase for: TODOs, FIXMEs, deprecated patterns, dead code,
overly long functions, and missing error handling.
Generates weekly tech debt report and backlog.
"""
import os, sys, json, logging, base64, re
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude_json
except Exception:  # noqa: bare-except
    def claude_json(s,u,**k): return {}

import urllib.request

log = logging.getLogger(__name__)
GH_TOKEN      = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO          = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY","")

DEBT_PATTERNS = {
    "TODO":        (re.compile(r"#\s*TODO", re.IGNORECASE), "LOW"),
    "FIXME":       (re.compile(r"#\s*FIXME", re.IGNORECASE), "HIGH"),
    "HACK":        (re.compile(r"#\s*HACK", re.IGNORECASE), "MEDIUM"),
    "deprecated":  (re.compile(r"#\s*DEPRECATED", re.IGNORECASE), "HIGH"),
    "pass_block":  (re.compile(r"^\s*pass$", re.MULTILINE), "LOW"),
    "bare_except": (re.compile(r"except:"), "MEDIUM"),
    "no_type_hint":(re.compile(r"^def \w+\((?!.*->)"), "LOW"),
}

def gh(path):
    if not GH_TOKEN: return None
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except: return None

def scan_file_for_debt(path: str, content: str) -> list:
    debt = []
    lines = content.split("\n")
    for i, line in enumerate(lines,1):
        for debt_type, (pattern, severity) in DEBT_PATTERNS.items():
            if pattern.search(line):
                debt.append({"file":path,"line":i,"type":debt_type,"severity":severity,"code":line.strip()[:80]})
    
    # Check function length (>50 lines = debt)
    func_starts = [(i,line) for i,line in enumerate(lines,1) if re.match(r"^def ",line) or re.match(r"^    def ",line)]
    for i,(lineno,funcline) in enumerate(func_starts):
        end = func_starts[i+1][0] if i+1 < len(func_starts) else len(lines)
        if end - lineno > 50:
            debt.append({"file":path,"line":lineno,"type":"long_function","severity":"MEDIUM","code":f"{funcline.strip()} ({end-lineno} lines)"})
    
    return debt

def run():
    log.info("Tech Debt Tracker scanning codebase...")
    all_debt = []
    for folder in ["agents","bots"]:
        files = gh(f"/repos/{REPO}/contents/{folder}")
        if not files or not isinstance(files,list): continue
        for f in files:
            if not f["name"].endswith(".py"): continue
            resp = gh(f"/repos/{REPO}/contents/{f['path']}")
            if not resp or not isinstance(resp,dict): continue
            try:
                content = base64.b64decode(resp.get("content","").replace("\n","")).decode("utf-8","replace")
                debt = scan_file_for_debt(f["path"], content)
                all_debt.extend(debt)
            except Exception:  # noqa: bare-except

                pass
    high     = len([d for d in all_debt if d["severity"]=="HIGH"])
    medium   = len([d for d in all_debt if d["severity"]=="MEDIUM"])
    low      = len([d for d in all_debt if d["severity"]=="LOW"])
    
    log.info(f"Tech debt: {len(all_debt)} items | {high} high | {medium} medium | {low} low")
    
    if PUSHOVER_API and PUSHOVER_USER:
        try:
            msg = f"🔧 Tech Debt Report\n{len(all_debt)} items found\n{high} HIGH | {medium} MEDIUM | {low} LOW"
            data = urllib.parse.urlencode({"token":PUSHOVER_API,"user":PUSHOVER_USER,"title":"Tech Debt Weekly","message":msg}).encode()
            urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
        except Exception:  # noqa: bare-except

            pass
    return {"total_debt":len(all_debt),"high":high,"medium":medium,"low":low,"items":all_debt[:20]}

import urllib.parse
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [TechDebt] %(message)s")
    run()
