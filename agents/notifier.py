# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
James Butler Notification Utility
Priority order: Pushover → ntfy.sh → Email → Log only
ntfy.sh requires zero setup on server side — Chairman installs app, subscribes to channel.
"""
import os, requests, logging

PUSHOVER_KEY = os.environ.get("PUSHOVER_API_KEY","")
PUSHOVER_USR = os.environ.get("PUSHOVER_USER_KEY","")
NTFY_CHANNEL = os.environ.get("NTFY_CHANNEL","nysr-chairman-alerts-xk9")
# AG-GMAIL-ZERO-HARD-DISABLED: GMAIL_USER   = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
# AG-GMAIL-ZERO-HARD-DISABLED: GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS","")

def notify(title: str, message: str, priority: int = 0, tags: list = None) -> bool:
    """Send notification via best available channel."""
    
    # Try Pushover first
    if PUSHOVER_KEY and PUSHOVER_USR:
        try:
            r = requests.post("https://api.pushover.net/1/messages.json",
                data={"token":PUSHOVER_KEY,"user":PUSHOVER_USR,
                      "message":message[:512],"title":title,"priority":priority},
                timeout=5)
            if r.status_code == 200:
                return True
        except Exception:  # noqa: bare-except

            pass
    # ntfy.sh fallback (free, no account)
    try:
        r = requests.post(f"https://ntfy.sh/{NTFY_CHANNEL}",
            json={"topic":NTFY_CHANNEL,"title":title,"message":message[:512],
                  "priority":max(1,min(5,priority+3)),"tags":tags or ["bell"]},
            headers={"Content-Type":"application/json"}, timeout=5)
        if r.status_code == 200:
            return True
    except Exception:  # noqa: bare-except

        pass
    # Email fallback
# AG-GMAIL-ZERO-HARD-DISABLED:     if GMAIL_PASS:
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(message)
# AG-GMAIL-ZERO-HARD-DISABLED:             msg["From"] = GMAIL_USER
# AG-GMAIL-ZERO-HARD-DISABLED:             msg["To"] = GMAIL_USER
            msg["Subject"] = f"[NYSR] {title}"
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP_SSL("[GMAIL-SMTP-REDACTED]", 465) as s:
# AG-NUCLEAR-GMAIL-ZERO-20260328:                 s.login(GMAIL_USER, GMAIL_PASS)
# AG-GMAIL-ZERO-HARD-DISABLED:                 s.send_message(msg)
            return True
        except Exception:  # noqa: bare-except

            pass
    logging.warning(f"NOTIFY (no channel): {title} — {message}")
    return False

if __name__ == "__main__":
    notify("Test", "James Butler notification system online", tags=["check"])
