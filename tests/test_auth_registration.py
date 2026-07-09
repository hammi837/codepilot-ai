from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.auth import router as auth_router
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    import app.db.session as db_session

    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api/v1")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_register_user_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hammad@example.com",
            "username": "hammad",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "hammad@example.com"
    assert payload["username"] == "hammad"
    assert "id" in payload
    assert "password" not in payload


def test_login_and_get_current_user(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "hammad@example.com",
            "username": "hammad",
            "password": "StrongPassword123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "hammad@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 200
    token_payload = login_response.json()
    assert token_payload["token_type"] == "bearer"
    assert "access_token" in token_payload

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "hammad@example.com"


def test_protected_route_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
