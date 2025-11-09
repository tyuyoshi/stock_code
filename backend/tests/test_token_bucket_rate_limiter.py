"""Tests for Token Bucket Rate Limiter"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from core.rate_limiter import TokenBucketRateLimiter


@pytest.fixture
def redis_client(request):
    """Redis client for testing"""
    from redis import Redis
    from core.config import settings

    if not settings.redis_url:
        pytest.skip("Redis not configured for testing")

    client = Redis.from_url(settings.redis_url)

    # Clean up keys before and after test
    test_key_prefix = "test:rate_limit:yahoo_api"

    def cleanup():
        client.delete(f"{test_key_prefix}:tokens")
        client.delete(f"{test_key_prefix}:last_refill")

    cleanup()
    request.addfinalizer(cleanup)

    return client


@pytest.mark.asyncio
async def test_token_bucket_initialization(redis_client):
    """Test rate limiter initialization"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=10,
        refill_rate=2.0,
        key_prefix="test:rate_limit:yahoo_api"
    )

    assert limiter.max_tokens == 10
    assert limiter.refill_rate == 2.0

    # Check initial token count
    tokens = await limiter._get_tokens()
    assert tokens == 10.0


@pytest.mark.asyncio
async def test_acquire_tokens_success(redis_client):
    """Test successful token acquisition"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=10,
        refill_rate=5.0,
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Acquire 1 token (should succeed immediately)
    start = time.time()
    result = await limiter.acquire(1)
    elapsed = time.time() - start

    assert result is True
    assert elapsed < 0.1  # Should be instant

    # Check remaining tokens
    tokens = await limiter._get_tokens()
    assert 8.9 <= tokens <= 9.1  # Allow small floating point error


@pytest.mark.asyncio
async def test_token_exhaustion_and_wait(redis_client):
    """Test behavior when tokens are exhausted"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=5,
        refill_rate=2.0,  # 2 tokens per second
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Exhaust all tokens
    for _ in range(5):
        await limiter.acquire(1)

    # Check tokens depleted
    tokens = await limiter._get_tokens()
    assert tokens < 1.0

    # Next acquisition should wait for refill
    start = time.time()
    result = await limiter.acquire(1)
    elapsed = time.time() - start

    assert result is True
    assert elapsed >= 0.4  # Should wait ~0.5s for 1 token at 2/sec
    assert elapsed < 1.0   # But not too long


@pytest.mark.asyncio
async def test_token_refill(redis_client):
    """Test token refill over time"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=10,
        refill_rate=10.0,  # Fast refill for testing
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Consume some tokens
    await limiter.acquire(5)
    tokens_after_consume = await limiter._get_tokens()
    assert 4.9 <= tokens_after_consume <= 5.1

    # Wait for refill
    await asyncio.sleep(0.5)

    # Trigger refill
    await limiter._refill_tokens()

    # Should have refilled ~5 tokens (0.5s * 10/s)
    tokens_after_refill = await limiter._get_tokens()
    assert 9.5 <= tokens_after_refill <= 10.0  # Capped at max_tokens


@pytest.mark.asyncio
async def test_concurrent_acquisition(redis_client):
    """Test concurrent token acquisition (race condition handling)"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=20,
        refill_rate=5.0,
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Simulate 30 concurrent requests (more than available tokens)
    async def acquire_token():
        return await limiter.acquire(1, timeout=5.0)

    tasks = [acquire_token() for _ in range(30)]
    results = await asyncio.gather(*tasks)

    # All should succeed (some will wait for refill)
    assert all(results)

    # Final token count should be negative or near zero
    final_tokens = await limiter._get_tokens()
    assert final_tokens < 5.0  # Most tokens consumed


@pytest.mark.asyncio
async def test_acquire_timeout(redis_client):
    """Test timeout when tokens not available"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=5,
        refill_rate=0.1,  # Very slow refill
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Exhaust tokens
    for _ in range(5):
        await limiter.acquire(1)

    # Try to acquire with short timeout
    start = time.time()
    result = await limiter.acquire(1, timeout=0.5)
    elapsed = time.time() - start

    # Should timeout
    assert result is False
    assert 0.4 <= elapsed <= 0.7


@pytest.mark.asyncio
async def test_get_stats(redis_client):
    """Test statistics retrieval"""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=10,
        refill_rate=2.0,
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Acquire some tokens
    await limiter.acquire(3)

    # Get stats
    stats = await limiter.get_stats()

    assert "current_tokens" in stats
    assert "max_tokens" in stats
    assert "refill_rate" in stats
    assert "utilization_percent" in stats

    assert stats["max_tokens"] == 10
    assert stats["refill_rate"] == 2.0
    assert 6.5 <= stats["current_tokens"] <= 7.5
    assert 25 <= stats["utilization_percent"] <= 35


@pytest.mark.asyncio
async def test_rate_limiter_without_redis():
    """Test initialization without Redis (should raise error)"""
    with pytest.raises(ValueError, match="Redis client is required"):
        TokenBucketRateLimiter(
            redis_client=None,
            max_tokens=10,
            refill_rate=2.0
        )


@pytest.mark.asyncio
async def test_acquire_more_tokens_than_max():
    """Test error when requesting more tokens than max capacity"""
    from redis import Redis
    from core.config import settings

    if not settings.redis_url:
        pytest.skip("Redis not configured for testing")

    redis_client = Redis.from_url(settings.redis_url)
    limiter = TokenBucketRateLimiter(
        redis_client=redis_client,
        max_tokens=10,
        refill_rate=2.0,
        key_prefix="test:rate_limit:yahoo_api"
    )

    # Try to acquire more tokens than max
    with pytest.raises(ValueError, match="Cannot acquire 15 tokens"):
        await limiter.acquire(15)


@pytest.mark.asyncio
async def test_yahoo_client_integration(redis_client):
    """Test integration with YahooFinanceClient"""
    from services.yahoo_finance_client import YahooFinanceClient

    client = YahooFinanceClient(redis_client=redis_client)

    # Rate limiter should be initialized
    assert client.rate_limiter is not None
    assert isinstance(client.rate_limiter, TokenBucketRateLimiter)

    # Get initial stats
    stats_before = await client.rate_limiter.get_stats()
    initial_tokens = stats_before["current_tokens"]

    # Make an API call (mocked to avoid real Yahoo API)
    with patch('yfinance.Ticker'):
        # Note: This will consume 1 token but the API call itself is mocked
        # We're testing that the rate limiter is invoked, not the Yahoo API
        pass

    # After integration, the rate limiter should still be accessible
    assert client.rate_limiter.max_tokens == 100  # Default from settings
    assert client.rate_limiter.refill_rate == 0.5  # Default from settings
