"""Rate limiting configuration for API endpoints"""

import logging
import time
import asyncio
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from redis import Redis

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
# Enable rate limiting for all environments (with relaxed limits for development)
rate_limit_enabled = True  # Always enabled, but with different limits
logger.info(f"Rate limiting enabled: {rate_limit_enabled} (environment: {settings.environment})")

# Set rate limits based on environment
if settings.environment.lower() == "development":
    # Relaxed limits for development
    default_limits = [
        "100000/day",   # 100k requests per day
        "10000/hour",   # 10k requests per hour  
        "1000/minute"   # 1000 requests per minute
    ]
    logger.info("Using relaxed rate limits for development environment")
else:
    # Production/staging limits from settings
    default_limits = [
        f"{settings.api_rate_limit_per_day}/day",
        f"{settings.api_rate_limit_per_hour}/hour",
        f"{settings.api_rate_limit_per_minute}/minute"
    ]
    logger.info(f"Using configured rate limits: {settings.api_rate_limit_per_minute}/min")

# Use Redis storage if Redis URL is configured
storage_uri = None
if settings.redis_url:
    # Use Redis for storage to persist rate limit data across restarts
    storage_uri = settings.redis_url
    logger.info(f"Using Redis storage for rate limiting: {storage_uri}")
else:
    logger.info("Using in-memory storage for rate limiting")
    if settings.environment == "production":
        logger.warning("Redis not configured for production rate limiting - using memory storage")

print(f"[RATE LIMITER] Enabled: {rate_limit_enabled}, Environment: {settings.environment}, Storage: {storage_uri or 'memory'}, Limits: {default_limits[2]}")

limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=default_limits,
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


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter using Redis for distributed systems

    Tokens are added to bucket at constant rate (refill_rate).
    Each API call consumes 1 token.
    When bucket is empty, requests wait until tokens available.

    Redis keys:
    - {key_prefix}:tokens - Current token count (float)
    - {key_prefix}:last_refill - Last refill timestamp (float)

    Example:
        >>> limiter = TokenBucketRateLimiter(
        ...     redis_client=redis,
        ...     max_tokens=100,
        ...     refill_rate=0.5  # 30 requests/minute
        ... )
        >>> await limiter.acquire(1)  # Wait for and consume 1 token
        True
    """

    def __init__(
        self,
        redis_client: Redis,
        max_tokens: int = 100,
        refill_rate: float = 0.5,  # Tokens per second
        key_prefix: str = "rate_limit:yahoo_api"
    ):
        """
        Initialize Token Bucket Rate Limiter

        Args:
            redis_client: Redis client for distributed coordination
            max_tokens: Maximum bucket capacity (burst limit)
            refill_rate: Tokens added per second (average rate)
            key_prefix: Redis key prefix for isolation

        Raises:
            ValueError: If redis_client is None
        """
        if not redis_client:
            raise ValueError("Redis client is required for TokenBucketRateLimiter")

        self.redis = redis_client
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens_key = f"{key_prefix}:tokens"
        self.last_refill_key = f"{key_prefix}:last_refill"

        logger.info(
            f"TokenBucketRateLimiter initialized: "
            f"max_tokens={max_tokens}, refill_rate={refill_rate}/sec "
            f"({refill_rate * 60}/min, {refill_rate * 3600}/hour)"
        )

    async def acquire(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """
        Acquire tokens from bucket (wait if not available)

        This method will block until tokens are available or timeout is reached.
        Tokens are refilled automatically based on elapsed time.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            timeout: Max wait time in seconds (default: 30.0)

        Returns:
            True if tokens acquired, False if timeout

        Raises:
            ValueError: If tokens > max_tokens

        Example:
            >>> success = await limiter.acquire(1)
            >>> if success:
            ...     # Make API call
            ...     result = await api_call()
        """
        if tokens > self.max_tokens:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (max: {self.max_tokens})"
            )

        start_time = time.time()

        while True:
            # Refill tokens based on elapsed time
            await self._refill_tokens()

            # Try to consume tokens
            current_tokens = await self._get_tokens()

            if current_tokens >= tokens:
                # Consume tokens atomically
                new_count = await asyncio.to_thread(
                    self.redis.incrbyfloat,
                    self.tokens_key,
                    -tokens
                )

                # Double-check we didn't go negative (race condition)
                if new_count >= 0:
                    logger.debug(
                        f"Acquired {tokens} tokens. "
                        f"Remaining: {new_count:.2f}/{self.max_tokens}"
                    )
                    return True
                else:
                    # Undo the decrement (race condition occurred)
                    await asyncio.to_thread(
                        self.redis.incrbyfloat,
                        self.tokens_key,
                        tokens
                    )

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(
                    f"Token acquisition timeout after {elapsed:.2f}s. "
                    f"Current tokens: {current_tokens:.2f}"
                )
                return False

            # Wait for refill (adaptive based on tokens needed)
            wait_time = min(tokens / self.refill_rate, 1.0)
            logger.debug(
                f"Waiting {wait_time:.2f}s for tokens. "
                f"Need: {tokens}, Available: {current_tokens:.2f}"
            )
            await asyncio.sleep(wait_time)

    async def _refill_tokens(self):
        """
        Add tokens based on elapsed time (atomic Redis operation)

        Uses Lua script for atomic get-calculate-set to prevent race conditions.
        """
        now = time.time()

        # Use Lua script for atomic get-calculate-set
        lua_script = """
        local tokens_key = KEYS[1]
        local last_refill_key = KEYS[2]
        local now = tonumber(ARGV[1])
        local max_tokens = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])

        local last_refill = tonumber(redis.call('GET', last_refill_key) or now)
        local current_tokens = tonumber(redis.call('GET', tokens_key) or max_tokens)

        local elapsed = now - last_refill

        if elapsed >= 0.1 then
            local new_tokens = math.min(
                current_tokens + (elapsed * refill_rate),
                max_tokens
            )
            redis.call('SET', tokens_key, new_tokens)
            redis.call('SET', last_refill_key, now)
            return new_tokens
        end

        return current_tokens
        """

        try:
            result = await asyncio.to_thread(
                self.redis.eval,
                lua_script,
                2,  # Number of keys
                self.tokens_key,
                self.last_refill_key,
                now,
                self.max_tokens,
                self.refill_rate
            )
            return float(result)
        except Exception as e:
            logger.error(f"Failed to refill tokens: {e}")
            # Fallback: return current tokens without refill
            return await self._get_tokens()

    async def _get_tokens(self) -> float:
        """Get current token count from Redis"""
        tokens = await asyncio.to_thread(self.redis.get, self.tokens_key)
        return float(tokens) if tokens else self.max_tokens

    async def get_stats(self) -> dict:
        """
        Get current rate limiter statistics

        Returns:
            dict: Statistics including current tokens, utilization, etc.

        Example:
            >>> stats = await limiter.get_stats()
            >>> print(stats)
            {'current_tokens': 87.5, 'max_tokens': 100, 'refill_rate': 0.5,
             'utilization_percent': 12.5, 'last_refill': 1699876543.21}
        """
        current_tokens = await self._get_tokens()
        last_refill = await asyncio.to_thread(self.redis.get, self.last_refill_key)

        return {
            "current_tokens": round(current_tokens, 2),
            "max_tokens": self.max_tokens,
            "refill_rate": self.refill_rate,
            "utilization_percent": round(
                (1 - current_tokens / self.max_tokens) * 100, 2
            ),
            "last_refill": float(last_refill) if last_refill else None
        }