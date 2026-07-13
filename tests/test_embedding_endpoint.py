from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import patch
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.embedding import router as embedding_router
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

    os.environ["XAI_API_KEY"] = "test-api-key"
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    del os.environ["XAI_API_KEY"]


@patch("app.services.embedding_service.OpenAI")
def test_embedding_endpoint_returns_embedding(mock_openai, client: TestClient) -> None:
    mock_client = mock_openai.return_value
    mock_response = SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])
    mock_client.embeddings.create.return_value = mock_response

    response = client.post(
        "/api/v1/embeddings/",
        json={"text": "Hello world"},
    )

    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3]


@patch("app.services.embedding_service.OpenAI")
def test_embedding_endpoint_handles_service_errors(mock_openai, client: TestClient) -> None:
    mock_client = mock_openai.return_value
    mock_client.embeddings.create.side_effect = Exception("network error")

    response = client.post(
        "/api/v1/embeddings/",
        json={"text": "Hello world"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Embedding provider request failed"
