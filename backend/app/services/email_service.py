"""Email service — send transactional emails."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Handles sending emails. Stub implementation — integrate with SMTP/SendGrid later."""

    @staticmethod
    async def send_email(to: str, subject: str, html_content: str) -> bool:
        """Send an email. Currently logs instead of sending."""
        if not settings.smtp_host:
            logger.info(f"[EMAIL] To: {to} | Subject: {subject} | Body: (omitted)")
            logger.warning("SMTP not configured — email not actually sent")
            return True  # Don't block registration

        try:
            # TODO: Implement actual email sending via aiosmtplib or SendGrid
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

    @staticmethod
    async def send_verification_email(to: str, token: str) -> bool:
        url = f"{settings.app_frontend_url}/verify-email?token={token}"
        html = f"<p>Click <a href='{url}'>here</a> to verify your email.</p>"
        return await EmailService.send_email(to, "Verify your email", html)

    @staticmethod
    async def send_password_reset_email(to: str, token: str) -> bool:
        url = f"{settings.app_frontend_url}/reset-password?token={token}"
        html = f"<p>Click <a href='{url}'>here</a> to reset your password.</p>"
        return await EmailService.send_email(to, "Reset your password", html)
