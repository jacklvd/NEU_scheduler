import boto3
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
from app.config import settings

class R2Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name=settings.r2_region
        )
        self.bucket_name = settings.r2_bucket_name
        
    def _get_object(self, key: str) -> Optional[Dict[str, Any]]:
        """Get object from R2"""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise e
    
    def _put_object(self, key: str, data: Dict[str, Any]) -> bool:
        """Put object to R2"""
        try:
            json_data = json.dumps(data, default=str, indent=2)
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            return True
        except ClientError as e:
            print(f"Error putting object {key}: {e}")
            return False
    
    def _delete_object(self, key: str) -> bool:
        """Delete object from R2"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting object {key}: {e}")
            return False
    
    def _list_objects(self, prefix: str) -> List[str]:
        """List objects with prefix"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            print(f"Error listing objects with prefix {prefix}: {e}")
            return []
    
    # User operations
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        # Email is used as the key for easy lookup
        key = f"users/email/{email.lower()}.json"
        return self._get_object(key)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        key = f"users/id/{user_id}.json"
        return self._get_object(key)
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        # Generate unique user ID
        user_id = f"user_{int(datetime.now(timezone.utc).timestamp() * 1000000)}"
        
        # Add timestamps and ID
        user_data.update({
            "id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "is_verified": True
        })
        
        # Store by both email and ID for different lookup patterns
        email_key = f"users/email/{user_data['email'].lower()}.json"
        id_key = f"users/id/{user_id}.json"
        
        # Store the same data in both locations
        self._put_object(email_key, user_data)
        self._put_object(id_key, user_data)
        
        return user_data
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        # Get existing user data
        user_data = self.get_user_by_id(user_id)
        if not user_data:
            return False
        
        # Update data
        user_data.update(updates)
        user_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update both storage locations
        email_key = f"users/email/{user_data['email'].lower()}.json"
        id_key = f"users/id/{user_id}.json"
        
        return self._put_object(email_key, user_data) and self._put_object(id_key, user_data)
    
    # OTP operations
    def create_otp(self, email: str, code: str, purpose: str, expires_at: datetime) -> str:
        """Create OTP code"""
        otp_id = f"otp_{int(datetime.now(timezone.utc).timestamp() * 1000000)}"
        
        otp_data = {
            "id": otp_id,
            "email": email.lower(),
            "code": code,
            "purpose": purpose,
            "is_used": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        key = f"otps/{email.lower()}/{otp_id}.json"
        self._put_object(key, otp_data)
        
        return otp_id
    
    def get_valid_otp(self, email: str, code: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get valid OTP for verification"""
        # List all OTPs for this email
        prefix = f"otps/{email.lower()}/"
        otp_keys = self._list_objects(prefix)
        print(f"🔍 Looking for valid OTP: email={email}, purpose={purpose}, code_length={len(code) if code else 0}")
        print(f"📋 Found {len(otp_keys)} OTP records for email {email}")
        
        if not otp_keys:
            print(f"❌ No OTP records found for email={email}")
            return None
            
        current_time = datetime.now(timezone.utc)
        
        for otp_key in otp_keys:
            print(f"📝 Checking OTP record: {otp_key}")
            otp_data = self._get_object(otp_key)
            if not otp_data:
                print(f"⚠️ Could not retrieve OTP data for key {otp_key}")
                continue
            
            # Check if OTP matches criteria
            stored_code = otp_data.get("code", "")
            stored_purpose = otp_data.get("purpose", "")
            is_used = otp_data.get("is_used", False)
            expires_at_str = otp_data.get("expires_at", "")
            
            # Parse expiration time
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                is_expired = expires_at <= current_time
            except Exception as e:
                print(f"⚠️ Error parsing expiration time: {e}")
                is_expired = True
            
            # Log individual verification steps
            code_match = stored_code == code
            purpose_match = stored_purpose == purpose
            
            print(f"📊 OTP verification details:")
            print(f"   - Code match: {code_match} (expected: {code}, got: {stored_code})")
            print(f"   - Purpose match: {purpose_match} (expected: {purpose}, got: {stored_purpose})")
            print(f"   - Used: {is_used}")
            print(f"   - Expired: {is_expired} (expires at: {expires_at_str}, now: {current_time.isoformat()})")
            
            if code_match and purpose_match and not is_used and not is_expired:
                print(f"✅ Valid OTP found for {email}")
                return otp_data
            else:
                print(f"❌ OTP validation failed: code_match={code_match}, purpose_match={purpose_match}, is_used={is_used}, is_expired={is_expired}")
        
        print(f"❌ No valid OTP found for email={email}, purpose={purpose}")
        return None
    
    def mark_otp_used(self, email: str, otp_id: str) -> bool:
        """Mark OTP as used"""
        key = f"otps/{email.lower()}/{otp_id}.json"
        otp_data = self._get_object(key)
        
        if otp_data:
            otp_data["is_used"] = True
            otp_data["used_at"] = datetime.now(timezone.utc).isoformat()
            return self._put_object(key, otp_data)
        
        return False
    
    def cleanup_expired_otps(self, email: str) -> int:
        """Clean up expired OTPs for an email"""
        prefix = f"otps/{email.lower()}/"
        otp_keys = self._list_objects(prefix)
        
        current_time = datetime.now(timezone.utc)
        cleaned_count = 0
        
        for otp_key in otp_keys:
            otp_data = self._get_object(otp_key)
            if not otp_data:
                continue
            
            expires_at = datetime.fromisoformat(otp_data.get("expires_at").replace('Z', '+00:00'))
            if expires_at <= current_time or otp_data.get("is_used"):
                self._delete_object(otp_key)
                cleaned_count += 1
        
        return cleaned_count
    
    # Session operations
    def create_session(self, user_id: str, token: str, expires_at: datetime) -> bool:
        """Create user session"""
        session_data = {
            "user_id": user_id,
            "token": token,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        key = f"sessions/{token}.json"
        return self._put_object(key, session_data)
    
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Get session by token"""
        key = f"sessions/{token}.json"
        session_data = self._get_object(key)
        
        if session_data:
            # Check if session is still valid
            current_time = datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(session_data.get("expires_at").replace('Z', '+00:00'))
            
            if expires_at > current_time and session_data.get("is_active"):
                return session_data
        
        return None
    
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a session"""
        key = f"sessions/{token}.json"
        session_data = self._get_object(key)
        
        if session_data:
            session_data["is_active"] = False
            session_data["invalidated_at"] = datetime.now(timezone.utc).isoformat()
            return self._put_object(key, session_data)
        
        return False

# Create global R2 client instance
r2_client = R2Client()