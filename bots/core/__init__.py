"""
Agency Core — Modular bot framework v3.0

All classes and functions are re-exported here for backward compatibility.
Existing imports like `from agency_core import BaseBot` continue to work.
"""

from .config import Config, AGENCY_CORE_VERSION
from .exceptions import BotError, ConfigError, APIError, RateLimitError, StateError, AlertError
from .logging_setup import get_logger
from .retry import with_retry
from .state import StateManager
from .health import HealthTracker
from .alerts import AlertSystem
from .claude_client import ClaudeClient
from .http_client import HTTPClient
from .email import EmailSender
from .base_bot import BaseBot

__all__ = [
    "Config",
    "AGENCY_CORE_VERSION",
    "BotError",
    "ConfigError",
    "APIError",
    "RateLimitError",
    "StateError",
    "AlertError",
    "get_logger",
    "with_retry",
    "StateManager",
    "HealthTracker",
    "AlertSystem",
    "ClaudeClient",
    "HTTPClient",
    "EmailSender",
    "BaseBot",
]
