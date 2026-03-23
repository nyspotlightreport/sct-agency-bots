"""Unified Claude API client with retry and error handling."""

import json
import requests
from .config import Config
from .retry import with_retry
from .exceptions import APIError


class ClaudeClient:
    """Unified Claude API client with retry and error handling."""
    BASE_URL = "https://api.anthropic.com/v1/messages"
    MODEL = "claude-sonnet-4-20250514"

    @staticmethod
    @with_retry(max_retries=3, delay=2.0, exceptions=(requests.RequestException,))
    def complete(system: str, user: str, max_tokens: int = 1000, json_mode: bool = False) -> str:
        if not Config.ANTHROPIC_API_KEY:
            raise APIError("ANTHROPIC_API_KEY not set")

        headers = {
            "x-api-key": Config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": ClaudeClient.MODEL,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        r = requests.post(ClaudeClient.BASE_URL, headers=headers, json=payload, timeout=45)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]

        if json_mode:
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        return text

    @staticmethod
    def complete_safe(system: str, user: str, max_tokens: int = 1000, fallback=None):
        """Complete with fallback on failure."""
        try:
            return ClaudeClient.complete(system, user, max_tokens)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Claude API failed: {e}")
            return fallback
