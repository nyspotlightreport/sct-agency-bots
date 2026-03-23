"""Robust HTTP client with retry, timeout, and user agent."""

import requests
from .retry import with_retry


class HTTPClient:
    """Robust HTTP client with retry, timeout, and user agent."""
    DEFAULT_HEADERS = {"User-Agent": "AgencyBot/3.0 (S.C. Thomas Internal Agency)"}

    @staticmethod
    @with_retry(max_retries=3, delay=1.5, exceptions=(requests.RequestException,))
    def get(url: str, params: dict = None, headers: dict = None, timeout: int = 15) -> requests.Response:
        h = {**HTTPClient.DEFAULT_HEADERS, **(headers or {})}
        r = requests.get(url, params=params, headers=h, timeout=timeout)
        r.raise_for_status()
        return r

    @staticmethod
    @with_retry(max_retries=3, delay=1.5, exceptions=(requests.RequestException,))
    def post(url: str, json_data: dict = None, headers: dict = None, timeout: int = 30) -> requests.Response:
        h = {**HTTPClient.DEFAULT_HEADERS, **(headers or {})}
        r = requests.post(url, json=json_data, headers=h, timeout=timeout)
        r.raise_for_status()
        return r
