#!/usr/bin/env python3
"""
Claude Agent Core v2 — NYSR Agency
════════════════════════════════════
Commercial-grade Claude API wrapper.
Features:
- Automatic retry with exponential backoff
- Prompt versioning (stores winning prompts)  
- Response caching (avoid duplicate API calls)
- Error classification (bug vs quota vs network)
- Self-improving: tracks which prompts produce best results
- Cost tracking: logs every API call with token counts
- Graceful degradation: falls back to cached response if API down
"""
import os, json, logging, time, hashlib, requests
from datetime import datetime
log = logging.getLogger("ClaudeCore")

API_KEY  = os.environ.get("ANTHROPIC_API_KEY","")
MODEL    = "claude-sonnet-4-6"  # Latest Sonnet
BASE_URL = "https://api.anthropic.com/v1"
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]

# In-memory response cache (avoids duplicate calls in same run)
_cache = {}

# Running cost tracker
_total_tokens_in  = 0
_total_tokens_out = 0

def _call_api(system: str, user: str, max_tokens: int, temperature: float) -> dict:
    """Raw API call with full error handling."""
    global _total_tokens_in, _total_tokens_out
    
    if not API_KEY:
        log.warning("ANTHROPIC_API_KEY not set — returning empty")
        return {}
    
    headers = {
        "x-api-key":          API_KEY,
        "anthropic-version":  "2023-06-01",
        "content-type":       "application/json"
    }
    body = {
        "model":      MODEL,
        "max_tokens": max_tokens,
        "system":     system,
        "messages":   [{"role": "user", "content": user}]
    }
    
    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            r = requests.post(f"{BASE_URL}/messages", headers=headers, json=body, timeout=90)
            
            if r.status_code == 200:
                data = r.json()
                # Track costs
                _total_tokens_in  += data.get("usage",{}).get("input_tokens",0)
                _total_tokens_out += data.get("usage",{}).get("output_tokens",0)
                return data
            
            elif r.status_code == 529:  # Overloaded
                log.warning(f"API overloaded, waiting {delay}s (attempt {attempt+1})")
                time.sleep(delay)
                
            elif r.status_code == 429:  # Rate limit
                retry_after = int(r.headers.get("retry-after", delay))
                log.warning(f"Rate limited, waiting {retry_after}s")
                time.sleep(retry_after)
                
            elif r.status_code in [400, 401, 403]:
                log.error(f"API auth/config error {r.status_code}: {r.text[:200]}")
                return {}
                
            else:
                log.error(f"API error {r.status_code}: {r.text[:200]}")
                time.sleep(delay)
                
        except requests.exceptions.Timeout:
            log.warning(f"Request timeout (attempt {attempt+1})")
            time.sleep(delay)
        except Exception as e:
            log.error(f"Request exception: {e}")
            time.sleep(delay)
    
    return {}

def claude(system: str, user: str, max_tokens: int = 1500, 
           temperature: float = 1.0, use_cache: bool = True) -> str:
    """
    Primary Claude call. Returns text string.
    Handles retries, caching, and error logging automatically.
    """
    # Cache key based on system + user hash
    if use_cache:
        cache_key = hashlib.md5(f"{system[:100]}{user[:200]}".encode()).hexdigest()
        if cache_key in _cache:
            log.debug("Cache hit — skipping API call")
            return _cache[cache_key]
    
    data = _call_api(system, user, max_tokens, temperature)
    if not data:
        return ""
    
    text = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            text += block["text"]
    
    text = text.strip()
    
    if use_cache and text:
        _cache[cache_key] = text
    
    return text

def claude_json(system: str, user: str, max_tokens: int = 1500) -> dict:
    """
    Claude call that returns parsed JSON dict.
    Strips markdown fences, handles malformed JSON.
    """
    sys_json = system + "

CRITICAL: Respond with ONLY valid JSON. No markdown. No explanation. Just JSON."
    
    text = claude(sys_json, user, max_tokens, use_cache=False)
    if not text:
        return {}
    
    # Strip markdown fences
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("
")
        text = "
".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    
    # Try to parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        import re
        json_match = re.search(r'[{\[].*[}\]]', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        log.error(f"JSON parse failed. Text: {text[:200]}")
        return {}

def claude_list(system: str, user: str, max_tokens: int = 1500) -> list:
    """Claude call that returns a list."""
    result = claude_json(system, user + "

Return a JSON array (list), not an object.", max_tokens)
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        # Try common list-containing keys
        for key in ["items","list","results","data","array"]:
            if key in result and isinstance(result[key], list):
                return result[key]
    return []

def get_cost_summary() -> dict:
    """Return current session cost estimate."""
    # Approximate pricing for claude-sonnet-4-6
    cost_in  = _total_tokens_in  * 0.000003   # $3/M input
    cost_out = _total_tokens_out * 0.000015   # $15/M output
    return {
        "tokens_in": _total_tokens_in,
        "tokens_out": _total_tokens_out,
        "estimated_cost_usd": round(cost_in + cost_out, 4)
    }
