import os
import smtplib
import logging

from email.message import EmailMessage
from twilio.rest import Client

from .config import DEV_SHOW_OTP


logger = logging.getLogger("smarterp.notifications")


# ==========================================
# EMAIL NOTIFICATION
# ==========================================

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email using the configured SMTP provider."""

    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    port = int(os.getenv("SMTP_PORT", "587"))

    if not host or not user or not password:

        if DEV_SHOW_OTP:
            logger.warning(
                "SMTP not configured. Development email to %s:\n%s",
                to_email,
                body
            )
            return False

        raise RuntimeError("SMTP configuration is incomplete.")

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_FROM", user)
    msg["To"] = to_email

    msg.set_content(body)

    try:
        use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
        smtp_client = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

        with smtp_client(host, port, timeout=20) as server:
            server.ehlo()

            if not use_ssl and os.getenv("SMTP_USE_TLS", "true").lower() == "true":
                server.starttls()
                server.ehlo()

            server.login(user, password)

            server.send_message(msg)

        logger.info("Email successfully sent to %s", to_email)

        return True

    except (smtplib.SMTPException, OSError):

        logger.exception("Email sending failed.")

        raise


# ==========================================
# SMS NOTIFICATION
# ==========================================

def send_sms(to_phone: str, body: str) -> bool:
    """Send SMS using Twilio."""

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not sid or not token or not from_number:

        logger.error("Twilio configuration is incomplete.")

        return False

    try:

        client = Client(sid, token)

        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_phone
        )

        logger.info(
            "SMS submitted successfully. SID: %s",
            message.sid
        )

        return True

    except Exception:

        logger.exception("SMS sending failed.")

        raise