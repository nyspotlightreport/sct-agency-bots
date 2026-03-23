"""Tests for core.base_bot module."""

import pytest
from core.base_bot import BaseBot
from core.exceptions import ConfigError


class SimpleBot(BaseBot):
    """Test bot that returns a fixed result."""
    def execute(self):
        return {"items_processed": 3, "status": "ok"}


class FailingBot(BaseBot):
    """Test bot that always fails."""
    def execute(self):
        raise ValueError("Something went wrong")


class TestBaseBot:
    def test_successful_run(self):
        bot = SimpleBot("test-simple")
        results = bot.run()
        assert results["items_processed"] == 3
        assert results["status"] == "ok"

    def test_failing_run_captures_error(self):
        bot = FailingBot("test-failing")
        results = bot.run()
        assert results["success"] is False
        assert "Something went wrong" in results["error"]
        assert "traceback" in results

    def test_missing_config_raises(self, monkeypatch):
        from core.config import Config
        monkeypatch.setattr(Config, "ANTHROPIC_API_KEY", "")
        with pytest.raises(ConfigError, match="Missing required config"):
            SimpleBot("test-config", required_config=["ANTHROPIC_API_KEY"])

    def test_execute_not_implemented(self):
        with pytest.raises(NotImplementedError):
            bot = BaseBot("test-abstract")
            bot.execute()

    def test_health_tracking(self):
        bot = SimpleBot("test-health-track")
        bot.run()
        stats = bot.health.get_stats()
        assert stats["total_runs"] == 1
        assert stats["success_rate"] == 100.0

    def test_logger_exists(self):
        bot = SimpleBot("test-logger")
        assert bot.logger is not None
        assert bot.logger.name == "test-logger"
