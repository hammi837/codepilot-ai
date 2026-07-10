"""AST-based semantic chunker for Python source files.

Handles all Python-specific scenarios:
- Functions → one chunk each (nested functions stay together)
- Classes small enough → one chunk
- Large classes → split by methods
- Large methods/functions → split by line count
- Global variables → grouped into one chunk
- Imports → prepended to the first code chunk
- Small files → one chunk
"""

import ast

from app.indexing.base_chunker import (
    BaseChunker,
    ChunkResponse,
    make_chunk,
    split_oversized,
)


def _get_source_segment(lines: list[str], node: ast.AST) -> tuple[int, int, str]:
    """Extract the source text for an AST node using its line numbers.

    Returns (start_line, end_line, source_text).  Line numbers are 1-indexed
    to match the original file.
    """
    start = node.lineno  # 1-indexed
    end = node.end_lineno or start  # 1-indexed
    segment = "".join(lines[start - 1 : end])
    return start, end, segment


class PythonChunker(BaseChunker):
    """Chunk Python files by their AST structure."""

    def chunk(
        self,
        file_path: str,
        content: str,
        repository: str,
        language: str = "Python",
    ) -> list[ChunkResponse]:
        lines = content.splitlines(keepends=True)

        # Tiny file — return as a single chunk
        if len(lines) <= self.max_lines:
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # Unparseable — return whole file
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

            # Check if the file has any classes or functions at all
            has_structure = any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                for node in ast.iter_child_nodes(tree)
            )
            if not has_structure:
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
        else:
            try:
                tree = ast.parse(content)
            except SyntaxError:
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
        # Classify top-level nodes
        # ------------------------------------------------------------------
        imports_lines: list[str] = []
        globals_nodes: list[ast.AST] = []
        function_nodes: list[ast.AST] = []
        class_nodes: list[ast.AST] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                start, end, _ = _get_source_segment(lines, node)
                imports_lines.extend(lines[start - 1 : end])
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                globals_nodes.append(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_nodes.append(node)
            elif isinstance(node, ast.ClassDef):
                class_nodes.append(node)
            # Other top-level statements (if, for, expressions) are treated as globals
            elif not isinstance(node, (ast.Import, ast.ImportFrom)):
                globals_nodes.append(node)

        imports_text = "".join(imports_lines)
        chunks: list[ChunkResponse] = []

        # ------------------------------------------------------------------
        # Globals chunk
        # ------------------------------------------------------------------
        if globals_nodes:
            first = globals_nodes[0]
            last = globals_nodes[-1]
            start = first.lineno
            end = last.end_lineno or last.lineno
            globals_text = "".join(lines[start - 1 : end])

            chunks.append(
                make_chunk(
                    globals_text,
                    repository=repository,
                    file=file_path,
                    language=language,
                    chunk_type="global",
                    name="globals",
                    start_line=start,
                    end_line=end,
                )
            )

        # ------------------------------------------------------------------
        # Function chunks
        # ------------------------------------------------------------------
        for node in function_nodes:
            start, end, func_text = _get_source_segment(lines, node)
            line_count = end - start + 1

            if line_count <= self.max_lines:
                chunks.append(
                    make_chunk(
                        func_text,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="function",
                        name=node.name,
                        start_line=start,
                        end_line=end,
                    )
                )
            else:
                # Function too large — split by line count
                func_lines = lines[start - 1 : end]
                chunks.extend(
                    split_oversized(
                        func_lines,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="function",
                        name=node.name,
                        base_start_line=start,
                        max_lines=self.max_lines,
                    )
                )

        # ------------------------------------------------------------------
        # Class chunks
        # ------------------------------------------------------------------
        for cls_node in class_nodes:
            chunks.extend(self._chunk_class(cls_node, lines, file_path, repository, language))

        # ------------------------------------------------------------------
        # Prepend imports to the first code chunk
        # ------------------------------------------------------------------
        if imports_text and chunks:
            first = chunks[0]
            merged_content = imports_text + "\n" + first.content
            chunks[0] = make_chunk(
                merged_content,
                repository=repository,
                file=file_path,
                language=language,
                chunk_type=first.metadata.type,
                name=first.metadata.name,
                parent=first.metadata.parent,
                start_line=1,
                end_line=first.metadata.end_line,
                chunk_index=first.metadata.chunk_index,
                total_chunks=first.metadata.total_chunks,
            )
        elif imports_text and not chunks:
            # File only has imports (edge case)
            chunks.append(
                make_chunk(
                    imports_text,
                    repository=repository,
                    file=file_path,
                    language=language,
                    chunk_type="imports",
                    name="imports",
                    start_line=1,
                    end_line=len(imports_lines),
                )
            )

        return chunks

    # ------------------------------------------------------------------
    # Class-level chunking
    # ------------------------------------------------------------------
    def _chunk_class(
        self,
        cls_node: ast.ClassDef,
        lines: list[str],
        file_path: str,
        repository: str,
        language: str,
    ) -> list[ChunkResponse]:
        """Chunk a class definition.

        - If it fits within *max_lines*, return it as a single chunk.
        - Otherwise, split into method-level chunks.
        - Nested classes are extracted as separate chunks.
        """
        start, end, class_text = _get_source_segment(lines, cls_node)
        line_count = end - start + 1

        # Small class — one chunk
        if line_count <= self.max_lines:
            return [
                make_chunk(
                    class_text,
                    repository=repository,
                    file=file_path,
                    language=language,
                    chunk_type="class",
                    name=cls_node.name,
                    start_line=start,
                    end_line=end,
                )
            ]

        # Large class — split by members
        chunks: list[ChunkResponse] = []
        methods: list[ast.AST] = []
        nested_classes: list[ast.ClassDef] = []

        for child in ast.iter_child_nodes(cls_node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(child)
            elif isinstance(child, ast.ClassDef):
                nested_classes.append(child)

        # Group methods into chunks that fit within max_lines
        current_group: list[ast.AST] = []
        current_line_count = 0

        for method in methods:
            m_start = method.lineno
            m_end = method.end_lineno or m_start
            m_lines = m_end - m_start + 1

            if m_lines > self.max_lines:
                # Flush any accumulated group first
                if current_group:
                    chunks.append(
                        self._methods_to_chunk(
                            current_group, lines, file_path, repository, language, cls_node.name,
                            chunk_index=len(chunks) + 1,
                        )
                    )
                    current_group = []
                    current_line_count = 0

                # Split this single oversized method by lines
                method_lines = lines[m_start - 1 : m_end]
                chunks.extend(
                    split_oversized(
                        method_lines,
                        repository=repository,
                        file=file_path,
                        language=language,
                        chunk_type="method",
                        name=method.name,
                        parent=cls_node.name,
                        base_start_line=m_start,
                        max_lines=self.max_lines,
                    )
                )
            elif current_line_count + m_lines > self.max_lines:
                # Flush current group, start a new one
                if current_group:
                    chunks.append(
                        self._methods_to_chunk(
                            current_group, lines, file_path, repository, language, cls_node.name,
                            chunk_index=len(chunks) + 1,
                        )
                    )
                current_group = [method]
                current_line_count = m_lines
            else:
                current_group.append(method)
                current_line_count += m_lines

        # Flush remaining methods
        if current_group:
            chunks.append(
                self._methods_to_chunk(
                    current_group, lines, file_path, repository, language, cls_node.name,
                    chunk_index=len(chunks) + 1,
                )
            )

        # Nested classes — each gets its own chunk(s)
        for nested in nested_classes:
            chunks.extend(self._chunk_class(nested, lines, file_path, repository, language))

        # Fix up total_chunks for the class-level splits
        class_chunks = [c for c in chunks if c.metadata.parent == cls_node.name and c.metadata.type == "class"]
        for idx, c in enumerate(class_chunks):
            c.metadata.chunk_index = idx + 1
            c.metadata.total_chunks = len(class_chunks)

        return chunks

    @staticmethod
    def _methods_to_chunk(
        methods: list[ast.AST],
        lines: list[str],
        file_path: str,
        repository: str,
        language: str,
        class_name: str,
        chunk_index: int,
    ) -> ChunkResponse:
        """Combine a group of method AST nodes into a single chunk."""
        first = methods[0]
        last = methods[-1]
        start = first.lineno
        end = last.end_lineno or last.lineno
        content = "".join(lines[start - 1 : end])

        method_names = ", ".join(getattr(m, "name", "?") for m in methods)

        return make_chunk(
            content,
            repository=repository,
            file=file_path,
            language=language,
            chunk_type="class",
            name=f"{class_name} ({method_names})",
            parent=class_name,
            start_line=start,
            end_line=end,
            chunk_index=chunk_index,
            total_chunks=1,  # will be corrected by the caller
        )
