"""Orchestrates the semantic chunking pipeline.

Reads indexed files from a cloned repository, detects language,
selects the appropriate chunker, and returns structured chunks.
"""

import os
from pathlib import Path
from typing import List

from app.indexing import get_chunker
from app.schemas.chunking import ChunkResponse


# Reuse the language detection map from RepositoryService
_EXT_TO_LANGUAGE = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript React", ".jsx": "JavaScript React",
    ".html": "HTML", ".css": "CSS", ".md": "Markdown",
    ".json": "JSON", ".go": "Go", ".java": "Java",
    ".cpp": "C++", ".c": "C", ".rs": "Rust", ".sh": "Shell",
    ".yml": "YAML", ".yaml": "YAML", ".txt": "Text",
    ".ini": "Unknown", ".toml": "Unknown", ".cfg": "Unknown",
}

IGNORED_DIRS = {".git", "venv", "node_modules", "__pycache__", "dist", "build"}

# Binary/non-text extensions to skip entirely
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".class",
    ".db", ".sqlite", ".sqlite3",
    ".lock",
}


class ChunkingService:
    """Read files from a cloned repository and produce semantic chunks."""

    def __init__(self) -> None:
        self.workspace_dir = Path("workspace")

    def chunk_repository(self, repository_name: str) -> List[ChunkResponse]:
        """Chunk every eligible file in the repository and return all chunks."""
        repo_name = repository_name.split("/")[-1]
        repo_path = self.workspace_dir / repo_name

        if not repo_path.exists():
            raise ValueError(f"Repository '{repo_name}' not found in workspace.")

        all_chunks: List[ChunkResponse] = []

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file_name in files:
                file_path = Path(root) / file_name
                ext = file_path.suffix.lower()

                # Skip binary files
                if ext in BINARY_EXTENSIONS:
                    continue

                relative_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                language = _EXT_TO_LANGUAGE.get(ext, "Unknown")

                # Try reading the file
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Skip empty files
                if not content.strip():
                    continue

                chunker = get_chunker(language)
                file_chunks = chunker.chunk(
                    file_path=relative_path,
                    content=content,
                    repository=repo_name,
                    language=language,
                )
                all_chunks.extend(file_chunks)

        return all_chunks
