"""Global configuration for all agency bots."""

import os
from pathlib import Path
from .exceptions import ConfigError

AGENCY_CORE_VERSION = "3.0.0"


class Config:
    ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
    GMAIL_USER         = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASS     = os.getenv("GMAIL_APP_PASS", "")
    CHAIRMAN_EMAIL     = os.getenv("CHAIRMAN_EMAIL", "")
    AHREFS_API_KEY     = os.getenv("AHREFS_API_KEY", "")
    HUBSPOT_API_KEY    = os.getenv("HUBSPOT_API_KEY", "")
    APOLLO_API_KEY     = os.getenv("APOLLO_API_KEY", "")
    TARGET_DOMAIN      = os.getenv("TARGET_DOMAIN", "")
    PAYPAL_ME_LINK     = os.getenv("PAYPAL_ME_LINK", "")
    PAYMENT_TERMS      = int(os.getenv("PAYMENT_TERMS", "15"))
    STATE_DIR          = Path(os.getenv("STATE_DIR", "./state"))
    LOG_DIR            = Path(os.getenv("LOG_DIR", "./logs"))
    MAX_RETRIES        = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY        = float(os.getenv("RETRY_DELAY", "2.0"))
    ALERT_ON_FAILURE   = os.getenv("ALERT_ON_FAILURE", "true").lower() == "true"

    @classmethod
    def validate(cls, required_keys: list) -> tuple:
        """Validate that required config keys are set. Returns (ok, missing_keys)."""
        missing = [k for k in required_keys if not getattr(cls, k, None)]
        return len(missing) == 0, missing

    @classmethod
    def require(cls, required_keys: list):
        """Validate required keys, raising ConfigError if any are missing."""
        ok, missing = cls.validate(required_keys)
        if not ok:
            raise ConfigError(f"Missing required config: {', '.join(missing)}")


# Create directories on import (safe for CI environments)
try:
    Config.STATE_DIR.mkdir(exist_ok=True, parents=True)
    Config.LOG_DIR.mkdir(exist_ok=True, parents=True)
except (OSError, PermissionError):
    pass  # Directories may not be writable in CI — bots handle this gracefully
