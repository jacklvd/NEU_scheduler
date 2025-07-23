from typing import Protocol
from app.config import settings

class EmailServiceProtocol(Protocol):
    """Protocol for email services"""
    async def send_email(self, to_email: str, subject: str, message: str) -> bool:
        ...

def get_email_service() -> EmailServiceProtocol:
    """Get Mailtrap email service"""
    
    if not settings.mail_username or not settings.mail_password:
        raise ValueError(
            "❌ Mailtrap credentials missing! Please add MAIL_USERNAME and MAIL_PASSWORD to your .env file"
        )
    
    from app.services.email import MailtrapEmailService
    return MailtrapEmailService()