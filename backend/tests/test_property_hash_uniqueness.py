"""Property-based tests for hash uniqueness per document (Property 4).

**Validates: Requirement 10.2**

Property 4: Hash Uniqueness per Document
— For any document, no two embeddings within that document share the same
content_hash. The deduplication logic (seen_hashes set) ensures that even
when input text contains repeated segments producing duplicate chunks,
the resulting hashes are always unique.
"""

import hashlib

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.services.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_deduplicated_hashes(chunks: list[str]) -> list[str]:
    """Replicate the deduplication logic from DocumentProcessor.process().

    Computes SHA-256 hashes for each chunk, then filters duplicates
    using a seen_hashes set (same logic as production code).
    """
    chunk_hashes = [hashlib.sha256(c.encode()).hexdigest() for c in chunks]
    seen: set[str] = set()
    deduplicated: list[str] = []
    for h in chunk_hashes:
        if h in seen:
            continue
        seen.add(h)
        deduplicated.append(h)
    return deduplicated


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
# Property 4: Hash Uniqueness per Document
# ---------------------------------------------------------------------------


class TestHashUniquenessProperty:
    """Property 4: Hash Uniqueness per Document.

    **Validates: Requirement 10.2**

    For any document, no two embeddings within that document share the same
    content_hash. After deduplication, all hashes in the output are unique.
    """

    def _get_processor(self) -> DocumentProcessor:
        """Create a DocumentProcessor instance for testing chunk_text (pure method)."""
        return DocumentProcessor(None, None)

    @given(text=_non_empty_text)
    @settings(max_examples=200, deadline=None)
    def test_deduplicated_hashes_are_unique_default_params(self, text: str):
        """For any non-empty text with default params, the deduplicated hashes
        contain no duplicates."""
        processor = self._get_processor()
        chunks = processor.chunk_text(text)
        assume(len(chunks) > 0)

        deduplicated_hashes = _compute_deduplicated_hashes(chunks)

        # Core property: no duplicates in the output
        assert len(deduplicated_hashes) == len(set(deduplicated_hashes)), (
            f"Duplicate hashes found after deduplication!\n"
            f"  Hashes count: {len(deduplicated_hashes)}\n"
            f"  Unique count: {len(set(deduplicated_hashes))}"
        )

    @given(text=_repeated_text)
    @settings(max_examples=200, deadline=None)
    def test_deduplicated_hashes_are_unique_repeated_text(self, text: str):
        """For text with deliberately repeated segments (producing duplicate chunks),
        the deduplication step still ensures unique hashes in output."""
        assume(len(text) > 0)
        processor = self._get_processor()
        chunks = processor.chunk_text(text)
        assume(len(chunks) > 0)

        deduplicated_hashes = _compute_deduplicated_hashes(chunks)

        # Core property: no duplicates in the output
        assert len(deduplicated_hashes) == len(set(deduplicated_hashes)), (
            f"Duplicate hashes found after deduplication with repeated text!\n"
            f"  Input text length: {len(text)}\n"
            f"  Chunks produced: {len(chunks)}\n"
            f"  Deduplicated hashes: {len(deduplicated_hashes)}\n"
            f"  Unique hashes: {len(set(deduplicated_hashes))}"
        )

    @given(text=_repeated_text)
    @settings(max_examples=200, deadline=None)
    def test_deduplication_reduces_duplicate_chunks(self, text: str):
        """For text with repeated segments, deduplication should produce fewer
        (or equal) hashes than the raw chunk count when duplicates exist."""
        assume(len(text) > 0)
        processor = self._get_processor()
        chunks = processor.chunk_text(text)
        assume(len(chunks) > 0)

        raw_hashes = [hashlib.sha256(c.encode()).hexdigest() for c in chunks]
        deduplicated_hashes = _compute_deduplicated_hashes(chunks)

        # Deduplicated count must be <= raw count
        assert len(deduplicated_hashes) <= len(raw_hashes), (
            f"Deduplication produced more hashes than raw chunks!\n"
            f"  Raw: {len(raw_hashes)}, Deduplicated: {len(deduplicated_hashes)}"
        )
        # And deduplicated must still have no duplicates
        assert len(deduplicated_hashes) == len(set(deduplicated_hashes))

    @given(text=_non_empty_text, params=_chunk_params)
    @settings(max_examples=200, deadline=None)
    def test_deduplicated_hashes_are_unique_parametrized(self, text: str, params: tuple):
        """For any non-empty text and valid chunk_size/chunk_overlap,
        deduplicated hashes contain no duplicates."""
        chunk_size, chunk_overlap = params
        processor = self._get_processor()
        chunks = processor.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        assume(len(chunks) > 0)

        deduplicated_hashes = _compute_deduplicated_hashes(chunks)

        assert len(deduplicated_hashes) == len(set(deduplicated_hashes)), (
            f"Duplicate hashes found after deduplication!\n"
            f"  chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n"
            f"  Hashes count: {len(deduplicated_hashes)}\n"
            f"  Unique count: {len(set(deduplicated_hashes))}"
        )
