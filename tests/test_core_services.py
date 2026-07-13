"""
Unit tests for core services — chunking, search, embeddings, context building.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.context_builder import ContextBuilder
from app.utils.token_manager import estimate_tokens, prioritize_and_trim
from app.schemas.search import SearchResult


# ── Helpers ────────────────────────────────────────────────────────────────

def make_result(file: str, name: str, score: float, content: str = "def foo(): pass") -> SearchResult:
    return SearchResult(repository="test-repo", file=file, type="function", name=name, score=score, content=content)


# ── Token manager ──────────────────────────────────────────────────────────

class TestTokenManager:
    def test_estimate_tokens_non_zero(self):
        tokens = estimate_tokens("Hello world, this is a test string.")
        assert tokens > 0

    def test_estimate_tokens_empty_string(self):
        tokens = estimate_tokens("")
        assert tokens >= 1  # returns max(1, ...)

    def test_prioritize_and_trim_sorts_by_score(self):
        results = [
            make_result("a.py", "low", 0.2),
            make_result("b.py", "high", 0.9),
            make_result("c.py", "mid", 0.5),
        ]
        trimmed = prioritize_and_trim(results)
        scores = [r.score for r in trimmed]
        assert scores == sorted(scores, reverse=True)

    def test_prioritize_and_trim_deduplicates(self):
        results = [
            make_result("a.py", "foo", 0.9),
            make_result("a.py", "foo", 0.5),  # duplicate, lower score
        ]
        trimmed = prioritize_and_trim(results)
        assert len(trimmed) == 1
        assert trimmed[0].score == 0.9

    def test_prioritize_and_trim_respects_token_budget(self):
        # Each chunk is ~500 chars = ~125 tokens; budget is 6000 tokens → max ~48 chunks
        big_content = "x" * 500
        results = [make_result(f"file{i}.py", f"fn{i}", 0.9 - i * 0.01, big_content) for i in range(100)]
        trimmed = prioritize_and_trim(results)
        assert len(trimmed) < 100


# ── Context builder ────────────────────────────────────────────────────────

class TestContextBuilder:
    def test_build_with_results(self):
        builder = ContextBuilder()
        results = [
            make_result("app/security.py", "create_token", 0.95, "def create_token(): pass"),
        ]
        context = builder.build(results)
        assert "app/security.py" in context
        assert "create_token" in context
        assert "def create_token" in context

    def test_build_empty_results(self):
        builder = ContextBuilder()
        context = builder.build([])
        assert "No relevant code context" in context

    def test_build_deduplicates(self):
        builder = ContextBuilder()
        results = [
            make_result("a.py", "foo", 0.9, "def foo(): pass"),
            make_result("a.py", "foo", 0.5, "def foo(): pass"),  # duplicate
        ]
        context = builder.build(results)
        # Should appear only once
        assert context.count("a.py") == 1
