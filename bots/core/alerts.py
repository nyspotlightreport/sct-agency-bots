"""Alert system for sending notifications to the Chairman."""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import Config


class AlertSystem:
    """Send alerts to Chairman via email."""

    @staticmethod
    def send(subject: str, body_html: str, severity: str = "INFO"):
        """Send alert email to Chairman."""
        colors = {"CRITICAL": "#c62828", "WARNING": "#f9a825", "INFO": "#1565c0", "SUCCESS": "#2e7d32"}
        color = colors.get(severity, "#555")

        html = f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<div style="background:{color};color:#fff;padding:16px 20px;">
  <strong>{severity}: {subject}</strong>
  <span style="float:right;font-size:12px;opacity:0.8;">{datetime.now().strftime('%Y-%m-%d %H:%M ET')}</span>
</div>
<div style="padding:20px;">{body_html}</div>
</body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{severity}] {subject}"
        msg["From"] = Config.GMAIL_USER
        msg["To"] = Config.CHAIRMAN_EMAIL
        msg.attach(MIMEText(html, "html"))

        if not Config.GMAIL_APP_PASS or not Config.GMAIL_USER:
            return False

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(Config.GMAIL_USER, Config.GMAIL_APP_PASS)
                s.sendmail(Config.GMAIL_USER, Config.CHAIRMAN_EMAIL, msg.as_string())
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Email failed: {e}")
            return False

    @staticmethod
    def bot_failure(bot_name: str, error: str, consecutive_failures: int):
        AlertSystem.send(
            subject=f"Bot Failure: {bot_name} ({consecutive_failures}x consecutive)",
            body_html=f"<p><strong>Bot:</strong> {bot_name}<br><strong>Error:</strong> {error}<br><strong>Consecutive failures:</strong> {consecutive_failures}</p>",
            severity="CRITICAL" if consecutive_failures >= 3 else "WARNING",
        )

    @staticmethod
    def bot_recovered(bot_name: str):
        AlertSystem.send(
            subject=f"Bot Recovered: {bot_name}",
            body_html=f"<p>{bot_name} is running successfully again.</p>",
            severity="SUCCESS",
        )
