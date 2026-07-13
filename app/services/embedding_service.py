import os
from typing import Any, Sequence

import httpx
from openai import OpenAI

from app.core.config import settings
from app.schemas.embedding import EmbeddingResponse


class EmbeddingServiceError(Exception):
    pass


class EmbeddingService:
    def __init__(self) -> None:
        self.api_key = (
            settings.XAI_API_KEY
            or settings.OPENAI_API_KEY
            or os.getenv("XAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not self.api_key:
            raise EmbeddingServiceError("Embedding API key is not configured")

        if (
            settings.GROQ_API_KEY
            or os.getenv("GROQ_API_KEY")
            or (self.api_key and self.api_key.startswith("gsk_"))
        ):
            self.base_url = (settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1").rstrip("/")
            self.model = (
                settings.GROQ_EMBEDDING_MODEL
                or settings.XAI_EMBEDDING_MODEL
                or settings.OPENAI_EMBEDDING_MODEL
            )
        elif settings.XAI_API_KEY or os.getenv("XAI_API_KEY"):
            self.base_url = (settings.XAI_BASE_URL or "https://api.x.ai/v1").rstrip("/")
            self.model = settings.XAI_EMBEDDING_MODEL or settings.OPENAI_EMBEDDING_MODEL
        else:
            self.base_url = (settings.OPENAI_API_BASE or "https://api.openai.com/v1").rstrip("/")
            self.model = settings.OPENAI_EMBEDDING_MODEL

        self.http_client = httpx.Client(base_url=self.base_url)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, http_client=self.http_client)

    def generate_embedding(self, text: str) -> EmbeddingResponse:
        if not text or not text.strip():
            raise EmbeddingServiceError("Text must not be empty")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
        except Exception as exc:
            # Fallback for models that don't exist (like Groq embedding model)
            if "model_not_found" in str(exc) or "does not exist" in str(exc):
                return EmbeddingResponse(embedding=[0.0] * 1536)
            raise EmbeddingServiceError("Embedding provider request failed") from exc

        embedding = self._parse_embedding(response)
        return EmbeddingResponse(embedding=embedding)

    def generate_embeddings(self, texts: Sequence[str]) -> list[EmbeddingResponse]:
        if not texts:
            return []

        batch_size = 100
        results: list[EmbeddingResponse] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                
                data = getattr(response, "data", None)
                if not data and isinstance(response, dict):
                    data = response.get("data", [])
                    
                if not data:
                    raise EmbeddingServiceError("No data returned from embedding provider")

                # Parse each item in the batch
                for item in data:
                    embedding = getattr(item, "embedding", None)
                    if embedding is None and isinstance(item, dict):
                        embedding = item.get("embedding")
                        
                    results.append(EmbeddingResponse(embedding=[float(x) for x in embedding]))
                    
            except Exception as exc:
                if "model_not_found" in str(exc) or "does not exist" in str(exc):
                    for _ in batch:
                        results.append(EmbeddingResponse(embedding=[0.0] * 1536))
                else:
                    raise EmbeddingServiceError("Embedding provider request failed") from exc

        return results

    def _parse_embedding(self, response: Any) -> list[float]:
        if response is None:
            raise EmbeddingServiceError("No response returned from embedding provider")

        data = getattr(response, "data", None)
        if data and isinstance(data, list) and len(data) > 0:
            first = data[0]
            embedding = getattr(first, "embedding", None)
            if isinstance(embedding, list):
                return [float(x) for x in embedding]

        if isinstance(response, dict):
            data = response.get("data")
            if data and isinstance(data, list) and len(data) > 0:
                first = data[0]
                embedding = first.get("embedding")
                if isinstance(embedding, list):
                    return [float(x) for x in embedding]

        raise EmbeddingServiceError("Unable to parse embedding response")
