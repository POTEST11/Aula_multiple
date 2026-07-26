"""Unit tests for DocumentProcessor.chunk_text method."""

import pytest

from app.services.document_processor import DocumentProcessor


@pytest.fixture
def processor():
    """Create a DocumentProcessor instance without dependencies (only testing chunk_text)."""
    return DocumentProcessor(session_factory=None, embedding_service=None)


class TestChunkText:
    """Tests for chunk_text method."""

    def test_empty_text_returns_empty_list(self, processor: DocumentProcessor):
        """Empty input returns no chunks."""
        assert processor.chunk_text("") == []

    def test_short_text_single_chunk(self, processor: DocumentProcessor):
        """Text shorter than chunk_size produces a single chunk."""
        text = "Hello world"
        result = processor.chunk_text(text, chunk_size=500, chunk_overlap=50)
        assert result == [text]

    def test_exact_chunk_size_single_chunk(self, processor: DocumentProcessor):
        """Text exactly equal to chunk_size produces a single chunk."""
        text = "A" * 500
        result = processor.chunk_text(text, chunk_size=500, chunk_overlap=50)
        assert result == [text]

    def test_basic_chunking_with_overlap(self, processor: DocumentProcessor):
        """Text 'ABCDEFGHIJ' with chunk_size=5, overlap=2 produces correct chunks."""
        text = "ABCDEFGHIJ"
        result = processor.chunk_text(text, chunk_size=5, chunk_overlap=2)
        assert result == ["ABCDE", "DEFGH", "GHIJ"]

    def test_all_chunks_non_empty(self, processor: DocumentProcessor):
        """All produced chunks must be non-empty strings."""
        text = "A" * 1000
        result = processor.chunk_text(text, chunk_size=500, chunk_overlap=50)
        assert all(len(chunk) > 0 for chunk in result)

    def test_reconstruction_no_data_loss(self, processor: DocumentProcessor):
        """Concatenating chunks (accounting for overlap) reconstructs original text."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunk_size = 10
        chunk_overlap = 3
        result = processor.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Reconstruct: first chunk in full, then for each subsequent chunk
        # take only the non-overlapping part (everything after chunk_overlap chars)
        reconstructed = result[0]
        for chunk in result[1:]:
            reconstructed += chunk[chunk_overlap:]

        assert reconstructed == text

    def test_adjacent_chunks_overlap_correctly(self, processor: DocumentProcessor):
        """Adjacent chunks share exactly chunk_overlap characters."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunk_size = 10
        chunk_overlap = 3
        result = processor.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        for i in range(len(result) - 1):
            # The last chunk_overlap chars of chunk[i] should equal
            # the first chunk_overlap chars of chunk[i+1]
            tail = result[i][-chunk_overlap:]
            head = result[i + 1][:chunk_overlap]
            assert tail == head, f"Chunks {i} and {i+1} don't overlap correctly"

    def test_default_parameters(self, processor: DocumentProcessor):
        """Default chunk_size=500, chunk_overlap=50 works correctly."""
        text = "X" * 1000
        result = processor.chunk_text(text)
        # With step=450, chunks: [0:500], [450:950], [900:1000]
        assert len(result) == 3
        assert len(result[0]) == 500
        assert len(result[1]) == 500
        assert len(result[2]) == 100

    def test_last_chunk_shorter_than_chunk_size(self, processor: DocumentProcessor):
        """The last chunk can be shorter than chunk_size."""
        text = "A" * 510
        result = processor.chunk_text(text, chunk_size=500, chunk_overlap=50)
        # step=450, chunks: [0:500], [450:510]
        assert len(result) == 2
        assert len(result[0]) == 500
        assert len(result[1]) == 60
