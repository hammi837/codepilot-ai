from fastapi import APIRouter, HTTPException, status

from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.vector_service import VectorService

router = APIRouter(prefix="/vector", tags=["vector"])

@router.post("/repositories/store/{repository:path}", status_code=status.HTTP_200_OK)
def store_repository(repository: str) -> dict:
    """Store repository chunks and embeddings into ChromaDB."""
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()
    vector_service = VectorService()
    
    # 1. Chunk the repository
    try:
        chunks = chunking_service.chunk_repository(repository)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        
    if not chunks:
        return {
            "repository": repository.split("/")[-1],
            "stored_chunks": 0
        }
        
    texts = [chunk.content for chunk in chunks]
    
    # 2. Get Embeddings
    try:
        embeddings = embedding_service.generate_embeddings(texts)
    except EmbeddingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
        
    # 3. Store in Vector Database
    repo_name = repository.split("/")[-1]
    
    try:
        stored_count = vector_service.add_chunks(repository=repo_name, chunks=chunks, embeddings=embeddings)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to store chunks: {str(exc)}")
        
    return {
        "repository": repo_name,
        "stored_chunks": stored_count
    }

@router.get("/collections", status_code=status.HTTP_200_OK)
def list_collections() -> dict:
    """List all ChromaDB collections."""
    vector_service = VectorService()
    return {
        "collections": vector_service.list_collections()
    }

@router.delete("/{repository:path}", status_code=status.HTTP_200_OK)
def delete_repository(repository: str) -> dict:
    """Delete a repository from ChromaDB."""
    vector_service = VectorService()
    repo_name = repository.split("/")[-1]
    
    try:
        vector_service.delete_repository(repository=repo_name)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete repository: {str(exc)}")
        
    return {
        "repository": repo_name,
        "status": "deleted"
    }
