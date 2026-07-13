"""
Integration tests for the Chat and Search API endpoints.
Uses TestClient to simulate real HTTP requests.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.search import SearchResult, SearchResponse
from app.schemas.chat import ChatResponse, SourceReference

client = TestClient(app)


def _mock_search_response(query: str) -> SearchResponse:
    return SearchResponse(
        query=query,
        results=[
            SearchResult(
                repository="test-repo",
                file="app/core/security.py",
                type="function",
                name="create_access_token",
                score=0.95,
                content="def create_access_token(data): ...",
            )
        ],
    )


def _mock_chat_response(question: str) -> ChatResponse:
    return ChatResponse(
        query=question,
        answer="JWT tokens are created in create_access_token() in app/core/security.py.",
        sources=[SourceReference(file="app/core/security.py", name="create_access_token", type="function")],
    )


# ── Search endpoint ────────────────────────────────────────────────────────

class TestSearchEndpoint:
    @patch("app.api.v1.search.SearchService")
    def test_search_repository_returns_200(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.search_repository.return_value = _mock_search_response("JWT")
        mock_svc_cls.return_value = mock_svc

        response = client.post(
            "/api/v1/search/test-repo",
            json={"query": "JWT", "top_k": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["query"] == "JWT"

    def test_search_missing_body_returns_422(self):
        response = client.post("/api/v1/search/test-repo", json={})
        assert response.status_code == 422


# ── Chat endpoint ──────────────────────────────────────────────────────────

class TestChatEndpoint:
    @patch("app.api.v1.chat.ChatService")
    def test_chat_repository_returns_200(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.chat.return_value = _mock_chat_response("How is JWT created?")
        mock_svc_cls.return_value = mock_svc

        response = client.post(
            "/api/v1/chat/test-repo",
            json={"question": "How is JWT created?", "history": [], "top_k": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data

    def test_chat_missing_question_returns_422(self):
        response = client.post("/api/v1/chat/test-repo", json={})
        assert response.status_code == 422


# ── Health endpoints ───────────────────────────────────────────────────────

class TestSystemEndpoints:
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_returns_healthy(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
