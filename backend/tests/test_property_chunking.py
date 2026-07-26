"""Property-based tests for chunking coverage (Property 11).

**Validates: Requirement 3.4**

Property 11: Chunking Coverage
— For any non-empty input text, the concatenation of all chunks (accounting
for overlap) reconstructs the original text with no data loss, and every
chunk is a non-empty string.
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.services.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reconstruct_from_chunks(chunks: list[str], chunk_overlap: int) -> str:
    """Reconstruct original text from overlapping chunks.

    Logic: result = chunks[0], then for each subsequent chunk append
    chunk[chunk_overlap:] (the non-overlapping suffix).
    """
    if not chunks:
        return ""
    result = chunks[0]
    for chunk in chunks[1:]:
        result += chunk[chunk_overlap:]
    return result


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty text strategy
_non_empty_text = st.text(min_size=1, max_size=2000)

# Chunk size and overlap strategy: chunk_size >= 2, chunk_overlap >= 0,
# chunk_overlap < chunk_size
_chunk_params = st.integers(min_value=2, max_value=500).flatmap(
    lambda chunk_size: st.tuples(
        st.just(chunk_size),
        st.integers(min_value=0, max_value=chunk_size - 1),
    )
)


# ---------------------------------------------------------------------------
# Property 11: Chunking Coverage
# ---------------------------------------------------------------------------


class TestChunkingCoverageProperty:
    """Property 11: Chunking Coverage.

    **Validates: Requirement 3.4**

    For any non-empty input text, the concatenation of all chunks
    (accounting for overlap) reconstructs the original text with no data loss,
    and every chunk is a non-empty string.
    """

    def _get_processor(self) -> DocumentProcessor:
        """Create a DocumentProcessor instance for testing chunk_text (pure method)."""
        return DocumentProcessor(None, None)

    @given(text=_non_empty_text)
    @settings(max_examples=200, deadline=None)
    def test_all_chunks_are_non_empty_default_params(self, text: str):
        """For any non-empty text with default params, all chunks are non-empty strings."""
        processor = self._get_processor()
        chunks = processor.chunk_text(text)

        assert len(chunks) >= 1, "Non-empty text must produce at least one chunk"
        for chunk in chunks:
            assert isinstance(chunk, str)
            assert len(chunk) > 0, "Every chunk must be a non-empty string"

    @given(text=_non_empty_text)
    @settings(max_examples=200, deadline=None)
    def test_reconstruction_preserves_original_default_params(self, text: str):
        """For any non-empty text with default params, reconstructing from chunks
        yields the original text (no data loss)."""
        processor = self._get_processor()
        chunk_overlap = 50
        chunks = processor.chunk_text(text, chunk_size=500, chunk_overlap=chunk_overlap)

        reconstructed = _reconstruct_from_chunks(chunks, chunk_overlap)
        assert reconstructed == text, (
            f"Reconstruction mismatch.\n"
            f"  Original length: {len(text)}\n"
            f"  Reconstructed length: {len(reconstructed)}\n"
            f"  Chunks: {len(chunks)}"
        )

    @given(
        text=_non_empty_text,
        params=_chunk_params,
    )
    @settings(max_examples=200, deadline=None)
    def test_all_chunks_are_non_empty_parametrized(self, text: str, params: tuple):
        """For any non-empty text and valid chunk_size/chunk_overlap,
        all chunks are non-empty strings."""
        chunk_size, chunk_overlap = params
        processor = self._get_processor()
        chunks = processor.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        assert len(chunks) >= 1, "Non-empty text must produce at least one chunk"
        for chunk in chunks:
            assert isinstance(chunk, str)
            assert len(chunk) > 0, "Every chunk must be a non-empty string"

    @given(
        text=_non_empty_text,
        params=_chunk_params,
    )
    @settings(max_examples=200, deadline=None)
    def test_reconstruction_preserves_original_parametrized(self, text: str, params: tuple):
        """For any non-empty text and valid chunk_size/chunk_overlap,
        reconstructing from chunks yields the original text (no data loss)."""
        chunk_size, chunk_overlap = params
        processor = self._get_processor()
        chunks = processor.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        reconstructed = _reconstruct_from_chunks(chunks, chunk_overlap)
        assert reconstructed == text, (
            f"Reconstruction mismatch.\n"
            f"  Original length: {len(text)}\n"
            f"  Reconstructed length: {len(reconstructed)}\n"
            f"  chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n"
            f"  Chunks: {len(chunks)}"
        )
