from typing import List
from app.schemas.search import SearchResult


MAX_CONTEXT_CHARS = 12_000  # Roughly 3,000 tokens — safe for most LLMs


class ContextBuilder:
    """
    Assembles retrieved code chunks into a clean, deduplicated context
    block suitable for injection into an LLM prompt.
    """

    def build(self, results: List[SearchResult]) -> str:
        """
        Takes search results, deduplicates by file+name, trims to a
        character budget, and returns a formatted context string.
        """
        if not results:
            return "No relevant code context was found in the repository."

        # Deduplicate: if two chunks come from the same file+function, keep the highest score
        seen: dict[str, SearchResult] = {}
        for result in results:
            key = f"{result.file}::{result.name or ''}"
            if key not in seen or result.score > seen[key].score:
                seen[key] = result

        # Sort by score descending
        deduped = sorted(seen.values(), key=lambda r: r.score, reverse=True)

        sections: List[str] = []
        total_chars = 0

        for result in deduped:
            section = self._format_chunk(result)
            if total_chars + len(section) > MAX_CONTEXT_CHARS:
                break
            sections.append(section)
            total_chars += len(section)

        return "\n\n".join(sections)

    def _format_chunk(self, result: SearchResult) -> str:
        """Format a single code chunk into a readable context section."""
        header_parts = [f"File: {result.file}"]
        if result.name:
            header_parts.append(f"Symbol: {result.name}")
        if result.type:
            header_parts.append(f"Type: {result.type}")

        header = " | ".join(header_parts)
        return f"--- {header} ---\n```\n{result.content}\n```"
