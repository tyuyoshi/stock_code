from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_redis_client
from core.auth import get_current_user, get_session_token
from core.sessions import create_session, delete_session
from core.config import settings
from models.user import User
from schemas.user import UserResponse, UserLoginResponse, LogoutResponse, ProfileUpdate
from services.google_oauth import get_google_oauth_client
from redis import Redis

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google/login")
async def google_login():
    try:
        oauth_client = get_google_oauth_client()
        authorization_url = oauth_client.get_authorization_url()
        return RedirectResponse(url=authorization_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/google/callback", response_model=UserLoginResponse)
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    response: Response = None,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
):
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required",
        )

    try:
        oauth_client = get_google_oauth_client()
        user_data = await oauth_client.authenticate(code)

        if not user_data.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified with Google",
            )

        google_id = user_data.get("google_id")
        email = user_data.get("email")
        name = user_data.get("name")
        profile_picture_url = user_data.get("profile_picture_url")

        user = db.query(User).filter(User.google_id == google_id).first()

        if user:
            user.name = name
            user.profile_picture_url = profile_picture_url
            user.last_login_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
        else:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_picture_url=profile_picture_url,
                role="free",
                is_active=True,
                email_notifications=True,
                price_alert_notifications=True,
                last_login_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Session service unavailable",
            )

        session_token = create_session(user.id, redis_client)

        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_token,
            httponly=settings.session_cookie_httponly,
            secure=settings.session_cookie_secure,
            samesite=settings.session_cookie_samesite,
            max_age=settings.session_expire_days * 24 * 60 * 60,
        )

        return UserLoginResponse(
            user=UserResponse.model_validate(user),
            session_token=session_token,
            message="Login successful",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = profile_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    session_token: Optional[str] = Depends(get_session_token),
    redis_client: Redis = Depends(get_redis_client),
    response: Response = None,
):
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session service unavailable",
        )

    delete_session(session_token, redis_client)

    response.delete_cookie(key=settings.session_cookie_name)

    return LogoutResponse(message="Logout successful")
