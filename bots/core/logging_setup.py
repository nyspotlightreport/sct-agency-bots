"""Structured logging for agency bots."""

import json
import logging
from .config import Config


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output (useful in GitHub Actions)."""

    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "bot": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        })


def get_logger(bot_name: str, json_format: bool = False) -> logging.Logger:
    """Get or create a logger for the given bot name."""
    logger = logging.getLogger(bot_name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    if json_format:
        fmt = JSONFormatter()
    else:
        fmt = logging.Formatter(
            f"%(asctime)s [{bot_name.upper()}] %(levelname)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler
    log_file = Config.LOG_DIR / f"{bot_name}.log"
    try:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except (OSError, IOError):
        pass  # Skip file logging if directory isn't writable (e.g., in CI)

    return logger
