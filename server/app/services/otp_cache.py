"""
In-memory OTP cache for temporary authentication codes.

This module handles OTP (One-Time Password) storage in memory rather than 
persistent storage, which is more appropriate for temporary data that expires
quickly (typically 5-10 minutes).

Benefits over persistent storage:
- Faster access (memory vs network calls)
- Automatic cleanup of expired data
- More secure (no persistent storage of sensitive codes)
- Cost effective (no storage costs for temporary data)
"""

from datetime import datetime, timezone
from typing import Dict, Optional, NamedTuple
import threading

class OTPRecord(NamedTuple):
    code: str
    purpose: str
    expires_at: datetime
    is_used: bool

class OTPCache:
    """In-memory cache for OTPs with automatic expiration"""
    
    def __init__(self):
        self._cache: Dict[str, OTPRecord] = {}
        self._lock = threading.Lock()
    
    def store_otp(self, email: str, code: str, purpose: str, expires_at: datetime) -> None:
        """Store OTP in cache"""
        with self._lock:
            # Clean expired OTPs first
            self._cleanup_expired()
            
            # Use email as key (only one active OTP per email)
            key = email.lower()
            self._cache[key] = OTPRecord(
                code=code,
                purpose=purpose,
                expires_at=expires_at,
                is_used=False
            )
    
    def verify_otp(self, email: str, code: str, purpose: str) -> bool:
        """Verify OTP and mark as used if valid"""
        with self._lock:
            # Clean expired OTPs first
            self._cleanup_expired()
            
            key = email.lower()
            otp_record = self._cache.get(key)
            
            if not otp_record:
                return False
            
            current_time = datetime.now(timezone.utc)
            
            # Check if expired
            if otp_record.expires_at <= current_time:
                del self._cache[key]  # Remove expired OTP
                return False
            
            # Check if already used
            if otp_record.is_used:
                return False
            
            # Check code and purpose match
            if otp_record.code != code or otp_record.purpose != purpose:
                return False
            
            # Mark as used
            self._cache[key] = otp_record._replace(is_used=True)
            return True
    
    def _cleanup_expired(self) -> None:
        """Remove expired OTPs from cache"""
        current_time = datetime.now(timezone.utc)
        expired_keys = [
            key for key, record in self._cache.items()
            if record.expires_at <= current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring"""
        with self._lock:
            self._cleanup_expired()
            total = len(self._cache)
            used = sum(1 for record in self._cache.values() if record.is_used)
            active = total - used
            
            return {
                "total_otps": total,
                "active_otps": active,
                "used_otps": used
            }

# Global cache instance
otp_cache = OTPCache()
