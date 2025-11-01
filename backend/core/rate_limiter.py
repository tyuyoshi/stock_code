"""Rate limiting configuration for API endpoints"""

import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings

logger = logging.getLogger(__name__)


def rate_limit_key_func(request: Request) -> str:
    """
    Get the key for rate limiting
    Uses IP address by default, but can be modified to use user ID for authenticated endpoints
    """
    # For authenticated endpoints, you can use user ID instead:
    # if hasattr(request.state, "user_id"):
    #     return f"user:{request.state.user_id}"
    return get_remote_address(request)


# Create limiter instance
# Enable rate limiting for non-development environments
rate_limit_enabled = settings.environment.lower() != "development"
logger.info(f"Rate limiting enabled: {rate_limit_enabled} (environment: {settings.environment})")

# Use Redis storage if Redis URL is configured, otherwise use in-memory storage
storage_uri = None
if settings.redis_url and rate_limit_enabled:
    # Use Redis for storage to persist rate limit data across restarts
    storage_uri = settings.redis_url
    logger.info(f"Using Redis storage for rate limiting: {storage_uri}")
else:
    logger.info("Using in-memory storage for rate limiting")

print(f"[RATE LIMITER] Enabled: {rate_limit_enabled}, Environment: {settings.environment}, Storage: {storage_uri or 'memory'}, Limits: {settings.api_rate_limit_per_minute}/min")

limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=[
        f"{settings.api_rate_limit_per_day}/day",
        f"{settings.api_rate_limit_per_hour}/hour",
        f"{settings.api_rate_limit_per_minute}/minute"
    ],
    enabled=rate_limit_enabled,
    storage_uri=storage_uri
)


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors
    """
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. {exc.detail}",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
        }
    )
    
    # Add Retry-After header if available
    if hasattr(exc, 'retry_after'):
        response.headers["Retry-After"] = str(exc.retry_after)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(exc.limit)
    response.headers["X-RateLimit-Remaining"] = "0"
    
    return response


# Decorator presets for common rate limits
class RateLimits:
    """Common rate limit presets"""
    
    # Strict limits for sensitive endpoints
    AUTH = f"5/minute"
    PASSWORD_RESET = f"3/hour"
    REGISTRATION = f"10/hour"
    
    # Standard limits for regular endpoints
    STANDARD = f"{settings.api_rate_limit_per_minute}/minute"
    
    # Relaxed limits for read-only endpoints
    READ_HEAVY = f"100/minute"
    
    # Very strict limits for expensive operations
    EXPENSIVE = f"10/minute"
    DATA_EXPORT = f"5/hour"
    BATCH_OPERATION = f"2/minute"


def get_rate_limit_decorator(limit: str):
    """
    Get a rate limit decorator with the specified limit
    
    Args:
        limit: Rate limit string (e.g., "10/minute")
        
    Returns:
        Rate limit decorator
    """
    return limiter.limit(limit)