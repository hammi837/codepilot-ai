from typing import List, Optional

from app.schemas.chat import ChatMessage, ChatResponse, SourceReference
from app.schemas.search import SearchResult
from app.services.ai_service import AIService, AIServiceError
from app.services.context_builder import ContextBuilder
from app.services.search_service import SearchService


class ChatService:
    """
    Orchestrates the full RAG pipeline:
    Question → Search → Context → LLM → Grounded Answer + Sources
    """

    def __init__(self) -> None:
        self.search_service = SearchService()
        self.context_builder = ContextBuilder()
        self.ai_service = AIService()

    def chat(
        self,
        question: str,
        repository: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        top_k: int = 5,
    ) -> ChatResponse:
        # Step 1: Semantic search
        if repository:
            search_resp = self.search_service.search_repository(question, repository, top_k)
        else:
            search_resp = self.search_service.search_all(question, top_k)

        retrieved: List[SearchResult] = search_resp.results

        # Step 2: Build context block
        context = self.context_builder.build(retrieved)

        # Step 3: Generate grounded LLM answer
        answer = self.ai_service.answer_question(
            question=question,
            context=context,
            history=history or [],
        )

        # Step 4: Deduplicated source citations
        sources = self._extract_sources(retrieved)

        return ChatResponse(answer=answer, sources=sources, query=question)

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
