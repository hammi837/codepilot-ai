"""Indexing and content processing modules.

Provides a factory function to select the correct chunker for a given language.
"""

from app.indexing.base_chunker import BaseChunker
from app.indexing.python_chunker import PythonChunker
from app.indexing.markdown_chunker import MarkdownChunker
from app.indexing.generic_chunker import GenericChunker


def get_chunker(language: str) -> BaseChunker:
    """Return the appropriate chunker based on the detected file language."""
    lang = language.lower()

    if lang == "python":
        return PythonChunker()
    elif lang == "markdown":
        return MarkdownChunker()
    else:
        return GenericChunker()
