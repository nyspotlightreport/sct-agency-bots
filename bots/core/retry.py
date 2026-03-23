"""Retry decorator with exponential backoff."""

import time
import functools
from .config import Config


def with_retry(max_retries=None, delay=None, exceptions=(Exception,), logger=None):
    """Decorator: auto-retry on failure with exponential backoff."""
    _max = max_retries or Config.MAX_RETRIES
    _delay = delay or Config.RETRY_DELAY

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, _max + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    wait = _delay * (2 ** (attempt - 1))
                    msg = f"Attempt {attempt}/{_max} failed: {e}. Retrying in {wait:.1f}s..."
                    if logger:
                        logger.warning(msg)
                    if attempt < _max:
                        time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator
