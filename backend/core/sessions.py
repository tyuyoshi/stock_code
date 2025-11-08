import secrets
import json
from datetime import timedelta
from typing import Optional, Dict, Any
from redis import Redis

from core.config import settings


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_session(
    user_id: int, redis_client: Redis, additional_data: Optional[Dict[str, Any]] = None
) -> str:
    session_token = generate_session_token()

    session_data = {"user_id": user_id, **(additional_data or {})}

    ttl = timedelta(days=settings.session_expire_days)

    redis_key = f"session:{session_token}"
    redis_client.setex(redis_key, ttl, json.dumps(session_data))

    return session_token


def get_session(session_token: str, redis_client: Redis) -> Optional[Dict[str, Any]]:
    redis_key = f"session:{session_token}"

    data = redis_client.get(redis_key)
    if not data:
        return None

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def refresh_session(session_token: str, redis_client: Redis) -> bool:
    redis_key = f"session:{session_token}"

    if not redis_client.exists(redis_key):
        return False

    ttl = timedelta(days=settings.session_expire_days)
    redis_client.expire(redis_key, ttl)
    return True


def delete_session(session_token: str, redis_client: Redis) -> bool:
    redis_key = f"session:{session_token}"
    result = redis_client.delete(redis_key)
    return result > 0


def delete_all_user_sessions(user_id: int, redis_client: Redis) -> int:
    pattern = "session:*"
    deleted_count = 0

    for key in redis_client.scan_iter(match=pattern):
        data = redis_client.get(key)
        if data:
            try:
                session_data = json.loads(data)
                if session_data.get("user_id") == user_id:
                    redis_client.delete(key)
                    deleted_count += 1
            except json.JSONDecodeError:
                continue

    return deleted_count
