"""Generic chunker for JSON, YAML, HTML, and unrecognized file types.

- JSON:  Small → one chunk.  Large → split by top-level keys.
- YAML:  Split by top-level keys/sections.
- HTML:  Split by semantic tags (<header>, <section>, <footer>, etc.).
- Other: Whole file as one chunk, or split by size if too large.
"""

import json
import re

from app.indexing.base_chunker import (
    BaseChunker,
    ChunkResponse,
    make_chunk,
    split_oversized,
)


class GenericChunker(BaseChunker):
    """Fallback chunker that handles JSON, YAML, HTML, and unknown files."""

    def chunk(
        self,
        file_path: str,
        content: str,
        repository: str,
        language: str = "Unknown",
    ) -> list[ChunkResponse]:
        lang = language.lower()

        if lang == "json":
            return self._chunk_json(file_path, content, repository, language)
        elif lang == "yaml":
            return self._chunk_yaml(file_path, content, repository, language)
        elif lang == "html":
            return self._chunk_html(file_path, content, repository, language)
        else:
            return self._chunk_plaintext(file_path, content, repository, language)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    def _chunk_json(
        self, file_path: str, content: str, repository: str, language: str,
    ) -> list[ChunkResponse]:
        lines = content.splitlines(keepends=True)

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

        # Try to split by top-level keys
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
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

        if isinstance(data, dict):
            chunks: list[ChunkResponse] = []
            total = len(data)
            for idx, (key, value) in enumerate(data.items()):
                key_content = json.dumps({key: value}, indent=2)
                chunks.append(
                    make_chunk(
                        key_content,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="json_key",
                        name=key,
                        start_line=1,
                        end_line=len(lines),
                        chunk_index=idx + 1,
                        total_chunks=total,
                    )
                )
            return chunks

        # Not a dict at top level — fall back to size splitting
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

    # ------------------------------------------------------------------
    # YAML
    # ------------------------------------------------------------------
    def _chunk_yaml(
        self, file_path: str, content: str, repository: str, language: str,
    ) -> list[ChunkResponse]:
        lines = content.splitlines(keepends=True)

        if len(lines) <= self.max_lines:
            # Try to identify top-level keys for better chunking
            sections = self._split_yaml_sections(lines)
            if len(sections) <= 1:
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

            chunks: list[ChunkResponse] = []
            total = len(sections)
            for idx, (key, start_idx, end_idx) in enumerate(sections):
                section_text = "".join(lines[start_idx:end_idx])
                chunks.append(
                    make_chunk(
                        section_text,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="yaml_section",
                        name=key,
                        start_line=start_idx + 1,
                        end_line=end_idx,
                        chunk_index=idx + 1,
                        total_chunks=total,
                    )
                )
            return chunks

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

    @staticmethod
    def _split_yaml_sections(lines: list[str]) -> list[tuple[str, int, int]]:
        """Identify top-level YAML keys and their line ranges.

        A top-level key is a non-indented, non-comment line ending with ``:``.
        Returns list of (key_name, start_line_index, end_line_index).
        """
        top_level_re = re.compile(r"^(\S[^:]*?):\s*")
        sections: list[tuple[str, int, int]] = []
        current_key: str | None = None
        current_start = 0

        for idx, line in enumerate(lines):
            match = top_level_re.match(line)
            if match and not line.lstrip().startswith("#"):
                if current_key is not None:
                    sections.append((current_key, current_start, idx))
                current_key = match.group(1).strip()
                current_start = idx

        if current_key is not None:
            sections.append((current_key, current_start, len(lines)))

        return sections

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------
    def _chunk_html(
        self, file_path: str, content: str, repository: str, language: str,
    ) -> list[ChunkResponse]:
        lines = content.splitlines(keepends=True)

        # Try to split by semantic tags
        semantic_tags = ["header", "section", "footer", "main", "article", "nav", "aside"]
        pattern = re.compile(
            r"<(" + "|".join(semantic_tags) + r")[\s>]",
            re.IGNORECASE,
        )

        # Find boundaries
        boundaries: list[tuple[int, str]] = []
        for idx, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                boundaries.append((idx, match.group(1).lower()))

        if not boundaries:
            # No semantic tags — treat as plain text
            return self._chunk_plaintext(file_path, content, repository, language)

        chunks: list[ChunkResponse] = []

        # Content before the first semantic tag
        if boundaries[0][0] > 0:
            preamble = "".join(lines[: boundaries[0][0]])
            if preamble.strip():
                chunks.append(
                    make_chunk(
                        preamble,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="html_section",
                        name="preamble",
                        start_line=1,
                        end_line=boundaries[0][0],
                    )
                )

        for i, (line_idx, tag) in enumerate(boundaries):
            end_idx = boundaries[i + 1][0] - 1 if i + 1 < len(boundaries) else len(lines) - 1
            section_text = "".join(lines[line_idx : end_idx + 1])

            if (end_idx - line_idx + 1) <= self.max_lines:
                chunks.append(
                    make_chunk(
                        section_text,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="html_section",
                        name=tag,
                        start_line=line_idx + 1,
                        end_line=end_idx + 1,
                        chunk_index=i + 1,
                        total_chunks=len(boundaries),
                    )
                )
            else:
                chunks.extend(
                    split_oversized(
                        lines[line_idx : end_idx + 1],
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="html_section",
                        name=tag,
                        base_start_line=line_idx + 1,
                        max_lines=self.max_lines,
                    )
                )

        return chunks if chunks else self._chunk_plaintext(file_path, content, repository, language)

    # ------------------------------------------------------------------
    # Plain text / fallback
    # ------------------------------------------------------------------
    def _chunk_plaintext(
        self, file_path: str, content: str, repository: str, language: str,
    ) -> list[ChunkResponse]:
        lines = content.splitlines(keepends=True)

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
