from typing import List, Optional, Generator

from app.schemas.chat import ChatMessage, ChatResponse, SourceReference
from app.schemas.search import SearchResult
from app.services.ai_service import AIService, AIServiceError
from app.services.context_builder import ContextBuilder
from app.services.search_service import SearchService
from app.utils.token_manager import prioritize_and_trim


class ChatService:
    """
    Orchestrates the full RAG pipeline:
    Question → Search → Token-trimmed Context → LLM → Grounded Answer + Sources
    """

    def __init__(self) -> None:
        self.search_service = SearchService()
        self.context_builder = ContextBuilder()
        self.ai_service = AIService()

    # ── Sync (full response at once) ───────────────────────────────────────

    def chat(
        self,
        question: str,
        repository: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        top_k: int = 5,
    ) -> ChatResponse:
        retrieved = self._retrieve(question, repository, top_k)
        context = self.context_builder.build(retrieved)

        answer = self.ai_service.answer_question(
            question=question,
            context=context,
            history=history or [],
        )

        sources = self._extract_sources(retrieved)
        return ChatResponse(answer=answer, sources=sources, query=question)

    # ── Streaming (token by token) ─────────────────────────────────────────

    def stream_chat(
        self,
        question: str,
        repository: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        top_k: int = 5,
    ) -> Generator[str, None, None]:
        """Yields tokens one by one from the LLM stream."""
        retrieved = self._retrieve(question, repository, top_k)
        context = self.context_builder.build(retrieved)

        yield from self.ai_service.stream_answer(
            question=question,
            context=context,
            history=history or [],
        )

    # ── Shared helpers ─────────────────────────────────────────────────────

    def _retrieve(
        self, question: str, repository: Optional[str], top_k: int
    ) -> List[SearchResult]:
        if repository:
            search_resp = self.search_service.search_repository(question, repository, top_k)
        else:
            search_resp = self.search_service.search_all(question, top_k)

        # Apply token-budget trimming and deduplication
        return prioritize_and_trim(search_resp.results)

    def _extract_sources(self, chunks: List[SearchResult]) -> List[SourceReference]:
        seen: set[str] = set()
        sources: List[SourceReference] = []

        for chunk in chunks:
            key = f"{chunk.file}::{chunk.name or ''}"
            if key not in seen:
                seen.add(key)
                sources.append(
                    SourceReference(file=chunk.file, name=chunk.name, type=chunk.type)
                )

        return sources
