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
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Mailtrap email failed: {e}")
            print(f"❌ Failed to send email via Mailtrap: {e}")
            
            return False