from typing import List, Dict, Any, Optional
import uuid

from app.vector.collection import get_or_create_collection, get_collection, delete_collection
from app.schemas.chunking import ChunkResponse
from app.schemas.embedding import EmbeddingResponse

class VectorService:
    """Manages interactions with the vector database for storing and querying embeddings."""
    
    def __init__(self, collection_name: str = "codepilot_chunks") -> None:
        self.collection_name = collection_name
        self.collection = get_or_create_collection(name=self.collection_name)
        
    def add_chunks(self, repository: str, chunks: List[ChunkResponse], embeddings: List[EmbeddingResponse]) -> int:
        """Stores a list of chunks and their corresponding embeddings into ChromaDB."""
        if not chunks or not embeddings:
            return 0
            
        if len(chunks) != len(embeddings):
            raise ValueError("Mismatched number of chunks and embeddings.")
            
        ids = []
        vectors = []
        documents = []
        metadatas = []
        
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # Use UUIDs to guarantee uniqueness across all chunks
            chunk_id = str(uuid.uuid4())
            
            ids.append(chunk_id)
            vectors.append(emb.embedding)
            documents.append(chunk.content)
            
            # Prepare metadata mapping
            meta = {
                "repository": repository,
                "file": chunk.metadata.file,
                "language": chunk.metadata.language,
                "type": chunk.metadata.type,
                "chunk_index": chunk.metadata.chunk_index,
                "total_chunks": chunk.metadata.total_chunks,
                "hash": chunk.metadata.hash,
                "start_line": chunk.metadata.start_line,
                "end_line": chunk.metadata.end_line
            }
            if chunk.metadata.name:
                meta["name"] = chunk.metadata.name
            if chunk.metadata.parent:
                meta["parent"] = chunk.metadata.parent
                
            metadatas.append(meta)
            
        # Add to ChromaDB in batches if needed, but ChromaDB supports reasonably large batches natively
        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(ids)

    def search(self, query_embedding: List[float], repository: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """Perform semantic search on the vector database."""
        where_clause = {"repository": repository} if repository else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        return results

    def delete_repository(self, repository: str) -> None:
        """Delete all chunks belonging to a specific repository."""
        self.collection.delete(
            where={"repository": repository}
        )
        
    def list_collections(self) -> List[str]:
        """List available collection names."""
        from app.vector.client import get_chroma_client
        client = get_chroma_client()
        # Newer chromadb APIs return objects, we get their names
        return [c.name for c in client.list_collections()]
