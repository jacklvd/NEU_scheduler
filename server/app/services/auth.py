import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.storage.r2_client import r2_client
from app.config import settings
from app.services.email_factory import get_email_service
from app.services.otp_cache import otp_cache


class AuthService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random OTP code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_jwt_token(data: Dict[str, Any]) -> str:
        """Generate JWT token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    async def send_otp_email(email: str, purpose: str) -> bool:
        """Generate and send OTP via Mailtrap"""
        try:
            # Generate OTP
            otp_code = AuthService.generate_otp(settings.otp_length)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)
            
            # Store OTP in cache (not persistent storage)
            otp_cache.store_otp(email, otp_code, purpose, expires_at)
            
            # Get Mailtrap email service
            email_service = get_email_service()
            subject = "Your NEU Course Scheduler Verification Code"
            
            # Create beautiful email content
            if purpose == "register":
                message = f"""
🎓 Welcome to NEU Course Scheduler!

Thank you for joining our platform to plan your academic journey at Northeastern University.

Your verification code is: {otp_code}

⏰ This code will expire in {settings.otp_expire_minutes} minutes.

Complete your registration to start:
• Searching courses with real-time availability
• Getting AI-powered course recommendations  
• Planning your entire academic schedule
• Tracking graduation requirements

If you didn't request this registration, please ignore this email.

Best regards,
The NEU Course Scheduler Team

---
Need help? This is a development environment using Mailtrap for testing.
                """.strip()
                
            elif purpose == "login":
                message = f"""
🔐 NEU Course Scheduler Login

Your login verification code is: {otp_code}

⏰ This code will expire in {settings.otp_expire_minutes} minutes.

Enter this code to access your account and continue planning your academic schedule.

🚨 If you didn't request this login, please secure your account immediately.

Best regards,
The NEU Course Scheduler Team

---
Need help? This is a development environment using Mailtrap for testing.
                """.strip()
                
            else:
                message = f"""
🔑 NEU Course Scheduler Verification

Your verification code is: {otp_code}

⏰ This code will expire in {settings.otp_expire_minutes} minutes.

Best regards,
The NEU Course Scheduler Team
                """.strip()
            
            # Send email via Mailtrap
            success = await email_service.send_email(
                to_email=email,
                subject=subject,
                message=message
            )
            
            if success:
                # Keep basic success logging for email operations
                pass
            else:
                # Keep error logging
                print(f"❌ Failed to send email to {email}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error in send_otp_email: {e}")
            return False
    
    @staticmethod
    def verify_otp(email: str, code: str, purpose: str) -> bool:
        """Verify OTP code"""
        try:
            # Use cache instead of R2 storage
            is_valid = otp_cache.verify_otp(email, code, purpose)
            
            return is_valid
            
        except Exception as e:
            print(f"❌ Error verifying OTP: {e}")
            return False
    
    @staticmethod
    def create_user(email: str, first_name: str, last_name: str, 
                   student_id: Optional[str] = None, graduation_year: Optional[int] = None, 
                   major: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user after OTP verification"""
        # Check if user already exists (even though we check during initial OTP request)
        existing_user = r2_client.get_user_by_email(email.lower())
        if existing_user:
            return existing_user
        
        user_data = {
            "email": email.lower(),
            "first_name": first_name,
            "last_name": last_name,
            "student_id": student_id,
            "graduation_year": graduation_year,
            "major": major,
            "is_verified": True  # User is verified since they completed OTP verification
        }
        
        created_user = r2_client.create_user(user_data)
        # Keep essential user creation logging
        print(f"✅ User created: {email} (ID: {created_user['id']})")
        return created_user
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return r2_client.get_user_by_email(email)
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return r2_client.get_user_by_id(user_id)