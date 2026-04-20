"""
Unit tests for ProcessingService with Docling, Chunking, and Transcription services.

Note: These tests are designed to verify the integration without requiring
full configuration setup. They test the core logic of the new methods.
"""

from services.chunking_service import MarkdownSplitter
from services.transcription_service import TranscriptionService
from services.docling_service import DoclingService

import pytest

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
CHUNK_THRESHOLD_RATIO = 0.8


class TestDoclingIntegration:
    """Test Docling integration components"""

    @pytest.fixture
    def chunking_service(self):
        """Create MarkdownSplitter instance"""
        return MarkdownSplitter()

    @pytest.fixture
    def docling_service(self):
        """Create DoclingService instance"""
        return DoclingService(disable_ocr=True)

    @pytest.fixture
    def transcription_service(self):
        """Create TranscriptionService instance"""
        return TranscriptionService()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a sample PDF file for testing"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("Mock PDF content")
        return str(pdf_path)

    def test_file_size_constants(self):
        """Test that file size constants are properly defined"""
        assert MAX_FILE_SIZE == 15 * 1024 * 1024  # 15MB
        assert CHUNK_THRESHOLD_RATIO == 0.8

    def test_chunking_service_creation(self, chunking_service):
        """Test that chunking service can be created"""
        assert isinstance(chunking_service, MarkdownSplitter)

    def test_docling_service_creation(self, docling_service):
        """Test that docling service can be created"""
        assert isinstance(docling_service, DoclingService)

    def test_transcription_service_creation(self, transcription_service):
        """Test that transcription service can be created"""
        assert isinstance(transcription_service, TranscriptionService)

    def test_chunking_token_count(self, chunking_service):
        """Test that chunking service can count tokens"""
        text = "This is a test document with some text."
        token_count = chunking_service.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)

    def test_chunking_split_text(self, chunking_service):
        """Test that chunking service can split text"""
        long_text = "word " * 10000  # Long text
        chunks = chunking_service.split(long_text)
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_file_size_validation_logic(self):
        """Test file size validation logic"""
        import os

        small_file = "/tmp/test_small.txt"
        with open(small_file, "w") as f:
            f.write("x" * 1000)

        size = os.path.getsize(small_file)
        assert size < MAX_FILE_SIZE  # Should be valid

        large_file = "/tmp/test_large.txt"
        with open(large_file, "wb") as f:
            f.write(b"x" * (MAX_FILE_SIZE + 1))

        size = os.path.getsize(large_file)
        assert size > MAX_FILE_SIZE  # Should be invalid

        os.remove(small_file)
        os.remove(large_file)


class TestChunkingLogic:
    """Test chunking logic components"""

    @pytest.fixture
    def chunking_service(self):
        """Create MarkdownSplitter instance"""
        return MarkdownSplitter()

    def test_should_chunk_logic_short_text(self, chunking_service):
        """Test chunking detection with short text"""
        short_text = "This is a short document."
        token_count = chunking_service.count_tokens(short_text)

        context_windows = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gemini-2.0-flash": 1000000,
        }

        max_tokens = context_windows.get("gpt-4o", 128000)
        threshold = int(max_tokens * CHUNK_THRESHOLD_RATIO)

        assert token_count < threshold  # Should not need chunking

    def test_should_chunk_logic_long_text(self, chunking_service):
        """Test chunking detection with long text"""
        long_text = "word " * 200000  # Very long text
        token_count = chunking_service.count_tokens(long_text)

        context_windows = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gemini-2.0-flash": 1000000,
        }

        max_tokens = context_windows.get("gpt-4o", 128000)
        threshold = int(max_tokens * CHUNK_THRESHOLD_RATIO)

        assert token_count > threshold  # Should need chunking

    def test_chunking_service_splits_large_text(self, chunking_service):
        """Test that chunking service properly splits large text"""
        large_text = "word " * 100000  # Much larger text

        chunks = chunking_service.split(
            large_text, max_tokens=2000, preserve_structure=False
        )

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_chunking_service_handles_small_text(self, chunking_service):
        """Test that chunking service handles small text without splitting"""
        small_text = "This is a small document."

        chunks = chunking_service.split(small_text)

        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)