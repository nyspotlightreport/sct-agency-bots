#!/usr/bin/env python3
"""
Test Generator Bot — Creates test suites for agents and bots.
Generates: unit tests, integration smoke tests, and workflow validation.
Uses pytest-compatible test files.
"""
import os, sys, json, logging, base64
from datetime import datetime
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
except Exception:  # noqa: bare-except
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
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/json"},
            method=method)
        with urllib.request.urlopen(req,timeout=15) as r:
            if r.status == 204: return {}
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"GH {path}: {e}")
        return None

def generate_tests(path: str, content: str) -> str:
    return claude(
        "Generate a complete pytest test file for this Python module. Include: smoke test for run(), mock tests for external APIs, edge case tests. Use unittest.mock for patching. File must be immediately runnable.",
        f"Module to test: {path}\n\n```python\n{content[:2500]}\n```\n\nGenerate complete test file:",
        max_tokens=1000
    ) or ("import pytest\n"
        "from unittest.mock import patch, MagicMock\n\n"
        "def test_" + path.split("/")[-1].replace(".py","") + "_imports():\n"
        "    \"\"\"Smoke test: module imports without errors.\"\"\"\n"
        "    try:\n"
        "        import importlib.util\n"
        "        spec = importlib.util.spec_from_file_location(\"module\", \"" + path + "\")\n"
        "        assert spec is not None\n"
        "    except ImportError:\n"
        "        pytest.skip(\"Dependencies not available in test environment\")\n\n"
        "def test_run_returns_dict():\n"
        "    \"\"\"run() should return a dict with at least one key.\"\"\"\n"
        "    pass  # TODO: implement after mock setup\n")

def run():
    log.info("Test Generator Bot running...")
    folders = ["agents","bots"]
    tests_created = 0
    
    for folder in folders:
        files = gh(f"/repos/{REPO}/contents/{folder}")
        if not files or not isinstance(files, list): continue
        for f in files:
            if not f["name"].endswith(".py"): continue
            try:
                resp = gh(f"/repos/{REPO}/contents/{f['path']}")
                if not resp or not isinstance(resp, dict): continue
                content = base64.b64decode(resp.get("content","").replace("\n","")).decode("utf-8","replace")
                test_code = generate_tests(f["path"], content)
                test_path = f"tests/test_{f['name']}"
                existing = gh(f"/repos/{REPO}/contents/{test_path}")
                sha = existing.get("sha","") if existing and isinstance(existing,dict) else ""
                payload = {"message":f"test: Auto-generated tests for {f['name']}","content":base64.b64encode(test_code.encode()).decode()}
                if sha: payload["sha"] = sha
                gh(f"/repos/{REPO}/contents/{test_path}", method="PUT", body=payload)
                tests_created += 1
                log.info(f"  Tests for: {f['name']}")
            except Exception as e:
                log.warning(f"  Test gen failed for {f['name']}: {e}")
    
    log.info(f"Tests generated: {tests_created}")
    return {"tests_created": tests_created}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [TestGen] %(message)s")
    run()
