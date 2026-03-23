"""Tests for core.config module."""

import os
import pytest
from core.config import Config
from core.exceptions import ConfigError


class TestConfig:
    def test_validate_returns_ok_when_keys_present(self, monkeypatch):
        monkeypatch.setattr(Config, "ANTHROPIC_API_KEY", "test-key")
        ok, missing = Config.validate(["ANTHROPIC_API_KEY"])
        assert ok is True
        assert missing == []

    def test_validate_returns_missing_keys(self):
        ok, missing = Config.validate(["NONEXISTENT_KEY_12345"])
        assert ok is False
        assert "NONEXISTENT_KEY_12345" in missing

    def test_require_raises_on_missing(self):
        with pytest.raises(ConfigError, match="Missing required config"):
            Config.require(["NONEXISTENT_KEY_12345"])

    def test_require_passes_when_present(self, monkeypatch):
        monkeypatch.setattr(Config, "ANTHROPIC_API_KEY", "test-key")
        Config.require(["ANTHROPIC_API_KEY"])  # Should not raise

    def test_max_retries_is_int(self):
        assert isinstance(Config.MAX_RETRIES, int)
        assert Config.MAX_RETRIES >= 1

    def test_state_dir_is_path(self):
        from pathlib import Path
        assert isinstance(Config.STATE_DIR, Path)
