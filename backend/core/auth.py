from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_redis_client
from core.sessions import get_session
from core.constants import ROLE_HIERARCHY
from models.user import User
from redis import Redis

security = HTTPBearer(auto_error=False)


def get_session_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    cookie_token: Optional[str] = Cookie(None, alias="stockcode_session"),
) -> Optional[str]:
    if credentials:
        return credentials.credentials

    if cookie_token:
        return cookie_token

    return None


async def get_current_user(
    session_token: Optional[str] = Depends(get_session_token),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
) -> User:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session service unavailable",
        )

    session_data = get_session(session_token, redis_client)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session data"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} subscription or higher",
            )

        return current_user

    return role_checker


async def get_optional_user(
    session_token: Optional[str] = Depends(get_session_token),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
) -> Optional[User]:
    if not session_token or not redis_client:
        return None

    session_data = get_session(session_token, redis_client)
    if not session_data:
        return None

    user_id = session_data.get("user_id")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user
