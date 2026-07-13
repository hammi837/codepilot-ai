from typing import List, Optional, Any
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.schemas.search import SearchResult, SearchResponse

class SearchService:
    """Service to handle semantic search over indexed repositories."""
    
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        
    def search_repository(self, query: str, repository: str, top_k: int = 5) -> SearchResponse:
        """Search within a specific repository."""
        return self._perform_search(query, repository, top_k)
        
    def search_all(self, query: str, top_k: int = 5) -> SearchResponse:
        """Search across all indexed repositories."""
        return self._perform_search(query, None, top_k)
        
    def _perform_search(self, query: str, repository: Optional[str], top_k: int) -> SearchResponse:
        # 1. Generate Embedding for the query
        emb_resp = self.embedding_service.generate_embedding(query)
        query_vector = emb_resp.embedding
        
        # 2. Search ChromaDB using the VectorService
        raw_results = self.vector_service.search(
            query_embedding=query_vector,
            repository=repository,
            top_k=top_k
        )
        
        # 3. Format into a response
        return self.format_results(query, raw_results)
        
    def format_results(self, query: str, raw_results: dict[str, Any]) -> SearchResponse:
        """Parse ChromaDB output into standard SearchResult schemas."""
        search_results = []
        
        # ChromaDB query returns lists of lists for documents, metadatas, distances
        if not raw_results or not raw_results.get("ids") or len(raw_results["ids"]) == 0 or len(raw_results["ids"][0]) == 0:
            return SearchResponse(query=query, results=[])
            
        docs = raw_results.get("documents", [[]])[0]
        metas = raw_results.get("metadatas", [[]])[0]
        dists = raw_results.get("distances", [[]])[0]
        
        for doc, meta, dist in zip(docs, metas, dists):
            # Convert cosine distance (0 is perfect, 1 is orthogonal) to a similarity score (1 is perfect)
            score = 1.0 - dist if dist is not None else 0.0
            
            result = SearchResult(
                repository=meta.get("repository", ""),
                file=meta.get("file", ""),
                type=meta.get("type", "unknown"),
                name=meta.get("name"),
                score=round(score, 4),
                content=doc
            )
            search_results.append(result)
            
        # Ensure they are sorted from highest score to lowest
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        return SearchResponse(query=query, results=search_results)
