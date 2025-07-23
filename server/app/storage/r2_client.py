import boto3
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
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
            # Keep error logging for storage operations
            print(f"Error putting object {key}: {e}")
            return False
    
    def _delete_object(self, key: str) -> bool:
        """Delete object from R2"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            # Keep error logging for storage operations
            print(f"Error deleting object {key}: {e}")
            return False
    
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
# Create global R2 client instance
r2_client = R2Client()