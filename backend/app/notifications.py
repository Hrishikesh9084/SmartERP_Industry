import os
import smtplib
import logging
from html import escape

from email.message import EmailMessage
from twilio.rest import Client

from .config import DEV_SHOW_OTP


logger = logging.getLogger("smarterp.notifications")


# ==========================================
# EMAIL NOTIFICATION
# ==========================================

def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> bool:
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
    reply_to = os.getenv("SMTP_REPLY_TO")
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Auto-Submitted"] = "auto-generated"
    msg["X-Auto-Response-Suppress"] = "All"

    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

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


def send_otp_email(
    to_email: str,
    otp: str,
    purpose: str,
    recipient_name: str | None = None,
) -> bool:
    """Send a branded, automatically generated OTP email."""

    purpose_label = "email verification" if purpose == "email_verification" else "secure sign-in"
    subject = f"Your SmartERP {purpose_label} code"
    safe_name = escape((recipient_name or "there").strip() or "there")
    safe_otp = escape(otp)
    expiry_minutes = escape(os.getenv("OTP_EXPIRY_MINUTES", "10"))

    body = (
        f"Hi {recipient_name or 'there'},\n\n"
        f"Your SmartERP {purpose_label} code is {otp}.\n"
        f"This code expires in {expiry_minutes} minutes. Do not share it with anyone.\n\n"
        "If you did not request this code, you can safely ignore this email.\n\n"
        "SmartERP\nThis is an automated message. Please do not reply."
    )
    html_body = f"""\
<!doctype html>
<html lang="en">
  <body style="margin:0;background:#f3f6fb;color:#172338;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6fb;padding:32px 16px;">
      <tr><td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 12px 35px rgba(23,35,56,.10);">
          <tr>
            <td style="padding:28px 32px;background:linear-gradient(135deg,#111d30,#245b9e);">
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="width:46px;height:46px;border-radius:14px;background:#4fd1c5;color:#111d30;font-size:26px;font-weight:800;text-align:center;vertical-align:middle;">S</td>
                  <td style="padding-left:12px;color:#ffffff;font-size:22px;font-weight:800;letter-spacing:.3px;">SmartERP</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:38px 32px 34px;">
              <p style="margin:0 0 10px;color:#60708a;font-size:14px;">Hi {safe_name},</p>
              <h1 style="margin:0;color:#111d30;font-size:28px;line-height:1.2;">Your secure code is ready</h1>
              <p style="margin:14px 0 26px;color:#60708a;font-size:15px;line-height:1.6;">
                Use this one-time code to complete your {escape(purpose_label)}.
              </p>
              <div style="padding:20px;text-align:center;background:#eef8f7;border:1px solid #c9eeea;border-radius:14px;">
                <span style="color:#111d30;font-size:36px;font-weight:800;letter-spacing:10px;">{safe_otp}</span>
              </div>
              <p style="margin:22px 0 0;color:#60708a;font-size:13px;line-height:1.6;">
                This code expires in <strong style="color:#172338;">{expiry_minutes} minutes</strong>.
                Never share it with anyone, including SmartERP support.
              </p>
              <p style="margin:24px 0 0;color:#8a96a8;font-size:12px;line-height:1.5;">
                If you did not request this code, you can safely ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 32px;background:#f8fafc;color:#8a96a8;font-size:11px;line-height:1.5;">
              This is an automated message from SmartERP. Please do not reply.
            </td>
          </tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""

    return send_email(to_email, subject, body, html_body)


def send_workspace_suspension_email(
    to_email: str,
    company_name: str,
    recipient_name: str | None = None,
) -> bool:
    """Notify a company user that their workspace was suspended."""

    safe_name = escape((recipient_name or "there").strip() or "there")
    safe_company = escape(company_name)
    subject = f"SmartERP workspace suspended: {company_name}"
    body = (
        f"Hi {recipient_name or 'there'},\n\n"
        f"Your SmartERP workspace, {company_name}, has been suspended by a platform administrator.\n"
        "You will not be able to sign in or access company data while it is suspended.\n"
        "Please contact your SmartERP administrator for assistance.\n\n"
        "SmartERP\nThis is an automated message. Please do not reply."
    )
    html_body = f"""\
<!doctype html>
<html lang="en">
  <body style="margin:0;background:#f3f6fb;color:#172338;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6fb;padding:32px 16px;">
      <tr><td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:20px;overflow:hidden;">
          <tr><td style="padding:28px 32px;background:#111d30;color:#ffffff;font-size:22px;font-weight:800;">SmartERP</td></tr>
          <tr><td style="padding:38px 32px 34px;">
            <p style="margin:0 0 10px;color:#60708a;font-size:14px;">Hi {safe_name},</p>
            <h1 style="margin:0;color:#111d30;font-size:28px;line-height:1.2;">Workspace suspended</h1>
            <p style="margin:14px 0 0;color:#60708a;font-size:15px;line-height:1.6;">
              The workspace <strong style="color:#172338;">{safe_company}</strong> has been suspended by a platform administrator.
              Sign-in and company data access are temporarily unavailable.
            </p>
            <p style="margin:22px 0 0;color:#60708a;font-size:13px;line-height:1.6;">
              Please contact your SmartERP administrator if you believe this was unexpected.
            </p>
          </td></tr>
          <tr><td style="padding:18px 32px;background:#f8fafc;color:#8a96a8;font-size:11px;">This is an automated message from SmartERP. Please do not reply.</td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""
    return send_email(to_email, subject, body, html_body)


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