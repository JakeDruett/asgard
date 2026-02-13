"""
Heimdall Duplication Detector Service

Detects code duplication using token-based analysis and similarity algorithms.

Duplication Types:
- Type 1 (Exact): Identical code blocks
- Type 2 (Structural): Same structure with different variable names
- Type 3 (Similar): Similar code with modifications
"""

import difflib
import hashlib
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from Asgard.Heimdall.Quality.models.duplication_models import (
    CloneFamily,
    CodeBlock,
    DuplicationConfig,
    DuplicationMatch,
    DuplicationResult,
    DuplicationType,
)
from Asgard.Heimdall.Quality.utilities.file_utils import scan_directory


class DuplicationDetector:
    """
    Detects code duplication using token-based analysis.

    Supports:
    - Exact match detection (Type 1 clones)
    - Structural similarity detection (Type 2 clones)
    - Near-miss detection (Type 3 clones)
    """

    # Normalization patterns for token comparison
    NORMALIZATION_PATTERNS = [
        (r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'IDENT'),  # Variable/function names
        (r'\b\d+\.?\d*\b', 'NUM'),  # Numbers
        (r'"[^"]*"', 'STR'),  # Double-quoted strings
        (r"'[^']*'", 'STR'),  # Single-quoted strings
        (r'#.*$', '', re.MULTILINE),  # Python comments
        (r'//.*$', '', re.MULTILINE),  # C-style comments
    ]

    def __init__(self, config: Optional[DuplicationConfig] = None):
        """
        Initialize the duplication detector.

        Args:
            config: Detection configuration. Uses defaults if not provided.
        """
        self.config = config or DuplicationConfig()

    def analyze(self, scan_path: Optional[Path] = None) -> DuplicationResult:
        """
        Perform duplication analysis on the specified path.

        Args:
            scan_path: Root path to scan. Uses config path if not provided.

        Returns:
            DuplicationResult containing all findings
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Scan path does not exist: {path}")

        start_time = time.time()

        result = DuplicationResult(
            scan_path=str(path),
            min_block_size=self.config.min_block_size,
            similarity_threshold=self.config.similarity_threshold,
        )

        # Collect all code blocks from files
        all_blocks: List[CodeBlock] = []
        files_scanned = 0
        total_lines = 0

        # Build exclude patterns
        exclude_patterns = list(self.config.exclude_patterns)
        if not self.config.include_tests:
            exclude_patterns.extend(["test_", "_test.py", "tests/", "conftest.py"])

        # Scan files
        for file_path in scan_directory(
            path,
            exclude_patterns=exclude_patterns,
            include_extensions=self.config.include_extensions,
        ):
            if files_scanned >= self.config.max_files:
                break

            try:
                blocks, line_count = self._extract_blocks_from_file(file_path, path)
                all_blocks.extend(blocks)
                total_lines += line_count
                files_scanned += 1
            except Exception:
                continue

        result.total_files_scanned = files_scanned
        result.total_blocks_analyzed = len(all_blocks)

        # Find clone families
        if all_blocks:
            clone_families = self._find_clone_families(all_blocks)
            for family in clone_families:
                result.add_clone_family(family)

        # Calculate duplication percentage
        if total_lines > 0:
            result.duplication_percentage = (result.total_duplicated_lines / total_lines) * 100

        result.scan_duration_seconds = time.time() - start_time

        # Sort families by severity
        result.clone_families.sort(
            key=lambda f: (f.block_count, f.total_duplicated_lines),
            reverse=True
        )

        return result

    def _extract_blocks_from_file(
        self, file_path: Path, root_path: Path
    ) -> Tuple[List[CodeBlock], int]:
        """
        Extract code blocks from a single file.

        Args:
            file_path: Path to the file
            root_path: Root path for relative path calculation

        Returns:
            Tuple of (list of code blocks, total lines in file)
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return [], 0

        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines < self.config.min_block_size:
            return [], total_lines

        blocks: List[CodeBlock] = []
        relative_path = str(file_path.relative_to(root_path))

        # Use function/class boundaries for Python files
        if file_path.suffix == ".py":
            blocks = self._extract_python_blocks(
                content, lines, str(file_path), relative_path
            )
        else:
            # Fall back to sliding window for other files
            blocks = self._extract_sliding_window_blocks(
                lines, str(file_path), relative_path
            )

        return blocks, total_lines

    def _extract_python_blocks(
        self, content: str, lines: List[str], file_path: str, relative_path: str
    ) -> List[CodeBlock]:
        """Extract code blocks based on Python function/class boundaries."""
        import ast

        blocks: List[CodeBlock] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to sliding window if parsing fails
            return self._extract_sliding_window_blocks(lines, file_path, relative_path)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno or start_line

                if end_line - start_line + 1 >= self.config.min_block_size:
                    block_lines = lines[start_line - 1:end_line]
                    block_content = "\n".join(block_lines)

                    tokens = self._tokenize(block_content)
                    normalized = self._normalize_tokens(tokens)
                    hash_value = self._hash_tokens(normalized)

                    blocks.append(CodeBlock(
                        file_path=file_path,
                        relative_path=relative_path,
                        start_line=start_line,
                        end_line=end_line,
                        content=block_content,
                        tokens=tokens,
                        normalized_tokens=normalized,
                        hash_value=hash_value,
                        line_count=end_line - start_line + 1,
                    ))

        return blocks

    def _extract_sliding_window_blocks(
        self, lines: List[str], file_path: str, relative_path: str
    ) -> List[CodeBlock]:
        """Extract code blocks using sliding window approach."""
        blocks: List[CodeBlock] = []
        min_size = self.config.min_block_size

        # Use a step to avoid too many overlapping blocks
        step = max(1, min_size // 2)

        for start in range(0, len(lines) - min_size + 1, step):
            end = start + min_size
            block_lines = lines[start:end]
            block_content = "\n".join(block_lines)

            # Skip blocks that are mostly empty or comments
            if not self._is_meaningful_block(block_lines):
                continue

            tokens = self._tokenize(block_content)
            normalized = self._normalize_tokens(tokens)
            hash_value = self._hash_tokens(normalized)

            blocks.append(CodeBlock(
                file_path=file_path,
                relative_path=relative_path,
                start_line=start + 1,
                end_line=end,
                content=block_content,
                tokens=tokens,
                normalized_tokens=normalized,
                hash_value=hash_value,
                line_count=min_size,
            ))

        return blocks

    def _tokenize(self, content: str) -> List[str]:
        """Tokenize code content."""
        # Split by whitespace and common delimiters
        tokens = re.findall(r'\w+|[^\w\s]', content)
        return [t.strip() for t in tokens if t.strip()]

    def _normalize_tokens(self, tokens: List[str]) -> List[str]:
        """Normalize tokens for structural comparison."""
        normalized = []
        token_string = " ".join(tokens)

        # Apply normalization patterns
        for pattern, replacement, *flags in self.NORMALIZATION_PATTERNS:
            flag = flags[0] if flags else 0
            token_string = re.sub(pattern, replacement, token_string, flags=flag)

        # Re-tokenize after normalization
        normalized = [t.strip() for t in token_string.split() if t.strip()]
        return normalized

    def _hash_tokens(self, tokens: List[str]) -> str:
        """Calculate hash of token sequence."""
        token_string = "".join(tokens)
        return hashlib.md5(token_string.encode()).hexdigest()

    def _is_meaningful_block(self, lines: List[str]) -> bool:
        """Check if block contains meaningful code."""
        meaningful = 0
        for line in lines:
            stripped = line.strip()
            # Skip empty lines, comments, and very short lines
            if stripped and not stripped.startswith("#") and len(stripped) > 3:
                meaningful += 1
        return meaningful >= self.config.min_block_size // 2

    def _find_clone_families(self, blocks: List[CodeBlock]) -> List[CloneFamily]:
        """
        Find clone families among code blocks.

        Groups blocks by similarity into clone families.
        """
        families: List[CloneFamily] = []
        used_blocks: Set[int] = set()

        # First pass: Group by exact hash (Type 1)
        hash_groups: Dict[str, List[int]] = defaultdict(list)
        for i, block in enumerate(blocks):
            hash_groups[block.hash_value].append(i)

        for hash_value, indices in hash_groups.items():
            if len(indices) >= 2:
                family = CloneFamily(
                    match_type=DuplicationType.EXACT,
                    average_similarity=1.0,
                    severity=CloneFamily.calculate_severity(len(indices)),
                )
                for idx in indices:
                    family.add_block(blocks[idx])
                    used_blocks.add(idx)
                families.append(family)

        # Second pass: Find structural similarities (Type 2/3)
        remaining = [i for i in range(len(blocks)) if i not in used_blocks]

        for i in range(len(remaining)):
            if remaining[i] in used_blocks:
                continue

            idx_i = remaining[i]
            similar_indices = [idx_i]

            for j in range(i + 1, len(remaining)):
                if remaining[j] in used_blocks:
                    continue

                idx_j = remaining[j]
                similarity = self._calculate_similarity(blocks[idx_i], blocks[idx_j])

                if similarity >= self.config.similarity_threshold:
                    similar_indices.append(idx_j)
                    used_blocks.add(idx_j)

            if len(similar_indices) >= 2:
                used_blocks.add(idx_i)
                avg_similarity = sum(
                    self._calculate_similarity(blocks[idx_i], blocks[k])
                    for k in similar_indices[1:]
                ) / (len(similar_indices) - 1) if len(similar_indices) > 1 else 1.0

                match_type = (
                    DuplicationType.STRUCTURAL if avg_similarity > 0.9
                    else DuplicationType.SIMILAR
                )

                family = CloneFamily(
                    match_type=match_type,
                    average_similarity=avg_similarity,
                    severity=CloneFamily.calculate_severity(len(similar_indices)),
                )
                for idx in similar_indices:
                    family.add_block(blocks[idx])
                families.append(family)

        return families

    def _calculate_similarity(self, block1: CodeBlock, block2: CodeBlock) -> float:
        """Calculate similarity between two code blocks."""
        matcher = difflib.SequenceMatcher(
            None, block1.normalized_tokens, block2.normalized_tokens
        )
        return matcher.ratio()

    def analyze_single_file(self, file_path: Path) -> DuplicationResult:
        """
        Analyze a single file for internal duplication.

        Args:
            file_path: Path to the file

        Returns:
            DuplicationResult with findings

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        start_time = time.time()

        result = DuplicationResult(
            scan_path=str(path.parent),
            min_block_size=self.config.min_block_size,
            similarity_threshold=self.config.similarity_threshold,
        )

        try:
            blocks, total_lines = self._extract_blocks_from_file(path, path.parent)
            result.total_files_scanned = 1
            result.total_blocks_analyzed = len(blocks)

            if blocks:
                clone_families = self._find_clone_families(blocks)
                for family in clone_families:
                    result.add_clone_family(family)

            if total_lines > 0:
                result.duplication_percentage = (
                    result.total_duplicated_lines / total_lines
                ) * 100

        except Exception:
            pass

        result.scan_duration_seconds = time.time() - start_time
        return result
