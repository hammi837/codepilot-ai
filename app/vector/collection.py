from typing import Any
from chromadb.api.models.Collection import Collection

from app.vector.client import get_chroma_client

def get_or_create_collection(name: str) -> Collection:
    """Retrieve or create a ChromaDB collection by name."""
    client = get_chroma_client()
    # We use cosine similarity by default for most embedding models
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )
    
def get_collection(name: str) -> Collection:
    """Retrieve an existing collection by name."""
    client = get_chroma_client()
    return client.get_collection(name=name)

def delete_collection(name: str) -> None:
    """Delete a collection by name."""
    client = get_chroma_client()
    client.delete_collection(name=name)
