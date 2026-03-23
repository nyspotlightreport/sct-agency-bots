"""Tests for core.state module."""

import json
import pytest
from core.state import StateManager


class TestStateManager:
    def test_initial_state_is_empty(self):
        sm = StateManager("test-bot")
        assert sm.all() == {}

    def test_set_and_get(self):
        sm = StateManager("test-bot-sg")
        sm.set("key1", "value1")
        assert sm.get("key1") == "value1"

    def test_get_default(self):
        sm = StateManager("test-bot-default")
        assert sm.get("nonexistent", "fallback") == "fallback"

    def test_persistence(self):
        sm1 = StateManager("test-bot-persist")
        sm1.set("counter", 42)

        sm2 = StateManager("test-bot-persist")
        assert sm2.get("counter") == 42

    def test_all_returns_copy(self):
        sm = StateManager("test-bot-copy")
        sm.set("a", 1)
        data = sm.all()
        data["b"] = 2  # Modify the copy
        assert sm.get("b") is None  # Original should be unchanged

    def test_handles_corrupt_state_file(self, temp_state_dir):
        from core.config import Config
        state_file = Config.STATE_DIR / "test-bot-corrupt_state.json"
        state_file.write_text("not valid json{{{")

        sm = StateManager("test-bot-corrupt")
        assert sm.all() == {}  # Should gracefully fall back to empty
