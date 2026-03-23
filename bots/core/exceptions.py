"""Custom exception types for the agency bot framework."""


class BotError(Exception):
    """Base exception for all bot errors."""
    pass


class ConfigError(BotError):
    """Raised when required configuration is missing or invalid."""
    pass


class APIError(BotError):
    """Raised when an external API call fails."""
    pass


class RateLimitError(APIError):
    """Raised when an API rate limit is hit."""
    pass


class StateError(BotError):
    """Raised when state management fails."""
    pass


class AlertError(BotError):
    """Raised when alert delivery fails."""
    pass
