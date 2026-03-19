#!/usr/bin/env python3
"""
AGENCY CORE — Shared utilities for all S.C. Thomas Internal Agency bots
Version: 2.0
Every bot imports from this module. Provides: retry logic, logging, health reporting,
alerting, Claude API, email, state management, and self-healing.
"""

import os
import json
import time
import logging
import smtplib
import hashlib
import traceback
import functools
import requests
from datetime import datetime, timezone
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── VERSION ──────────────────────────────────────────────────────────────────
AGENCY_CORE_VERSION = "2.0.0"

# ─── GLOBAL CONFIG ────────────────────────────────────────────────────────────
class Config:
    ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
    GMAIL_USER         = os.getenv("GMAIL_USER", "seanb041992@gmail.com")
    GMAIL_APP_PASS     = os.getenv("GMAIL_APP_PASS", "")
    CHAIRMAN_EMAIL     = os.getenv("CHAIRMAN_EMAIL", "seanb041992@gmail.com")
    AHREFS_API_KEY     = os.getenv("AHREFS_API_KEY", "")
    HUBSPOT_API_KEY    = os.getenv("HUBSPOT_API_KEY", "")
    APOLLO_API_KEY     = os.getenv("APOLLO_API_KEY", "")
    TARGET_DOMAIN      = os.getenv("TARGET_DOMAIN", "")
    PAYPAL_ME_LINK     = os.getenv("PAYPAL_ME_LINK", "https://paypal.me/yourhandle")
    PAYMENT_TERMS      = int(os.getenv("PAYMENT_TERMS", "15"))
    STATE_DIR          = Path(os.getenv("STATE_DIR", "./state"))
    LOG_DIR            = Path(os.getenv("LOG_DIR", "./logs"))
    MAX_RETRIES        = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY        = float(os.getenv("RETRY_DELAY", "2.0"))
    ALERT_ON_FAILURE   = os.getenv("ALERT_ON_FAILURE", "true").lower() == "true"

    @classmethod
    def validate(cls, required_keys: list) -> tuple:
        missing = [k for k in required_keys if not getattr(cls, k, None)]
        return len(missing) == 0, missing

# Create directories
Config.STATE_DIR.mkdir(exist_ok=True, parents=True)
Config.LOG_DIR.mkdir(exist_ok=True, parents=True)

# ─── LOGGING ──────────────────────────────────────────────────────────────────
def get_logger(bot_name: str) -> logging.Logger:
    logger = logging.getLogger(bot_name)
    if logger.handlers: return logger
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        f"%(asctime)s [{bot_name.upper()}] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File
    log_file = Config.LOG_DIR / f"{bot_name}.log"
    fh = logging.FileHandler(log_file)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

# ─── RETRY DECORATOR ──────────────────────────────────────────────────────────
def with_retry(max_retries=None, delay=None, exceptions=(Exception,), logger=None):
    """Decorator: auto-retry on failure with exponential backoff"""
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
                    wait = _delay * (2 ** (attempt - 1))  # exponential backoff
                    msg = f"Attempt {attempt}/{_max} failed: {e}. Retrying in {wait:.1f}s..."
                    if logger: logger.warning(msg)
                    else: print(f"⚠️  {msg}")
                    if attempt < _max: time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator

# ─── STATE MANAGEMENT ─────────────────────────────────────────────────────────
class StateManager:
    """Persistent key-value state across bot runs"""
    def __init__(self, bot_name: str):
        self.path = Config.STATE_DIR / f"{bot_name}_state.json"
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if self.path.exists():
                return json.loads(self.path.read_text())
        except: pass
        return {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self._data, indent=2, default=str))

    def all(self) -> dict:
        return self._data.copy()

# ─── HEALTH TRACKER ───────────────────────────────────────────────────────────
class HealthTracker:
    """Tracks bot run history, success/failure rates, and uptime"""
    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.state    = StateManager(f"{bot_name}_health")
        self.start_time = datetime.now(timezone.utc)

    def record_run(self, success: bool, details: str = "", items_processed: int = 0):
        history = self.state.get("history", [])
        history.append({
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "success":         success,
            "details":         details,
            "items_processed": items_processed,
            "duration_s":      round((datetime.now(timezone.utc) - self.start_time).total_seconds(), 2)
        })
        history = history[-50:]  # Keep last 50 runs

        runs        = len(history)
        successes   = sum(1 for r in history if r["success"])
        last_success = next((r["timestamp"] for r in reversed(history) if r["success"]), None)
        consecutive_failures = 0
        for r in reversed(history):
            if not r["success"]: consecutive_failures += 1
            else: break

        self.state.set("history", history)
        self.state.set("stats", {
            "total_runs":           runs,
            "success_rate":         round(successes / runs * 100, 1) if runs else 0,
            "last_success":         last_success,
            "consecutive_failures": consecutive_failures,
            "last_run":             history[-1]["timestamp"] if history else None
        })

        return consecutive_failures

    def get_stats(self) -> dict:
        return self.state.get("stats", {})

    def is_healthy(self) -> bool:
        stats = self.get_stats()
        return stats.get("consecutive_failures", 0) < 3

# ─── ALERT SYSTEM ─────────────────────────────────────────────────────────────
class AlertSystem:
    """Send alerts to Chairman via email"""

    @staticmethod
    def send(subject: str, body_html: str, severity: str = "INFO"):
        """Send alert email to Chairman"""
        colors = {"CRITICAL": "#c62828", "WARNING": "#f9a825", "INFO": "#1565c0", "SUCCESS": "#2e7d32"}
        color  = colors.get(severity, "#555")

        html = f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<div style="background:{color};color:#fff;padding:16px 20px;">
  <strong>{severity}: {subject}</strong>
  <span style="float:right;font-size:12px;opacity:0.8;">{datetime.now().strftime('%Y-%m-%d %H:%M ET')}</span>
</div>
<div style="padding:20px;">{body_html}</div>
</body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{severity}] {subject}"
        msg["From"]    = Config.GMAIL_USER
        msg["To"]      = Config.CHAIRMAN_EMAIL
        msg.attach(MIMEText(html, "html"))

        if not Config.GMAIL_APP_PASS:
            print(f"[AlertSystem] Would send {severity}: {subject}")
            return False

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(Config.GMAIL_USER, Config.GMAIL_APP_PASS)
                s.sendmail(Config.GMAIL_USER, Config.CHAIRMAN_EMAIL, msg.as_string())
            return True
        except Exception as e:
            print(f"[AlertSystem] Email failed: {e}")
            return False

    @staticmethod
    def bot_failure(bot_name: str, error: str, consecutive_failures: int):
        AlertSystem.send(
            subject  = f"Bot Failure: {bot_name} ({consecutive_failures}x consecutive)",
            body_html= f"<p><strong>Bot:</strong> {bot_name}<br><strong>Error:</strong> {error}<br><strong>Consecutive failures:</strong> {consecutive_failures}</p><p>The bot will auto-retry on next scheduled run. If failures persist, check env vars and API keys.</p>",
            severity = "CRITICAL" if consecutive_failures >= 3 else "WARNING"
        )

    @staticmethod
    def bot_recovered(bot_name: str):
        AlertSystem.send(
            subject  = f"Bot Recovered: {bot_name}",
            body_html= f"<p>{bot_name} is running successfully again. ✅</p>",
            severity = "SUCCESS"
        )

# ─── CLAUDE API CLIENT ────────────────────────────────────────────────────────
class ClaudeClient:
    """Unified Claude API client with retry and error handling"""
    BASE_URL = "https://api.anthropic.com/v1/messages"
    MODEL    = "claude-sonnet-4-20250514"

    @staticmethod
    @with_retry(max_retries=3, delay=2.0, exceptions=(requests.RequestException,))
    def complete(system: str, user: str, max_tokens: int = 1000, json_mode: bool = False) -> str:
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")

        headers = {
            "x-api-key":         Config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json"
        }
        payload = {
            "model":      ClaudeClient.MODEL,
            "max_tokens": max_tokens,
            "system":     system,
            "messages":   [{"role": "user", "content": user}]
        }
        r = requests.post(ClaudeClient.BASE_URL, headers=headers, json=payload, timeout=45)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]

        if json_mode:
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        return text

    @staticmethod
    def complete_safe(system: str, user: str, max_tokens: int = 1000, fallback=None):
        """Complete with fallback on failure"""
        try:
            return ClaudeClient.complete(system, user, max_tokens)
        except Exception as e:
            print(f"[ClaudeClient] Failed: {e}")
            return fallback

# ─── HTTP CLIENT ──────────────────────────────────────────────────────────────
class HTTPClient:
    """Robust HTTP client with retry, timeout, and user agent"""
    DEFAULT_HEADERS = {"User-Agent": "AgencyBot/2.0 (S.C. Thomas Internal Agency)"}

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

# ─── BASE BOT CLASS ───────────────────────────────────────────────────────────
class BaseBot:
    """
    All bots inherit from this. Provides:
    - Structured run loop with health tracking
    - Auto-alerting on failure
    - Recovery detection
    - State persistence
    - Logging
    """
    VERSION = "2.0.0"

    def __init__(self, name: str, required_config: list = None):
        self.name    = name
        self.logger  = get_logger(name)
        self.state   = StateManager(name)
        self.health  = HealthTracker(name)
        self.alerts  = AlertSystem()
        self.claude  = ClaudeClient
        self.http    = HTTPClient
        self.start   = datetime.now(timezone.utc)

        # Validate config
        if required_config:
            ok, missing = Config.validate(required_config)
            if not missing == []:
                self.logger.warning(f"Missing config: {missing}. Bot will run in degraded mode.")

    def execute(self) -> dict:
        """Override in subclass — main bot logic. Return results dict."""
        raise NotImplementedError

    def run(self) -> dict:
        """Main entry point — handles all lifecycle, health, alerting"""
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
                items_processed=items
            )

            # Recovery alert
            if not was_healthy:
                self.alerts.bot_recovered(self.name)
                self.logger.info(f"Recovered after previous failures ✅")

            self.logger.info(f"Complete in {duration}s | Items: {items}")

        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error(f"Failed: {e}\n{tb}")

            consecutive_failures = self.health.record_run(
                success=False,
                details=str(e)[:200]
            )

            if Config.ALERT_ON_FAILURE:
                self.alerts.bot_failure(self.name, str(e), consecutive_failures)

            results = {"success": False, "error": str(e), "traceback": tb}

        return results

    def log_summary(self, **kwargs):
        """Log a structured summary of what the bot did"""
        summary = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"Summary: {summary}")

    @property
    def cfg(self):
        return Config
