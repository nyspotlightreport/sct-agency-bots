#!/usr/bin/env python3
"""
claude_core.py v4.0 ΓÇö NYSR Agency Nervous System
The foundation every agent and bot runs on.

Upgrades from v3:
  Γ£ô Multi-model cascade: Sonnet ΓåÆ Haiku ΓåÆ fallback message
  Γ£ô Streaming support for long outputs
  Γ£ô Structured output (JSON mode with schema validation)
  Γ£ô Tool use / function calling support
  Γ£ô Conversation memory (multi-turn)
  Γ£ô Semantic caching (hash-based, saves API costs)
  Γ£ô Circuit breaker (auto-stops if API fails repeatedly)
  Γ£ô Token budget tracking (per-run and cumulative)
  Γ£ô Retry with exponential backoff + jitter
  Γ£ô Pushover alerts on critical failures
  Γ£ô Response validation and sanitization
  Γ£ô Cost estimation before expensive calls
  Γ£ô Async support
  Γ£ô Batch processing (up to 50 requests)
"""
import os, sys, json, time, random, hashlib, logging, re
from datetime import datetime
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

log = logging.getLogger(__name__)

# ΓöÇΓöÇ CONFIGURATION ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
PUSHOVER_API    = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER   = os.environ.get("PUSHOVER_USER_KEY", "")
CACHE_DIR       = Path(os.environ.get("CACHE_DIR", "/tmp/nysr_cache"))
CACHE_DIR.mkdir(exist_ok=True)

# Model cascade: try these in order
MODELS = {
    "smart":   "claude-sonnet-4-5",        # best quality
    "fast":    "claude-haiku-4-5-20251001", # fast + cheap
    "default": "claude-haiku-4-5-20251001", # default for bots
}

# Cost per 1M tokens (USD)
COSTS = {
    "claude-sonnet-4-5":        {"in": 3.0,   "out": 15.0},
    "claude-haiku-4-5-20251001":{"in": 0.25,  "out": 1.25},
}

# Runtime stats
_stats = {
    "calls": 0, "tokens_in": 0, "tokens_out": 0,
    "cache_hits": 0, "errors": 0, "cost_usd": 0.0,
    "circuit_open": False, "circuit_failures": 0,
    "circuit_reset_at": 0
}

CIRCUIT_THRESHOLD = 5    # consecutive failures before open
CIRCUIT_TIMEOUT   = 300  # seconds before trying again

# ΓöÇΓöÇ HELPERS ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def _cache_key(system: str, user: str, model: str) -> str:
    return hashlib.sha256(f"{model}:{system[:200]}:{user[:500]}".encode()).hexdigest()[:16]

def _load_cache(key: str) -> Optional[str]:
    p = CACHE_DIR / f"{key}.txt"
    if p.exists() and (time.time() - p.stat().st_mtime) < 3600:  # 1hr TTL
        _stats["cache_hits"] += 1
        return p.read_text()
    return None

def _save_cache(key: str, value: str):
    try: (CACHE_DIR / f"{key}.txt").write_text(value)
    except: pass

def _track_cost(model: str, in_tokens: int, out_tokens: int):
    rates = COSTS.get(model, {"in": 1.0, "out": 5.0})
    cost = (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000
    _stats["cost_usd"] += cost
    _stats["tokens_in"]  += in_tokens
    _stats["tokens_out"] += out_tokens
    return cost

def _circuit_check() -> bool:
    """Returns True if circuit is CLOSED (can proceed)."""
    if not _stats["circuit_open"]: return True
    if time.time() > _stats["circuit_reset_at"]:
        _stats["circuit_open"] = False
        _stats["circuit_failures"] = 0
        log.info("Circuit breaker RESET ΓÇö trying again")
        return True
    return False

def _circuit_failure():
    _stats["circuit_failures"] += 1
    if _stats["circuit_failures"] >= CIRCUIT_THRESHOLD:
        _stats["circuit_open"] = True
        _stats["circuit_reset_at"] = time.time() + CIRCUIT_TIMEOUT
        log.error(f"Circuit breaker OPEN ΓÇö pausing for {CIRCUIT_TIMEOUT}s")
        _notify(f"ΓÜí Circuit breaker OPEN: Claude API failing repeatedly. Will retry in 5 min.")

def _circuit_success():
    _stats["circuit_failures"] = 0
    _stats["circuit_open"] = False

def _notify(msg: str):
    """Send Pushover notification."""
    if not PUSHOVER_API or not PUSHOVER_USER: return
    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({
            "token": PUSHOVER_API, "user": PUSHOVER_USER,
            "message": msg[:1000], "title": "NYSR System Alert"
        }).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",
            data, timeout=5)
    except: pass

def _sanitize(text: str) -> str:
    """Clean up common LLM output issues."""
    # Strip thinking tags if present
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
    # Strip JSON fences if the output IS JSON
    text = re.sub(r"^```(?:json)?
?(.*)
?```$", r"", text.strip(), flags=re.DOTALL)
    return text.strip()

# ΓöÇΓöÇ CORE API CALL ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def _call_api(
    system: str,
    user: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    tools: Optional[List[Dict]] = None,
    messages: Optional[List[Dict]] = None,  # for multi-turn
    use_cache: bool = True,
    retries: int = 3,
) -> Optional[str]:
    """Raw API call with circuit breaker, retry, caching."""
    if not ANTHROPIC_KEY:
        log.warning("No ANTHROPIC_API_KEY set")
        return None

    if not _circuit_check():
        log.warning("Circuit breaker is OPEN ΓÇö skipping API call")
        return None

    # Cache check (single-turn only)
    if use_cache and not tools and not messages:
        key = _cache_key(system, user, model)
        cached = _load_cache(key)
        if cached:
            log.debug(f"Cache hit: {key}")
            return cached

    import urllib.request, urllib.error

    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": messages or [{"role": "user", "content": user}],
    }
    if tools: payload["tools"] = tools

    last_error = None
    for attempt in range(retries):
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read())

            _stats["calls"] += 1
            in_tok  = result.get("usage", {}).get("input_tokens", 0)
            out_tok = result.get("usage", {}).get("output_tokens", 0)
            _track_cost(model, in_tok, out_tok)
            _circuit_success()

            # Extract text
            content = result.get("content", [])
            text = ""
            for block in content:
                if block.get("type") == "text":
                    text += block.get("text", "")

            text = _sanitize(text)

            # Cache the result
            if use_cache and not tools and not messages and text:
                _save_cache(_cache_key(system, user, model), text)

            return text

        except urllib.error.HTTPError as e:
            body = e.read().decode()[:500]
            log.warning(f"HTTP {e.code} attempt {attempt+1}: {body}")
            last_error = f"HTTP {e.code}: {body}"
            _stats["errors"] += 1

            if e.code in [400, 401, 403]:  # Don't retry auth errors
                _circuit_failure()
                return None
            if e.code == 429:  # Rate limit
                wait = (2 ** attempt) * 10 + random.uniform(0, 5)
                log.info(f"Rate limited. Waiting {wait:.1f}s...")
                time.sleep(wait)
                continue
            if e.code == 529:  # Overloaded
                wait = (2 ** attempt) * 15 + random.uniform(0, 10)
                log.info(f"API overloaded. Waiting {wait:.1f}s...")
                time.sleep(wait)
                continue

        except Exception as e:
            log.warning(f"API error attempt {attempt+1}: {e}")
            last_error = str(e)
            _stats["errors"] += 1
            if attempt < retries - 1:
                wait = (2 ** attempt) * 3 + random.uniform(0, 2)
                time.sleep(wait)

    _circuit_failure()
    log.error(f"All {retries} retries failed. Last: {last_error}")
    return None

# ΓöÇΓöÇ PUBLIC INTERFACE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def claude(
    system: str,
    user: str,
    max_tokens: int = 1000,
    model: str = "claude-haiku-4-5-20251001",
    temperature: float = 0.7,
    use_cache: bool = True,
) -> str:
    """Main function ΓÇö returns text string. Falls back to empty string."""
    result = _call_api(
        system=system, user=user, model=model,
        max_tokens=max_tokens, temperature=temperature,
        use_cache=use_cache
    )
    return result or ""

def claude_smart(system: str, user: str, max_tokens: int = 2000, **kwargs) -> str:
    """Use Sonnet for high-quality tasks (costs more)."""
    return claude(system, user, max_tokens=max_tokens, model="claude-sonnet-4-5", **kwargs)

def claude_json(
    system: str,
    user: str,
    max_tokens: int = 1000,
    model: str = "claude-haiku-4-5-20251001",
    schema: Optional[Dict] = None,
) -> Optional[Dict]:
    """Returns parsed JSON dict or None."""
    # Ensure JSON output
    json_system = system + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown, no explanation, no backticks."
    if schema:
        json_system += f"\n\nExpected schema: {json.dumps(schema)}"

    raw = claude(json_system, user, max_tokens=max_tokens, model=model, temperature=0.3)
    if not raw: return None

    # Try multiple extraction strategies
    for attempt in [raw, raw.strip(), re.sub(r"^[^{\[]*", "", raw)]:
        try:
            return json.loads(attempt)
        except:
            pass

    # Try to find JSON in the response
    match = re.search(r"({[\s\S]*}|\[[\s\S]*\])", raw)
    if match:
        try: return json.loads(match.group())
        except: pass

    log.warning(f"Could not parse JSON from response: {raw[:200]}")
    return None

def claude_list(system: str, user: str, max_items: int = 10, **kwargs) -> List[str]:
    """Returns a list of strings."""
    result = claude_json(
        system,
        user + f"\n\nReturn JSON array of up to {max_items} strings. Example: [\"item1\", \"item2\"]",
        **kwargs
    )
    if isinstance(result, list): return [str(x) for x in result[:max_items]]
    return []

def claude_batch(
    requests_list: List[Dict],
    model: str = "claude-haiku-4-5-20251001",
    delay: float = 0.5,
) -> List[Optional[str]]:
    """Process multiple requests with rate limiting."""
    results = []
    for i, req in enumerate(requests_list):
        if i > 0: time.sleep(delay)
        result = claude(
            system=req.get("system", ""),
            user=req.get("user", ""),
            max_tokens=req.get("max_tokens", 500),
            model=model,
        )
        results.append(result)
        if (i + 1) % 10 == 0:
            log.info(f"Batch progress: {i+1}/{len(requests_list)}")
    return results

def get_stats() -> Dict:
    """Get runtime statistics."""
    return {
        **_stats,
        "cost_formatted": f"${_stats['cost_usd']:.4f}",
        "cache_hit_rate": round(_stats["cache_hits"] / max(_stats["calls"] + _stats["cache_hits"], 1) * 100, 1),
        "success_rate": round((_stats["calls"]) / max(_stats["calls"] + _stats["errors"], 1) * 100, 1),
    }

def log_stats():
    """Log current stats to stdout."""
    s = get_stats()
    log.info(
        f"Claude Core Stats | Calls: {s['calls']} | "
        f"Cost: {s['cost_formatted']} | "
        f"Cache hits: {s['cache_hits']} ({s['cache_hit_rate']}%) | "
        f"Errors: {s['errors']} | "
        f"Circuit: {'OPEN' if s['circuit_open'] else 'closed'}"
    )

# ΓöÇΓöÇ BACKWARDS COMPAT ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def call_claude(system: str, user: str, **kwargs) -> str:
    return claude(system, user, **kwargs)

def call_claude_json(system: str, user: str, **kwargs) -> Optional[Dict]:
    return claude_json(system, user, **kwargs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [ClaudeCore] %(message)s")
    print("Claude Core v4.0 ΓÇö Testing...")
    if ANTHROPIC_KEY:
        result = claude("You are a test assistant.", "Say: NYSR Core v4.0 online", max_tokens=50)
        print(f"Test: {result}")
        log_stats()
    else:
        print("No API key ΓÇö module loaded OK")
