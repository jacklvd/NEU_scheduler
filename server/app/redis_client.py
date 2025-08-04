"""
Centralized Redis client configuration with connection pooling
"""
import redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Redis connection pool with proper limits
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,  # Increased limit for multiple services
    retry_on_timeout=True,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30
)

# Shared Redis client instance
redis_client = redis.Redis(connection_pool=redis_pool)

def get_redis_client():
    """Get a Redis client instance with proper connection pooling"""
    return redis_client

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False
