#!/usr/bin/env python3
"""
AGENCY CORE — Backward-compatible shim (v3.0)

This file re-exports everything from the new modular `core/` package.
All existing imports continue to work:
    from agency_core import BaseBot, Config, ClaudeClient, etc.

For new code, prefer importing from the core package directly:
    from core import BaseBot
    from core.email import EmailSender
    from core.exceptions import APIError
"""

import os, sys

# Ensure bots/ directory is on path so `core` package is importable
_bots_dir = os.path.dirname(os.path.abspath(__file__))
if _bots_dir not in sys.path:
    sys.path.insert(0, _bots_dir)

from core import *  # noqa: F401,F403
from core import (
    Config,
    AGENCY_CORE_VERSION,
    get_logger,
    with_retry,
    StateManager,
    HealthTracker,
    AlertSystem,
    ClaudeClient,
    HTTPClient,
    BaseBot,
    EmailSender,
    BotError,
    ConfigError,
    APIError,
    RateLimitError,
    StateError,
    AlertError,
)
