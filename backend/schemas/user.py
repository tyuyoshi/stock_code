from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    google_id: str
    profile_picture_url: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    investment_experience: Optional[str] = Field(
        None, description="beginner, intermediate, advanced"
    )
    investment_style: Optional[str] = Field(
        None, description="long_term, short_term, swing"
    )
    interested_industries: Optional[List[str]] = None
    email_notifications: Optional[bool] = None
    price_alert_notifications: Optional[bool] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    investment_experience: Optional[str] = Field(
        None, description="Investment experience level"
    )
    investment_style: Optional[str] = Field(
        None, description="Investment style preference"
    )
    interested_industries: Optional[List[str]] = Field(
        None, description="List of interested industry codes"
    )
    email_notifications: Optional[bool] = Field(
        None, description="Enable email notifications"
    )
    price_alert_notifications: Optional[bool] = Field(
        None, description="Enable price alert notifications"
    )

    @field_validator("investment_experience")
    @classmethod
    def validate_experience(cls, v):
        if v is not None:
            allowed = ["beginner", "intermediate", "advanced"]
            if v not in allowed:
                raise ValueError(
                    f'investment_experience must be one of: {", ".join(allowed)}'
                )
        return v

    @field_validator("investment_style")
    @classmethod
    def validate_style(cls, v):
        if v is not None:
            allowed = [
                "long_term",
                "short_term",
                "swing",
                "day_trading",
                "value",
                "growth",
            ]
            if v not in allowed:
                raise ValueError(
                    f'investment_style must be one of: {", ".join(allowed)}'
                )
        return v


class UserResponse(BaseModel):
    id: int
    google_id: str
    email: EmailStr
    name: str
    profile_picture_url: Optional[str] = None
    investment_experience: Optional[str] = None
    investment_style: Optional[str] = None
    interested_industries: Optional[List[str]] = None
    email_notifications: bool
    price_alert_notifications: bool
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    user: UserResponse
    session_token: str
    message: str = "Login successful"


class LogoutResponse(BaseModel):
    message: str = "Logout successful"
