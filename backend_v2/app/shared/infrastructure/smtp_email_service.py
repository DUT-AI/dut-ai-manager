"""SMTP email service implementation."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.settings import CommonSettings, SMTPSetting
from loguru import logger


class SmtpEmailService:
    """Send emails via SMTP. Ported from backend v1."""

    def __init__(self) -> None:
        smtp = SMTPSetting()
        common = CommonSettings()
        self.server = smtp.SMTP_SERVER
        self.port = smtp.SMTP_PORT
        self.username = smtp.SMTP_USER
        self.password = smtp.SMTP_PASSWORD
        self.from_email = smtp.EMAILS_FROM_EMAIL
        self.from_name = smtp.EMAILS_FROM_NAME
        self.frontend_host = common.FRONTEND_HOST.rstrip("/")

    def _send_email(
        self, to_email: str, subject: str, html_content: str
    ) -> None:
        if not self.username or not self.password:
            logger.warning("SMTP credentials not set. Email not sent.")
            return

        try:
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)
            msg_alternative.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")

    async def send_welcome_email(
        self, to_email: str, name: str, password: str
    ) -> None:
        """Send welcome email with credentials (runs sync SMTP in async context)."""
        subject = "Chào mừng đến với DUT AI Manager"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="margin:0;padding:0;background-color:#f4f6f9;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr><td align="center" style="padding:20px 0;">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600"
                           style="border-collapse:collapse;background-color:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                        <tr><td align="center" style="padding:0;">
                            <img src="https://minio.dutai.site/dut-ai-manager-prod/540975150_122103163550994716_7679218897607609211_n%20(1).png"
                                 alt="Welcome to DUT AI" width="600"
                                 style="display:block;width:100%;max-width:600px;height:auto;border-top-left-radius:16px;border-top-right-radius:16px;">
                        </td></tr>
                        <tr><td style="padding:20px 50px;">
                            <h1 style="color:#1a1a1a;margin:0 0 20px 0;font-size:24px;text-align:center;">Xin chào {name},</h1>
                            <p style="color:#4a5568;font-size:16px;line-height:1.6;margin-bottom:30px;text-align:center;">
                                Chào mừng bạn đến với <strong>DUT AI Manager</strong>. Tài khoản của bạn đã được khởi tạo thành công.
                            </p>
                            <div style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:25px;margin-bottom:30px;">
                                <div style="margin-bottom:15px;">
                                    <span style="display:block;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#718096;margin-bottom:5px;">Tên đăng nhập</span>
                                    <span style="display:block;font-size:18px;color:#2d3748;font-weight:600;">{to_email}</span>
                                </div>
                                <div>
                                    <span style="display:block;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#718096;margin-bottom:5px;">Mật khẩu</span>
                                    <code style="display:block;font-family:'Consolas','Monaco',monospace;font-size:20px;color:#3182ce;background-color:#ebf8ff;padding:10px;border-radius:6px;letter-spacing:2px;">{password}</code>
                                </div>
                            </div>
                            <div style="text-align:center;margin-bottom:30px;">
                                <a href="{self.frontend_host}" style="background-color:#3182ce;color:#fff;padding:14px 30px;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;display:inline-block;">Đăng nhập ngay</a>
                            </div>
                            <p style="color:#718096;font-size:14px;text-align:center;font-style:italic;">
                                Vui lòng đổi mật khẩu ngay sau khi đăng nhập lần đầu để bảo mật tài khoản.
                            </p>
                        </td></tr>
                        <tr><td style="background-color:#f7fafc;padding:20px;text-align:center;border-top:1px solid #edf2f7;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;">© 2024 DUT AI Manager. All rights reserved.</p>
                            <p style="margin:5px 0 0;color:#a0aec0;font-size:12px;">Đây là email tự động, vui lòng không trả lời.</p>
                        </td></tr>
                    </table>
                </td></tr>
            </table>
        </body>
        </html>
        """
        self._send_email(to_email, subject, html_content)
