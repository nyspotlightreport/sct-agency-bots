"""Shared test fixtures."""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add bots/ to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bots"))


@pytest.fixture(autouse=True)
def temp_state_dir(monkeypatch, tmp_path):
    """Use temp directories for state and logs during tests."""
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    (tmp_path / "state").mkdir()
    (tmp_path / "logs").mkdir()

    # Reload config to pick up new env vars
    from core.config import Config
    Config.STATE_DIR = tmp_path / "state"
    Config.LOG_DIR = tmp_path / "logs"

    return tmp_path
