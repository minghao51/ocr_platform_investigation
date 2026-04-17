"""
Chunking service for splitting large documents into manageable chunks.

This service provides Markdown-aware text splitting for chunking long documents,
with support for:
- Dynamic token limits based on model context window
- Map-reduce synthesis for JSON extraction results
- Progress tracking through WebSocket
- Integration with existing extraction pipeline
"""

from typing import List, Dict, Any, Optional
import tiktoken


class MarkdownSplitter:
    """
    Markdown-aware text splitter for chunking long documents.

    Splits text while preserving:
    - Markdown headers (##, ###, etc.)
    - Code blocks
    - List items
    - Table structures

    Provides overlap between chunks to maintain context.
    """

    def __init__(
        self,
        encoding_name: str = "cl100k_base",  # GPT-4/GPT-3.5 encoding
        default_max_tokens: int = 2000,
        overlap_tokens: int = 200,
    ):
        """
        Initialize the Markdown splitter.

        Args:
            encoding_name: Tiktoken encoding name for token counting
            default_max_tokens: Default maximum tokens per chunk
            overlap_tokens: Number of tokens to overlap between chunks
        """
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.default_max_tokens = default_max_tokens
        self.overlap_tokens = overlap_tokens

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in text using the configured encoding."""
        return len(self.encoding.encode(text))

    def split(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        preserve_structure: bool = True,
    ) -> List[str]:
        """
        Split text into chunks while preserving Markdown structure.

        Args:
            text: Input text to split
            max_tokens: Maximum tokens per chunk (uses default if not specified)
            preserve_structure: Whether to preserve Markdown structure (headers, code blocks, etc.)

        Returns:
            List of text chunks
        """
        if max_tokens is None:
            max_tokens = self.default_max_tokens

        # If text is short enough, return as single chunk
        if self.count_tokens(text) <= max_tokens:
            return [text]

        if preserve_structure:
            return self._split_markdown_aware(text, max_tokens)
        else:
            return self._split_simple(text, max_tokens)

    def _split_markdown_aware(self, text: str, max_tokens: int) -> List[str]:
        """
        Split text while preserving Markdown structure.

        Strategy:
        1. Split on major headers (#, ##)
        2. If sections are too long, split on sub-headers (###, ####)
        3. If still too long, split on paragraphs
        4. Maintain overlap between chunks
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0

        # Split into sections based on headers
        lines = text.split("\n")

        for i, line in enumerate(lines):
            # Check if this line is a header
            is_header = line.strip().startswith("#")

            if is_header and current_chunk:
                # Check if adding this header would exceed token limit
                line_tokens = self.count_tokens(line + "\n")
                potential_tokens = current_tokens + line_tokens

                if potential_tokens > max_tokens:
                    # Save current chunk and start new one
                    chunks.append(current_chunk.strip())
                    # Add overlap from previous chunk
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + "\n\n" + line + "\n"
                    current_tokens = self.count_tokens(current_chunk)
                else:
                    # Add to current chunk
                    current_chunk += "\n" + line
                    current_tokens += line_tokens
            elif current_chunk:
                # Add line to current chunk
                line_tokens = self.count_tokens(line + "\n")
                if current_tokens + line_tokens > max_tokens:
                    # Save current chunk and start new one with overlap
                    chunks.append(current_chunk.strip())
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + "\n" + line
                    current_tokens = self.count_tokens(current_chunk)
                else:
                    current_chunk += "\n" + line
                    current_tokens += line_tokens
            else:
                # First line
                current_chunk = line
                current_tokens = self.count_tokens(line)

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_simple(self, text: str, max_tokens: int) -> List[str]:
        """
        Simple token-based splitting without structure preservation.

        Splits text into chunks of approximately max_tokens, with overlap.
        """
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0

        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end - self.overlap_tokens if end < len(tokens) else end

        return chunks

    def _get_overlap(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk.

        Returns the last few paragraphs or lines to maintain context.
        """
        # Split into paragraphs
        paragraphs = text.split("\n\n")

        # Take last 1-2 paragraphs for overlap
        if len(paragraphs) <= 2:
            overlap = "\n\n".join(paragraphs[-1:])
        else:
            overlap = "\n\n".join(paragraphs[-2:])

        # Ensure overlap doesn't exceed token limit
        overlap_tokens = self.count_tokens(overlap)
        if overlap_tokens > self.overlap_tokens * 1.5:
            # Truncate overlap if too long
            lines = overlap.split("\n")
            overlap_lines: list[str] = []
            for line in reversed(lines):
                overlap_lines.insert(0, line)
                if self.count_tokens("\n".join(overlap_lines)) > self.overlap_tokens:
                    break
            overlap = "\n".join(overlap_lines)

        return overlap

    def merge_chunks(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge extraction results from multiple chunks using map-reduce strategy.

        Args:
            results: List of extraction results from chunks

        Returns:
            Merged result with deduplicated fields
        """
        if not results:
            return {}

        if len(results) == 1:
            return results[0]

        # Start with first result as base
        merged = results[0].copy()

        # Merge subsequent results
        for result in results[1:]:
            for key, value in result.items():
                if key not in merged:
                    # Field not in merged, add it
                    merged[key] = value
                elif isinstance(merged[key], list):
                    # Field is a list, extend it
                    if isinstance(value, list):
                        merged[key].extend(value)
                    else:
                        merged[key].append(value)
                elif isinstance(merged[key], dict):
                    # Field is a dict, merge it
                    if isinstance(value, dict):
                        merged[key] = {**merged[key], **value}
                    else:
                        # Keep existing value
                        pass
                elif merged[key] != value:
                    # Values differ, keep both as list
                    if not isinstance(merged[key], list):
                        merged[key] = [merged[key]]
                    if isinstance(value, list):
                        merged[key].extend(value)
                    else:
                        merged[key].append(value)

        # Deduplicate lists
        for key, value in merged.items():
            if isinstance(value, list):
                # Remove duplicates while preserving order
                seen = set()
                unique_list = []
                for item in value:
                    if item not in seen:
                        seen.add(item)
                        unique_list.append(item)
                merged[key] = unique_list

        return merged

    def split_with_progress(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        websocket_callback=None,
    ) -> List[str]:
        """
        Split text with progress tracking via WebSocket.

        Args:
            text: Input text to split
            max_tokens: Maximum tokens per chunk
            websocket_callback: Optional callback for progress updates

        Returns:
            List of text chunks
        """
        if max_tokens is None:
            max_tokens = self.default_max_tokens

        total_tokens = self.count_tokens(text)
        estimated_chunks = max(1, (total_tokens // max_tokens) + 1)

        chunks = []
        current_chunk = ""
        current_tokens = 0

        lines = text.split("\n")

        for i, line in enumerate(lines):
            line_tokens = self.count_tokens(line + "\n")

            if current_tokens + line_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunks.append(current_chunk.strip())

                # Send progress update
                if websocket_callback:
                    progress = len(chunks) / estimated_chunks
                    websocket_callback(
                        {
                            "type": "chunking_progress",
                            "progress": min(progress, 1.0),
                            "chunks_completed": len(chunks),
                            "estimated_total": estimated_chunks,
                        }
                    )

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text + "\n" + line
                current_tokens = self.count_tokens(current_chunk)
            else:
                if current_chunk:
                    current_chunk += "\n" + line
                else:
                    current_chunk = line
                current_tokens += line_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Send final progress update
        if websocket_callback:
            websocket_callback(
                {
                    "type": "chunking_complete",
                    "progress": 1.0,
                    "total_chunks": len(chunks),
                }
            )

        return chunks
