"""Persistent key-value state management for bots."""

import json
import logging
from .config import Config
from .exceptions import StateError


class StateManager:
    """Persistent key-value state across bot runs."""

    def __init__(self, bot_name: str):
        self.path = Config.STATE_DIR / f"{bot_name}_state.json"
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if self.path.exists():
                return json.loads(self.path.read_text())
        except (json.JSONDecodeError, IOError, OSError) as e:
            logging.getLogger(__name__).warning(f"State load failed for {self.path}: {e}")
        return {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def save(self):
        try:
            self.path.write_text(json.dumps(self._data, indent=2, default=str))
        except (IOError, OSError) as e:
            raise StateError(f"Failed to save state to {self.path}: {e}") from e

    def all(self) -> dict:
        return self._data.copy()
