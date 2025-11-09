import pytest
from sqlalchemy.exc import IntegrityError
from models.user import User


def test_create_user(db_session):
    user = User(
        google_id="google_123",
        email="test@example.com",
        name="Test User",
        profile_picture_url="https://example.com/pic.jpg",
        role="free",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.google_id == "google_123"
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.role == "free"
    assert user.is_active is True
    assert user.created_at is not None


def test_user_google_id_unique_constraint(db_session):
    user1 = User(
        google_id="google_123", email="user1@example.com", name="User 1", role="free"
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        google_id="google_123", email="user2@example.com", name="User 2", role="free"
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_email_unique_constraint(db_session):
    user1 = User(
        google_id="google_123", email="same@example.com", name="User 1", role="free"
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        google_id="google_456", email="same@example.com", name="User 2", role="free"
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_with_investment_profile(db_session):
    user = User(
        google_id="google_investor",
        email="investor@example.com",
        name="Investor User",
        role="premium",
        investment_experience="intermediate",
        investment_style="long_term",
        interested_industries=["technology", "finance", "healthcare"],
        email_notifications=True,
        price_alert_notifications=True,
    )
    db_session.add(user)
    db_session.commit()

    assert user.investment_experience == "intermediate"
    assert user.investment_style == "long_term"
    assert "technology" in user.interested_industries
    assert user.email_notifications is True


def test_user_default_values(db_session):
    user = User(
        google_id="google_default", email="default@example.com", name="Default User"
    )
    db_session.add(user)
    db_session.commit()

    assert user.role == "free"
    assert user.is_active is True
    assert user.email_notifications is True
    assert user.price_alert_notifications is True


def test_user_repr(db_session):
    user = User(
        google_id="google_repr",
        email="repr@example.com",
        name="Repr User",
        role="premium",
    )
    db_session.add(user)
    db_session.commit()

    repr_str = repr(user)
    assert "User" in repr_str
    assert str(user.id) in repr_str
    assert "repr@example.com" in repr_str
    assert "premium" in repr_str
