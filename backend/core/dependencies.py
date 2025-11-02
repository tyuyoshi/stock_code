"""FastAPI Dependencies"""

from typing import Generator
from redis import Redis
from services.yahoo_finance_client import YahooFinanceClient
from .config import settings
import logging

logger = logging.getLogger(__name__)


def get_redis_client() -> Redis:
    """Get Redis client instance"""
    try:
        if settings.redis_url:
            return Redis.from_url(settings.redis_url)
    except Exception as e:
        logger.warning(f"Failed to create Redis client: {e}")
    return None


def get_yahoo_finance_client() -> YahooFinanceClient:
    """Get Yahoo Finance client instance"""
    redis_client = get_redis_client()
    return YahooFinanceClient(redis_client=redis_client)