"""Base chunker interface and shared utilities for all language-specific chunkers."""

import hashlib
from abc import ABC, abstractmethod

from app.schemas.chunking import ChunkMetadata, ChunkResponse


# Default limits (in lines)
MAX_CHUNK_LINES = 1500
MIN_CHUNK_LINES = 3


def compute_hash(content: str) -> str:
    """Generate a SHA-256 hash of the content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def make_chunk(
    content: str,
    *,
    repository: str,
    file: str,
    language: str,
    chunk_type: str,
    name: str | None = None,
    parent: str | None = None,
    start_line: int,
    end_line: int,
    chunk_index: int = 1,
    total_chunks: int = 1,
) -> ChunkResponse:
    """Convenience factory to build a ChunkResponse with its metadata."""
    return ChunkResponse(
        content=content,
        metadata=ChunkMetadata(
            repository=repository,
            file=file,
            language=language,
            type=chunk_type,
            name=name,
            parent=parent,
            start_line=start_line,
            end_line=end_line,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            hash=compute_hash(content),
        ),
    )


def split_oversized(
    lines: list[str],
    *,
    repository: str,
    file: str,
    language: str,
    chunk_type: str,
    name: str | None = None,
    parent: str | None = None,
    base_start_line: int,
    max_lines: int = MAX_CHUNK_LINES,
) -> list[ChunkResponse]:
    """Split a block of lines that exceeds *max_lines* into sequential chunks.

    Each resulting chunk carries metadata linking it back to the original
    logical unit (function, class, etc.) via *chunk_index* / *total_chunks*.
    """
    total_chunks = (len(lines) + max_lines - 1) // max_lines  # ceiling division
    chunks: list[ChunkResponse] = []

    for i in range(total_chunks):
        start = i * max_lines
        end = min(start + max_lines, len(lines))
        chunk_lines = lines[start:end]
        content = "".join(chunk_lines)

        chunks.append(
            make_chunk(
                content,
                repository=repository,
                file=file,
                language=language,
                chunk_type=chunk_type,
                name=name,
                parent=parent,
                start_line=base_start_line + start,
                end_line=base_start_line + end - 1,
                chunk_index=i + 1,
                total_chunks=total_chunks,
            )
        )

    return chunks


class BaseChunker(ABC):
    """Abstract base class that every language-specific chunker must implement."""

    def __init__(self, max_lines: int = MAX_CHUNK_LINES) -> None:
        self.max_lines = max_lines

    @abstractmethod
    def chunk(
        self,
        file_path: str,
        content: str,
        repository: str,
        language: str,
    ) -> list[ChunkResponse]:
        """Parse *content* and return a list of semantically meaningful chunks."""
        ...
