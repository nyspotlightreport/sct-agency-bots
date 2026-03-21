#!/usr/bin/env python3
"""
Claude Agent Core — NYSR Agency
Shared Claude API wrapper used by ALL intelligence agents.
Every agent in the system calls this for reasoning + generation.
Model: claude-sonnet-4-5 (best balance of quality + speed + cost)
"""
import os, requests, json, logging, time
log = logging.getLogger("ClaudeCore")

API_KEY = os.environ.get("ANTHROPIC_API_KEY","")
MODEL   = "claude-sonnet-4-5"
BASE    = "https://api.anthropic.com/v1"

def claude(system: str, user: str, max_tokens=1500, temperature=1.0) -> str:
    """Single Claude API call — returns text response."""
    if not API_KEY:
        log.warning("No ANTHROPIC_API_KEY")
        return ""
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role":"user","content":user}]
    }
    for attempt in range(3):
        try:
            r = requests.post(f"{BASE}/messages", headers=headers, json=body, timeout=60)
            if r.status_code == 200:
                return r.json()["content"][0]["text"].strip()
            elif r.status_code == 529:
                time.sleep(10 * (attempt+1))
            else:
                log.error(f"Claude API {r.status_code}: {r.text[:100]}")
                return ""
        except Exception as e:
            log.error(f"Claude request failed: {e}")
            time.sleep(5)
    return ""

def claude_json(system: str, user: str, max_tokens=1500) -> dict:
    """Claude call that returns parsed JSON."""
    sys_with_json = system + "\n\nYou must respond with valid JSON only. No markdown, no explanation."
    text = claude(sys_with_json, user, max_tokens)
    try:
        # Strip any accidental markdown fences
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        log.error(f"JSON parse failed: {e} | text: {text[:100]}")
        return {}

def claude_list(system: str, user: str, max_tokens=1500) -> list:
    """Claude call that returns a list."""
    result = claude_json(system, user + "\n\nReturn a JSON array.", max_tokens)
    return result if isinstance(result, list) else []
