from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MailtrapEmailService:
    """Email service using Mailtrap Sandbox"""
    
    def __init__(self):
        """Initialize Mailtrap configuration"""
        try:
            self.conf = ConnectionConfig(
                MAIL_USERNAME=settings.mail_username,
                MAIL_PASSWORD=settings.mail_password,
                MAIL_FROM=settings.mail_from,
                MAIL_PORT=settings.mail_port,
                MAIL_SERVER=settings.mail_server,
                MAIL_FROM_NAME=settings.mail_from_name,
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True,
                TEMPLATE_FOLDER=None  # We'll use plain text
            )
            
            self.fast_mail = FastMail(self.conf)
            logger.info("✅ Mailtrap email service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Mailtrap service: {e}")
            raise e
    
    async def send_email(self, to_email: str, subject: str, message: str) -> bool:
        """Send email via Mailtrap Sandbox"""
        try:
            # Create message
            email_message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=message,
                subtype=MessageType.plain
            )
            
            # Send email
            await self.fast_mail.send_message(email_message)
            
            logger.info(f"📧 Email sent successfully to {to_email} via Mailtrap")
            print(f"📧 Email sent to Mailtrap inbox: {to_email}")
            print(f"🔍 Check your Mailtrap inbox at: https://mailtrap.io/inboxes")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Mailtrap email failed: {e}")
            print(f"❌ Failed to send email via Mailtrap: {e}")
            
            # Show helpful debug info
            self._show_debug_info(to_email, subject, message)
            
            return False
    
    def _show_debug_info(self, to_email: str, subject: str, message: str):
        """Show debug info when email fails"""
        print("\n" + "🔧 " + "="*60)
        print("DEBUG: Email Configuration")
        print("="*64)
        print(f"MAIL_SERVER: {settings.mail_server}")
        print(f"MAIL_PORT: {settings.mail_port}")
        print(f"MAIL_USERNAME: {settings.mail_username}")
        print(f"MAIL_FROM: {settings.mail_from}")
        print(f"TO_EMAIL: {to_email}")
        print(f"SUBJECT: {subject}")
        print("="*64)
        print("💡 Check:")
        print("1. Mailtrap credentials are correct")
        print("2. Mailtrap account is active")  
        print("3. Internet connection is working")
        print("4. No firewall blocking SMTP")
        print("="*64 + "\n")