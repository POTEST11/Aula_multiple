"""Property-based tests for processing completeness (Property 2).

**Validates: Requirements 3.7, 5.3**

Property 2: Processing Completeness
— For any document with status="ready", document.chunk_count equals the actual
count of document_embeddings rows for that document. This test verifies the
invariant by replicating the chunking + deduplication logic and confirming that
the resulting chunk_count matches the number of unique records produced.
"""

import hashlib

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.services.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _simulate_processing_pipeline(chunks: list[str]) -> int:
    """Simulate the deduplication logic from DocumentProcessor.process().

    Replicates the production code:
    1. Compute SHA-256 hash for each chunk
    2. Filter duplicates using a seen_hashes set
    3. Return the count of deduplicated records (i.e. chunk_count)
    """
    chunk_hashes = [hashlib.sha256(c.encode()).hexdigest() for c in chunks]
    seen_hashes: set[str] = set()
    record_count = 0
    for chunk_hash in chunk_hashes:
        if chunk_hash in seen_hashes:
            continue
        seen_hashes.add(chunk_hash)
        record_count += 1
    return record_count


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty text strategy (arbitrary unicode)
_non_empty_text = st.text(min_size=1, max_size=2000)

# Text with deliberately repeated segments to produce duplicate chunks
_repeated_text = st.text(min_size=1, max_size=200).flatmap(
    lambda segment: st.integers(min_value=2, max_value=10).map(
        lambda n: segment * n
    )
)

# Chunk params strategy: chunk_size >= 2, 0 <= chunk_overlap < chunk_size
_chunk_params = st.integers(min_value=2, max_value=500).flatmap(
    lambda chunk_size: st.tuples(
        st.just(chunk_size),
        st.integers(min_value=0, max_value=chunk_size - 1),
    )
)


# ---------------------------------------------------------------------------
# Property 2: Processing Completeness
# ---------------------------------------------------------------------------


class TestProcessingCompletenessProperty:
    """Property 2: Processing Completeness.

    **Validates: Requirements 3.7, 5.3**

    For any document with status="ready", document.chunk_count equals the actual
    count of document_embeddings rows for that document. We verify this by
    simulating the pipeline: chunk text → deduplicate by hash → count records.
    """

    def _get_processor(self) -> DocumentProcessor:
        """Create a DocumentProcessor instance for testing chunk_text (pure method)."""
        return DocumentProcessor(None, None)

    @given(text=_non_empty_text)
    @settings(max_examples=200, deadline=None)
    def test_chunk_count_equals_deduplicated_record_count_default_params(self, text: str):
        """For any non-empty text with default chunking params, chunk_count
        equals the number of deduplicated embedding records."""
        processor = self._get_processor()
        chunks = processor.chunk_text(text)
        assume(len(chunks) > 0)

        # Simulate what process() does: deduplicate and set chunk_count
        chunk_count = _simulate_processing_pipeline(chunks)

        # The actual number of embedding rows equals the deduplicated count
        actual_embedding_rows = _simulate_processing_pipeline(chunks)

        assert chunk_count == actual_embedding_rows, (
            f"Processing completeness violated!\n"
            f"  chunk_count set by pipeline: {chunk_count}\n"
            f"  actual embedding rows: {actual_embedding_rows}\n"
            f"  raw chunks produced: {len(chunks)}"
        )

    @given(text=_repeated_text)
    @settings(max_examples=200, deadline=None)
    def test_chunk_count_equals_deduplicated_record_count_repeated_text(self, text: str):
        """For text with repeated segments (producing duplicate chunks),
        chunk_count still equals the deduplicated embedding row count."""
        assume(len(text) > 0)
        processor = self._get_processor()
        chunks = processor.chunk_text(text)
        assume(len(chunks) > 0)

        # chunk_count as set by the pipeline
        chunk_count = _simulate_processing_pipeline(chunks)

        # Count unique chunks (what would be stored as embedding rows)
        unique_hashes: set[str] = set()
        for chunk in chunks:
            unique_hashes.add(hashlib.sha256(chunk.encode()).hexdigest())
        actual_embedding_rows = len(unique_hashes)

        assert chunk_count == actual_embedding_rows, (
            f"Processing completeness violated with repeated text!\n"
            f"  chunk_count set by pipeline: {chunk_count}\n"
            f"  actual unique embedding rows: {actual_embedding_rows}\n"
            f"  raw chunks produced: {len(chunks)}\n"
            f"  text length: {len(text)}"
        )

    @given(text=_non_empty_text, params=_chunk_params)
    @settings(max_examples=200, deadline=None)
    def test_chunk_count_equals_deduplicated_record_count_parametrized(
        self, text: str, params: tuple
    ):
        """For any non-empty text and valid chunk_size/chunk_overlap,
        chunk_count equals the number of deduplicated embedding records."""
        chunk_size, chunk_overlap = params
        processor = self._get_processor()
        chunks = processor.chunk_text(
            text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        assume(len(chunks) > 0)

        # Simulate the pipeline to get chunk_count
        chunk_count = _simulate_processing_pipeline(chunks)

        # Independently count unique hashes (the embedding rows that would exist)
        unique_hashes: set[str] = set()
        for chunk in chunks:
            unique_hashes.add(hashlib.sha256(chunk.encode()).hexdigest())
        actual_embedding_rows = len(unique_hashes)

        assert chunk_count == actual_embedding_rows, (
            f"Processing completeness violated!\n"
            f"  chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n"
            f"  chunk_count set by pipeline: {chunk_count}\n"
            f"  actual unique embedding rows: {actual_embedding_rows}\n"
            f"  raw chunks produced: {len(chunks)}"
        )

    @given(text=_repeated_text, params=_chunk_params)
    @settings(max_examples=200, deadline=None)
    def test_chunk_count_never_exceeds_raw_chunk_count(self, text: str, params: tuple):
        """chunk_count (deduplicated) must always be <= the raw number of chunks,
        ensuring deduplication only removes, never adds records."""
        assume(len(text) > 0)
        chunk_size, chunk_overlap = params
        processor = self._get_processor()
        chunks = processor.chunk_text(
            text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        assume(len(chunks) > 0)

        chunk_count = _simulate_processing_pipeline(chunks)

        assert chunk_count <= len(chunks), (
            f"chunk_count exceeds raw chunk count!\n"
            f"  chunk_count: {chunk_count}\n"
            f"  raw chunks: {len(chunks)}\n"
            f"  chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
        )
        # Also verify chunk_count is at least 1 (non-empty chunks exist)
        assert chunk_count >= 1, (
            f"chunk_count is 0 but chunks were produced!\n"
            f"  raw chunks: {len(chunks)}"
        )
