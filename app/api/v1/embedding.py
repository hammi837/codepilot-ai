from fastapi import APIRouter, HTTPException, status
import uuid

from app.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.chunking_service import ChunkingService

router = APIRouter(prefix="/repositories", tags=["embeddings"])

# In-memory storage for embeddings (temporary until Hour 11)
_embeddings_store = {}


@router.post("/embed/{repository:path}", status_code=status.HTTP_200_OK)
def embed_repository(repository: str) -> dict:
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()

    try:
        chunks = chunking_service.chunk_repository(repository)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not chunks:
        return {
            "repository": repository.split("/")[-1],
            "chunks": 0,
            "embedded": 0
        }

    texts = [chunk.content for chunk in chunks]

    try:
        embeddings = embedding_service.generate_embeddings(texts)
    except EmbeddingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    for chunk, emb_resp in zip(chunks, embeddings):
        # Generate a simple chunk_id for this session if it doesn't exist
        # We can use the hash and index to make it somewhat deterministic
        chunk_id = f"chunk_{chunk.metadata.hash}_{chunk.metadata.chunk_index}"
        _embeddings_store[chunk_id] = {
            "repository": chunk.metadata.repository,
            "file": chunk.metadata.file,
            "chunk_id": chunk_id,
            "embedding": emb_resp.embedding
        }

    return {
        "repository": repository.split("/")[-1],
        "chunks": len(chunks),
        "embedded": len(embeddings)
    }


@router.get("/embedding/{chunk_id}", status_code=status.HTTP_200_OK)
def get_embedding(chunk_id: str) -> dict:
    if chunk_id not in _embeddings_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

    data = _embeddings_store[chunk_id]
    return {
        "chunk_id": data["chunk_id"],
        "dimensions": len(data["embedding"])
    }
