import pytest
from datetime import datetime
from decimal import Decimal

from models.user import User
from models.company import Company
from models.watchlist import Watchlist, WatchlistItem
from core.sessions import create_session


@pytest.fixture
def test_user(db_session):
    user = User(
        google_id="watchlist_test_user",
        email="watchlist@example.com",
        name="Watchlist Test User",
        role="free",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def premium_user(db_session):
    user = User(
        google_id="premium_test_user",
        email="premium@example.com",
        name="Premium User",
        role="premium",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_company(db_session):
    company = Company(
        ticker_symbol="9999",
        edinet_code="E00000",
        company_name_jp="テスト株式会社",
        company_name_en="Test Corporation",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_company_2(db_session):
    company = Company(
        ticker_symbol="8888",
        edinet_code="E00001",
        company_name_jp="サンプル株式会社",
        company_name_en="Sample Corporation",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def authenticated_client(client, test_user, redis_client):
    session_token = create_session(test_user.id, redis_client)
    client.headers = {"Authorization": f"Bearer {session_token}"}
    yield client
    client.headers = {}


@pytest.fixture
def premium_authenticated_client(client, premium_user, redis_client):
    session_token = create_session(premium_user.id, redis_client)
    client.headers = {"Authorization": f"Bearer {session_token}"}
    yield client
    client.headers = {}


@pytest.fixture
def test_watchlist(db_session, test_user):
    watchlist = Watchlist(
        user_id=test_user.id,
        name="My Watchlist",
        description="Test watchlist",
        is_public=False,
        display_order=0,
    )
    db_session.add(watchlist)
    db_session.commit()
    db_session.refresh(watchlist)
    return watchlist


def test_create_watchlist(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/watchlists/",
        json={
            "name": "New Watchlist",
            "description": "My first watchlist",
            "is_public": False,
            "display_order": 0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Watchlist"
    assert data["description"] == "My first watchlist"
    assert data["is_public"] is False


def test_create_watchlist_exceeds_limit(authenticated_client, db_session, test_user):
    watchlist = Watchlist(
        user_id=test_user.id, name="Existing", is_public=False, display_order=0
    )
    db_session.add(watchlist)
    db_session.commit()

    response = authenticated_client.post(
        "/api/v1/watchlists/",
        json={"name": "Second Watchlist", "is_public": False, "display_order": 0},
    )
    assert response.status_code == 403
    assert "Plan limit reached" in response.json()["detail"]


def test_get_watchlists(authenticated_client, test_watchlist):
    response = authenticated_client.get("/api/v1/watchlists/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "My Watchlist"


def test_get_watchlist_detail(authenticated_client, test_watchlist):
    response = authenticated_client.get(f"/api/v1/watchlists/{test_watchlist.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Watchlist"
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_watchlist_not_found(authenticated_client):
    response = authenticated_client.get("/api/v1/watchlists/99999")
    assert response.status_code == 404


def test_get_watchlist_unauthorized(authenticated_client, db_session, premium_user):
    other_watchlist = Watchlist(
        user_id=premium_user.id,
        name="Other's Watchlist",
        is_public=False,
        display_order=0,
    )
    db_session.add(other_watchlist)
    db_session.commit()

    response = authenticated_client.get(f"/api/v1/watchlists/{other_watchlist.id}")
    assert response.status_code == 403


def test_update_watchlist(authenticated_client, test_watchlist):
    response = authenticated_client.put(
        f"/api/v1/watchlists/{test_watchlist.id}",
        json={"name": "Updated Watchlist", "is_public": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Watchlist"
    assert data["is_public"] is True


def test_delete_watchlist(authenticated_client, test_watchlist):
    response = authenticated_client.delete(f"/api/v1/watchlists/{test_watchlist.id}")
    assert response.status_code == 204


def test_add_stock_to_watchlist(authenticated_client, test_watchlist, test_company):
    response = authenticated_client.post(
        f"/api/v1/watchlists/{test_watchlist.id}/stocks",
        json={
            "company_id": test_company.id,
            "display_order": 0,
            "memo": "Good company",
            "tags": ["tech", "growth"],
            "quantity": "100",
            "purchase_price": "1500.50",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == test_company.id
    assert data["memo"] == "Good company"
    assert data["tags"] == ["tech", "growth"]


def test_add_stock_company_not_found(authenticated_client, test_watchlist):
    response = authenticated_client.post(
        f"/api/v1/watchlists/{test_watchlist.id}/stocks",
        json={"company_id": 99999, "display_order": 0},
    )
    assert response.status_code == 404
    assert "Company not found" in response.json()["detail"]


def test_add_duplicate_stock(
    authenticated_client, db_session, test_watchlist, test_company
):
    item = WatchlistItem(
        watchlist_id=test_watchlist.id,
        company_id=test_company.id,
        display_order=0,
    )
    db_session.add(item)
    db_session.commit()

    response = authenticated_client.post(
        f"/api/v1/watchlists/{test_watchlist.id}/stocks",
        json={"company_id": test_company.id, "display_order": 0},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_add_stock_exceeds_limit(
    authenticated_client, db_session, test_watchlist, test_company
):
    for i in range(20):
        company = Company(
            ticker_symbol=f"{1000+i}",
            edinet_code=f"ELIMIT{i:03d}",
            company_name_jp=f"会社{i}",
        )
        db_session.add(company)
        db_session.flush()

        item = WatchlistItem(
            watchlist_id=test_watchlist.id,
            company_id=company.id,
            display_order=i,
        )
        db_session.add(item)
    db_session.commit()

    response = authenticated_client.post(
        f"/api/v1/watchlists/{test_watchlist.id}/stocks",
        json={"company_id": test_company.id, "display_order": 20},
    )
    assert response.status_code == 403
    assert "Plan limit reached" in response.json()["detail"]


def test_remove_stock_from_watchlist(
    authenticated_client, db_session, test_watchlist, test_company
):
    item = WatchlistItem(
        watchlist_id=test_watchlist.id,
        company_id=test_company.id,
        display_order=0,
    )
    db_session.add(item)
    db_session.commit()

    response = authenticated_client.delete(
        f"/api/v1/watchlists/{test_watchlist.id}/stocks/{test_company.id}"
    )
    assert response.status_code == 204


def test_remove_stock_not_found(authenticated_client, test_watchlist):
    response = authenticated_client.delete(
        f"/api/v1/watchlists/{test_watchlist.id}/stocks/99999"
    )
    assert response.status_code == 404


def test_premium_user_can_create_multiple_watchlists(premium_authenticated_client):
    for i in range(5):
        response = premium_authenticated_client.post(
            "/api/v1/watchlists/",
            json={
                "name": f"Watchlist {i}",
                "is_public": False,
                "display_order": i,
            },
        )
        assert response.status_code == 201

    response = premium_authenticated_client.get("/api/v1/watchlists/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_unauthenticated_access_denied(client):
    response = client.get("/api/v1/watchlists/")
    assert response.status_code == 401
