import asyncio
from app.services.email import MailtrapEmailService

async def test_mailtrap_service():
    print("🧪 Testing Mailtrap Email Service...")
    
    try:
        email_service = MailtrapEmailService()
        
        # Test email
        success = await email_service.send_email(
            to_email="vo.lo@northeastern.edu",
            subject="🧪 Test Email - NEU Course Scheduler",
            message="""
🎓 Welcome to NEU Course Scheduler!

This is a test email to verify Mailtrap integration.

Your test verification code is: 123456

If you can see this email in your Mailtrap inbox, everything is working correctly!

Best regards,
NEU Course Scheduler Team
            """.strip()
        )
        
        if success:
            print("✅ Mailtrap email sent successfully!")
            print("🔍 Check your Mailtrap inbox: https://mailtrap.io/inboxes")
        else:
            print("❌ Failed to send Mailtrap email")
            
    except Exception as e:
        print(f"❌ Mailtrap test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mailtrap_service())