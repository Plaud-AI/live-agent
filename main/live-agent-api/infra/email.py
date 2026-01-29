"""Email service for sending verification and password reset emails"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config import settings


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _send_email_sync(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Synchronous email sending (runs in thread pool)"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text part (fallback)
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            # Send email
            if self.use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls(context=context)
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, to_email, message.as_string())
            else:
                with smtplib.SMTP_SSL(self.host, self.port) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._send_email_sync,
            to_email,
            subject,
            html_content,
            text_content
        )
    
    async def send_verification_email(
        self, 
        to_email: str, 
        verification_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send email verification email"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = "Verify Your Email Address"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <tr>
                    <td style="padding: 40px 30px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">Live Agent</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 40px 30px;">
                        <h2 style="color: #333333; margin: 0 0 20px; font-size: 24px;">Verify Your Email Address</h2>
                        <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                            Hi{f' {user_name}' if user_name else ''},
                        </p>
                        <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                            Thank you for signing up! Please click the button below to verify your email address and complete your registration.
                        </p>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="text-align: center;">
                                    <a href="{verification_url}" 
                                       style="display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                        Verify Email
                                    </a>
                                </td>
                            </tr>
                        </table>
                        <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 30px 0 0;">
                            This link will expire in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.
                        </p>
                        <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 10px 0 0;">
                            If you didn't create an account, you can safely ignore this email.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 30px; background-color: #f8f9fa; text-align: center;">
                        <p style="color: #999999; font-size: 12px; margin: 0;">
                            © {settings.SMTP_FROM_NAME}. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email Address
        
        Hi{f' {user_name}' if user_name else ''},
        
        Thank you for signing up! Please click the link below to verify your email address:
        
        {verification_url}
        
        This link will expire in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.
        
        If you didn't create an account, you can safely ignore this email.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_email(
        self, 
        to_email: str, 
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Reset Your Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <tr>
                    <td style="padding: 40px 30px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">Live Agent</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 40px 30px;">
                        <h2 style="color: #333333; margin: 0 0 20px; font-size: 24px;">Reset Your Password</h2>
                        <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                            Hi{f' {user_name}' if user_name else ''},
                        </p>
                        <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                            We received a request to reset your password. Click the button below to create a new password.
                        </p>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="text-align: center;">
                                    <a href="{reset_url}" 
                                       style="display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                        Reset Password
                                    </a>
                                </td>
                            </tr>
                        </table>
                        <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 30px 0 0;">
                            This link will expire in {settings.PASSWORD_RESET_EXPIRE_HOURS} hour(s).
                        </p>
                        <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 10px 0 0;">
                            If you didn't request a password reset, you can safely ignore this email.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 30px; background-color: #f8f9fa; text-align: center;">
                        <p style="color: #999999; font-size: 12px; margin: 0;">
                            © {settings.SMTP_FROM_NAME}. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password
        
        Hi{f' {user_name}' if user_name else ''},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in {settings.PASSWORD_RESET_EXPIRE_HOURS} hour(s).
        
        If you didn't request a password reset, you can safely ignore this email.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()


