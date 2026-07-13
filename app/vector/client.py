import os
from chromadb import PersistentClient
from chromadb.config import Settings

from app.core.config import settings

def get_chroma_client() -> PersistentClient:
    """Returns a persistent ChromaDB client."""
    # Define storage path for ChromaDB
    storage_path = os.path.join("storage", "chromadb")
    os.makedirs(storage_path, exist_ok=True)
    
    return PersistentClient(
        path=storage_path,
        settings=Settings(anonymized_telemetry=False)
    )
