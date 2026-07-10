"""Heading-based chunker for Markdown files.

Splits content by heading hierarchy (# / ## / ###).  Each section — from
one heading to the next heading of equal or higher level — becomes a chunk.
"""

import re

from app.indexing.base_chunker import (
    BaseChunker,
    ChunkResponse,
    make_chunk,
    split_oversized,
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)


class MarkdownChunker(BaseChunker):
    """Chunk Markdown files by heading structure."""

    def chunk(
        self,
        file_path: str,
        content: str,
        repository: str,
        language: str = "Markdown",
    ) -> list[ChunkResponse]:
        lines = content.splitlines(keepends=True)

        # Find all headings with their line indices and levels
        headings: list[tuple[int, int, str]] = []  # (line_index, level, title)
        for idx, line in enumerate(lines):
            match = _HEADING_RE.match(line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append((idx, level, title))

        # No headings → whole file is one chunk
        if not headings:
            if len(lines) <= self.max_lines:
                return [
                    make_chunk(
                        content,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="file",
                        name=file_path.split("/")[-1],
                        start_line=1,
                        end_line=len(lines),
                    )
                ]
            return split_oversized(
                lines,
                repository=repository,
                file=file_path,
                language=language,
                chunk_type="file",
                name=file_path.split("/")[-1],
                base_start_line=1,
                max_lines=self.max_lines,
            )

        # Build sections: each heading runs until the next heading of same/higher level
        sections: list[tuple[int, int, str]] = []  # (start_idx, end_idx, title)
        for i, (line_idx, level, title) in enumerate(headings):
            # Find the end: next heading at same or higher (lower number) level
            end_idx = len(lines) - 1
            for j in range(i + 1, len(headings)):
                if headings[j][1] <= level:
                    end_idx = headings[j][0] - 1
                    break
            sections.append((line_idx, end_idx, title))

        # Content before the first heading (preamble)
        if headings[0][0] > 0:
            preamble = "".join(lines[: headings[0][0]])
            if preamble.strip():
                sections.insert(0, (0, headings[0][0] - 1, "preamble"))

        # Convert sections to chunks
        chunks: list[ChunkResponse] = []
        total = len(sections)

        for idx, (start_idx, end_idx, title) in enumerate(sections):
            section_lines = lines[start_idx : end_idx + 1]
            section_text = "".join(section_lines)
            line_count = end_idx - start_idx + 1

            if line_count <= self.max_lines:
                chunks.append(
                    make_chunk(
                        section_text,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="markdown_section",
                        name=title,
                        start_line=start_idx + 1,
                        end_line=end_idx + 1,
                        chunk_index=idx + 1,
                        total_chunks=total,
                    )
                )
            else:
                chunks.extend(
                    split_oversized(
                        section_lines,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="markdown_section",
                        name=title,
                        base_start_line=start_idx + 1,
                        max_lines=self.max_lines,
                    )
                )

        return chunks
