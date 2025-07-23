import strawberry
from app.services.otp_cache import otp_cache

@strawberry.type
class CacheStats:
    total_otps: int
    active_otps: int
    used_otps: int

@strawberry.type
class HealthQuery:
    @strawberry.field
    def cache_stats(self) -> CacheStats:
        """Get OTP cache statistics for monitoring"""
        stats = otp_cache.get_cache_stats()
        return CacheStats(
            total_otps=stats["total_otps"],
            active_otps=stats["active_otps"],
            used_otps=stats["used_otps"]
        )
