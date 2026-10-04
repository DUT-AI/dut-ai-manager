"""
Script to test EmailService by sending a welcome test email.
"""

from loguru import logger

from app.core.config import settings
from app.shared.infrastructure.email_service import EmailService


def main():
    logger.info("🔧 Checking SMTP configuration...")
    logger.info(f"  SMTP_SERVER: {settings.SMTP_SERVER}")
    logger.info(f"  SMTP_PORT: {settings.SMTP_PORT}")
    logger.info(f"  SMTP_USER: {settings.SMTP_USER}")
    logger.info(f"  EMAILS_FROM_EMAIL: {settings.EMAILS_FROM_EMAIL}")
    logger.info(
        f"  SMTP_PASSWORD is set: {bool(settings.SMTP_PASSWORD)} (length: {len(settings.SMTP_PASSWORD or '')})"
    )

    recipient = "huynhphuocnguyen.dev@gmail.com"
    logger.info(f"🚀 Sending test email to: {recipient} ...")

    email_service = EmailService()
    try:
        email_service.send_new_account_email(
            to_email=recipient,
            name="Huỳnh Phước Nguyên",
            password="DUT-TestPassword-123456",
        )
        logger.info("✅ Email sending completed! Please check your inbox / spam folder.")
    except Exception as e:
        logger.error(f"❌ Error while calling send_new_account_email: {e}")


if __name__ == "__main__":
    main()
