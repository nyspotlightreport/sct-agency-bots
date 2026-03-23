"""Base bot class — all bots should inherit from this."""

import traceback
from datetime import datetime, timezone
from .config import Config
from .exceptions import ConfigError
from .logging_setup import get_logger
from .state import StateManager
from .health import HealthTracker
from .alerts import AlertSystem
from .claude_client import ClaudeClient
from .http_client import HTTPClient


class BaseBot:
    """
    All bots inherit from this. Provides:
    - Structured run loop with health tracking
    - Auto-alerting on failure
    - Recovery detection
    - State persistence
    - Logging
    """
    VERSION = "3.0.0"

    def __init__(self, name: str, required_config: list = None):
        self.name = name
        self.logger = get_logger(name)
        self.state = StateManager(name)
        self.health = HealthTracker(name)
        self.alerts = AlertSystem()
        self.claude = ClaudeClient
        self.http = HTTPClient
        self.start = datetime.now(timezone.utc)

        # Validate config — fail fast on missing required keys
        if required_config:
            ok, missing = Config.validate(required_config)
            if not ok:
                self.logger.error(f"Missing required config: {missing}")
                raise ConfigError(f"Missing required config: {', '.join(missing)}")

    def execute(self) -> dict:
        """Override in subclass — main bot logic. Return results dict."""
        raise NotImplementedError

    def run(self) -> dict:
        """Main entry point — handles all lifecycle, health, alerting."""
        self.logger.info(f"Starting v{self.VERSION}")
        was_healthy = self.health.is_healthy()
        results = {}

        try:
            results = self.execute()
            duration = round((datetime.now(timezone.utc) - self.start).total_seconds(), 2)
            items = results.get("items_processed", 0) if isinstance(results, dict) else 0

            consecutive_failures = self.health.record_run(
                success=True,
                details=str(results)[:200],
                items_processed=items,
            )

            # Recovery alert
            if not was_healthy:
                self.alerts.bot_recovered(self.name)
                self.logger.info("Recovered after previous failures")

            self.logger.info(f"Complete in {duration}s | Items: {items}")

        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error(f"Failed: {e}\n{tb}")

            consecutive_failures = self.health.record_run(
                success=False,
                details=str(e)[:200],
            )

            if Config.ALERT_ON_FAILURE:
                self.alerts.bot_failure(self.name, str(e), consecutive_failures)

            results = {"success": False, "error": str(e), "traceback": tb}

        return results

    def log_summary(self, **kwargs):
        """Log a structured summary of what the bot did."""
        summary = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"Summary: {summary}")

    @property
    def cfg(self):
        return Config
