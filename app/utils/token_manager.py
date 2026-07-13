"""
Token and context management utilities.

Estimates token usage and trims context to fit within model limits.
"""
from typing import List
from app.schemas.search import SearchResult

# Conservative token budget (GPT-4 / Groq context safe limit)
MAX_CONTEXT_TOKENS = 6000
# Rough average: 1 token ≈ 4 characters
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Quick token estimation without a tokenizer dependency."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def prioritize_and_trim(results: List[SearchResult], max_tokens: int = MAX_CONTEXT_TOKENS) -> List[SearchResult]:
    """
    Sort by similarity score (highest first), deduplicate by file+name,
    then greedily include chunks until the token budget is exhausted.
    """
    # Deduplicate by file+name key, keeping highest scored
    seen: dict[str, SearchResult] = {}
    for r in results:
        key = f"{r.file}::{r.name or ''}"
        if key not in seen or r.score > seen[key].score:
            seen[key] = r

    ranked = sorted(seen.values(), key=lambda r: r.score, reverse=True)

    selected: List[SearchResult] = []
    used_tokens = 0

    for chunk in ranked:
        chunk_tokens = estimate_tokens(chunk.content)
        if used_tokens + chunk_tokens > max_tokens:
            break
        selected.append(chunk)
        used_tokens += chunk_tokens

    return selected
