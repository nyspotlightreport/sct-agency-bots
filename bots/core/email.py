"""Shared email utility — replaces duplicated SMTP code across 25+ bots."""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import Config
from .exceptions import AlertError

logger = logging.getLogger(__name__)


class EmailSender:
    """Centralized email sending — use this instead of inline SMTP code."""

    def __init__(self, from_name: str = "NYSR Bot"):
        self.from_name = from_name
        self.user = Config.GMAIL_USER
        self.password = Config.GMAIL_APP_PASS

    def send(self, to: str, subject: str, body_html: str, reply_to: str = None) -> bool:
        """Send an HTML email. Returns True on success, raises AlertError on failure."""
        if not self.user or not self.password:
            logger.warning("Email not configured (GMAIL_USER or GMAIL_APP_PASS missing)")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.user}>"
        msg["To"] = to
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.user, self.password)
                server.sendmail(self.user, to, msg.as_string())
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email to {to} failed: {e}")
            raise AlertError(f"Email delivery failed: {e}") from e

    def send_to_chairman(self, subject: str, body_html: str) -> bool:
        """Convenience method to send to the Chairman."""
        if not Config.CHAIRMAN_EMAIL:
            logger.warning("CHAIRMAN_EMAIL not configured")
            return False
        return self.send(Config.CHAIRMAN_EMAIL, subject, body_html)
