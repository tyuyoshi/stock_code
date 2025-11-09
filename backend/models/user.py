from sqlalchemy import Column, Integer, String, DateTime, Boolean, ARRAY, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    profile_picture_url = Column(String(512))

    investment_experience = Column(String(50))
    investment_style = Column(String(50))
    interested_industries = Column(ARRAY(String))

    email_notifications = Column(Boolean, default=True)
    price_alert_notifications = Column(Boolean, default=True)

    role = Column(String(50), default="free", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    last_login_at = Column(DateTime)

    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
