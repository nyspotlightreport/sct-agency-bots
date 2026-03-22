#!/usr/bin/env python3
"""
utils/cached_claude.py
Drop-in replacement for Claude API calls with prompt caching.
Reduces LLM costs by 90% on static system prompts.
All agents should import this instead of calling the API directly.

Usage:
  from utils.cached_claude import claude_cached
  response = claude_cached(prompt, system_prompt)
  # Static portions of system_prompt are cached — only charged 10% after first call
"""
import os, json, urllib.request, urllib.error, logging

log = logging.getLogger("cached_claude")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

# NYSR's universal system context — gets cached, charged at 10% after first call
NYSR_SYSTEM_CONTEXT = """You are an AI agent in the NYSR (NY Spotlight Report) autonomous agency system.

COMPANY: NY Spotlight Report — AI agency automation, Coram NY
CHAIRMAN: S.C. Thomas (Sean) — final authority on all decisions
MISSION: Profit + Speed to ROI + Respect

OFFERS (always lead with DFY for higher ticket):
- ProFlow AI $97/mo — automation starter (self-serve)
- ProFlow Growth $297/mo — full stack with BI dashboard
- ProFlow Elite $797/mo — growth + monthly strategy call + guarantee
- DFY Setup $997 setup + $497/mo — we build it for you
- DFY Agency $2,997 setup + $997/mo — enterprise + white-label
- NYSR Retainer $1,497/mo — ongoing enterprise partnership
- 30-Day Pilot $497 — zero risk trial that applies to DFY

GUARANTEES: 30-day money-back (all), 4 meetings/30days (Elite), live in 14 days (DFY), 10 meetings/90days (Agency)

STORE: nyspotlightreport.com/store/ — PayPal connected, live
PRICING: nyspotlightreport.com/pricing/
WEBINAR: nyspotlightreport.com/webinar/
AUDIT: nyspotlightreport.com/audit/
CX: nyspotlightreport.com/cx/

OPERATING RULES:
- Always execute. Never wait unless confidence < 0.70.
- Lead with DFY $1,497+ for operators/executives.
- Use ROI framing — reframe cost as comparison to status quo.
- Every prospect needs 7+ touchpoints. Never give up at 3.
- Ritz-Carlton standard on CX. Belkins precision on outreach.

TOP OBJECTIONS & RESPONSES:
- "Too expensive" → "Too expensive compared to what? You pay 3x our price in your own time."
- "Need to think" → "What specifically is giving you pause? Let's address it now."
- "Bad timing" → "What if we started a pilot now so Q3 decision is data-backed?"
- "Have a provider" → "What made you choose them? How's that working out?" (never attack)
- "Guarantee results?" → "Yes. [Specific deliverable] in [timeframe] or [specific consequence]."
"""

def claude_cached(
    prompt: str,
    system: str = "",
    max_tokens: int = 500,
    model: str = "claude-haiku-4-5-20251001"
) -> str:
    """
    Call Claude with prompt caching on the system prompt.
    Static context (NYSR_SYSTEM_CONTEXT) cached at 10% cost after first call.
    """
    if not ANTHROPIC:
        return ""

    # Build system with cache control on static portion
    system_blocks = [
        {
            "type": "text",
            "text": NYSR_SYSTEM_CONTEXT,
            "cache_control": {"type": "ephemeral"}  # Cache the static NYSR context
        }
    ]

    if system:
        system_blocks.append({
            "type": "text",
            "text": system  # Agent-specific context — not cached (changes per call)
        })

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_blocks,
        "messages": [{"role": "user", "content": prompt}]
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31"  # Enable caching
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            response = json.loads(r.read())
            # Log cache performance if available
            usage = response.get("usage",{})
            cache_read = usage.get("cache_read_input_tokens",0)
            cache_write = usage.get("cache_creation_input_tokens",0)
            if cache_read > 0:
                log.debug(f"Cache HIT: {cache_read} tokens read (90% cheaper)")
            elif cache_write > 0:
                log.debug(f"Cache WRITE: {cache_write} tokens written (next call 90% cheaper)")
            return response["content"][0]["text"]
    except urllib.error.HTTPError as e:
        log.warning(f"Claude API error: {e.code}")
        return ""
    except Exception as e:
        log.warning(f"Claude call failed: {e}")
        return ""
