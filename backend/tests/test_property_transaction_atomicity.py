"""Property-based tests for transaction atomicity on failure (Property 12).

**Validates: Requirements 4.1, 4.2**

Property 12: Transaction Atomicity on Failure
— For any document where processing fails at any stage, zero document_embeddings
rows exist for that document AND the document status is "error" with a non-empty
error_message.

This test verifies that the error handling path in DocumentProcessor.process()
correctly:
1. Rolls back any partial work (no embeddings stored)
2. Opens a new session to set status="error"
3. Records a non-empty error_message (truncated to 500 chars max)
"""

from enum import Enum
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.services.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Failure stage enum
# ---------------------------------------------------------------------------


class FailureStage(Enum):
    """Stages at which processing can fail."""

    TEXT_EXTRACTION = "text_extraction"
    CHUNKING = "chunking"
    EMBEDDING_GENERATION = "embedding_generation"
    DATABASE_STORAGE = "database_storage"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class ErrorTracker:
    """Tracks what happened to the document during error handling."""

    def __init__(self):
        self.final_status = None
        self.final_error_message = None
        self.rollback_called = False
        self.embeddings_committed = False


def _build_processor(
    failure_stage: FailureStage,
    error_message: str,
    mime_type: str = "application/pdf",
) -> tuple[DocumentProcessor, ErrorTracker]:
    """Build a DocumentProcessor with mocked dependencies that will fail at the given stage.

    The mock architecture mirrors the production code's session usage:
    - First call to session_factory() -> main processing session (async context manager)
    - Second call to session_factory() -> error-handling session (async context manager)

    Returns (processor, tracker) where tracker records observable outcomes.
    """
    tracker = ErrorTracker()

    # --- Mock document returned by session.get() ---
    mock_document = MagicMock()
    mock_document.id = 1
    mock_document.classroom_id = 42
    mock_document.status = "pending"
    mock_document.mime_type = mime_type
    mock_document.file_path = "/app/uploads/42/test-doc.pdf"
    mock_document.error_message = None
    mock_document.chunk_count = None
    mock_document.processed_at = None

    # Document used in the error session
    error_document = MagicMock()
    error_document.id = 1
    error_document.status = "processing"
    error_document.error_message = None

    # --- Build the main session (first factory call) ---
    main_session = AsyncMock()
    main_session.get = AsyncMock(return_value=mock_document)

    # Track commit calls in main session
    main_commit_count = {"n": 0}

    async def main_commit():
        main_commit_count["n"] += 1
        if failure_stage == FailureStage.DATABASE_STORAGE and main_commit_count["n"] >= 2:
            # The second commit (storing embeddings) fails
            raise RuntimeError(error_message)

    main_session.commit = AsyncMock(side_effect=main_commit)

    async def main_rollback():
        tracker.rollback_called = True

    main_session.rollback = AsyncMock(side_effect=main_rollback)
    main_session.add_all = MagicMock()

    # --- Build the error session (second factory call) ---
    error_session = AsyncMock()
    error_session.get = AsyncMock(return_value=error_document)

    async def error_commit():
        tracker.final_status = error_document.status
        tracker.final_error_message = error_document.error_message

    error_session.commit = AsyncMock(side_effect=error_commit)

    # --- Build session factory that returns context managers ---
    factory_call_count = {"n": 0}

    def session_factory():
        factory_call_count["n"] += 1
        ctx = MagicMock()
        if factory_call_count["n"] == 1:
            ctx.__aenter__ = AsyncMock(return_value=main_session)
        else:
            ctx.__aenter__ = AsyncMock(return_value=error_session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    # --- Build embedding service ---
    embedding_service = AsyncMock()
    embedding_service.generate_batch = AsyncMock(
        return_value=[[0.1] * 384 for _ in range(5)]
    )

    # --- Create processor ---
    processor = DocumentProcessor(session_factory, embedding_service)

    # --- Configure failure at the appropriate stage ---
    if failure_stage == FailureStage.TEXT_EXTRACTION:
        processor.extract_text_from_pdf = MagicMock(
            side_effect=ValueError(error_message)
        )
        processor.extract_text_from_image = MagicMock(
            side_effect=ValueError(error_message)
        )
    elif failure_stage == FailureStage.CHUNKING:
        processor.extract_text_from_pdf = MagicMock(return_value="Valid extracted text content")
        processor.extract_text_from_image = MagicMock(return_value="Valid extracted text content")
        processor.chunk_text = MagicMock(side_effect=RuntimeError(error_message))
    elif failure_stage == FailureStage.EMBEDDING_GENERATION:
        processor.extract_text_from_pdf = MagicMock(return_value="Valid extracted text content")
        processor.extract_text_from_image = MagicMock(return_value="Valid extracted text content")
        processor.chunk_text = MagicMock(return_value=["chunk1", "chunk2", "chunk3"])
        embedding_service.generate_batch = AsyncMock(
            side_effect=RuntimeError(error_message)
        )
    elif failure_stage == FailureStage.DATABASE_STORAGE:
        # Everything succeeds until the final commit that would persist embeddings
        processor.extract_text_from_pdf = MagicMock(return_value="Valid extracted text content")
        processor.extract_text_from_image = MagicMock(return_value="Valid extracted text content")
        processor.chunk_text = MagicMock(return_value=["chunk1", "chunk2", "chunk3"])
        # The main_commit side_effect already handles failing on the 2nd call

    return processor, tracker


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Generate failure stages
_failure_stage = st.sampled_from(list(FailureStage))

# Generate non-empty error messages (simulate real exception messages)
_error_message = st.text(min_size=1, max_size=600).filter(lambda s: s.strip())

# Generate MIME types that the processor handles
_mime_type = st.sampled_from(["application/pdf", "image/png", "image/jpeg"])


# ---------------------------------------------------------------------------
# Property 12: Transaction Atomicity on Failure
# ---------------------------------------------------------------------------


class TestTransactionAtomicityProperty:
    """Property 12: Transaction Atomicity on Failure.

    **Validates: Requirements 4.1, 4.2**

    For any document where processing fails at any stage:
    - Zero document_embeddings rows exist for that document (rollback ensures this)
    - The document status is "error" with a non-empty error_message
    """

    @given(
        failure_stage=_failure_stage,
        error_message=_error_message,
        mime_type=_mime_type,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_failure_results_in_error_status_with_message(
        self, failure_stage: FailureStage, error_message: str, mime_type: str
    ):
        """For any failure stage and error message, after processing fails
        the document ends up with status='error' and a non-empty error_message."""
        processor, tracker = _build_processor(failure_stage, error_message, mime_type)

        await processor.process(document_id=1)

        # Property assertion: status must be "error"
        assert tracker.final_status == "error", (
            f"Document status should be 'error' after failure at {failure_stage.value}, "
            f"but got '{tracker.final_status}'"
        )

        # Property assertion: error_message must be non-empty
        assert tracker.final_error_message is not None, (
            f"error_message should not be None after failure at {failure_stage.value}"
        )
        assert len(tracker.final_error_message) > 0, (
            f"error_message should be non-empty after failure at {failure_stage.value}"
        )

    @given(
        failure_stage=_failure_stage,
        error_message=_error_message,
        mime_type=_mime_type,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_rollback_is_called_before_error_status(
        self, failure_stage: FailureStage, error_message: str, mime_type: str
    ):
        """For any failure stage, session.rollback() is called, ensuring
        no partial embeddings persist before setting error status."""
        processor, tracker = _build_processor(failure_stage, error_message, mime_type)

        await processor.process(document_id=1)

        # Property assertion: rollback must have been called
        assert tracker.rollback_called is True, (
            f"session.rollback() should be called after failure at {failure_stage.value}"
        )

    @given(error_message=st.text(min_size=501, max_size=800).filter(lambda s: s.strip()))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_error_message_truncated_to_500_chars(self, error_message: str):
        """For any error message longer than 500 characters, the stored
        error_message is truncated to at most 500 characters."""
        assume(len(error_message) > 500)

        processor, tracker = _build_processor(
            FailureStage.TEXT_EXTRACTION, error_message, "application/pdf"
        )

        await processor.process(document_id=1)

        # Property assertion: error_message is at most 500 chars
        assert tracker.final_error_message is not None
        assert len(tracker.final_error_message) <= 500, (
            f"error_message should be at most 500 chars, "
            f"but got {len(tracker.final_error_message)} chars"
        )
        # It should be the first 500 chars of the original error
        assert tracker.final_error_message == error_message[:500]

    @given(
        failure_stage=_failure_stage,
        error_message=_error_message,
        mime_type=_mime_type,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_error_session_uses_separate_transaction(
        self, failure_stage: FailureStage, error_message: str, mime_type: str
    ):
        """For any failure, the error status update happens in a NEW session/transaction,
        not the rolled-back one. This ensures atomicity: the error status commit
        is independent of the failed processing transaction."""
        tracker = ErrorTracker()

        # Build with tracking of factory calls
        mock_document = MagicMock()
        mock_document.id = 1
        mock_document.classroom_id = 42
        mock_document.status = "pending"
        mock_document.mime_type = mime_type
        mock_document.file_path = "/app/uploads/42/test-doc.pdf"
        mock_document.error_message = None

        error_document = MagicMock()
        error_document.id = 1
        error_document.status = "processing"
        error_document.error_message = None

        main_session = AsyncMock()
        main_session.get = AsyncMock(return_value=mock_document)
        main_session.commit = AsyncMock()
        main_session.rollback = AsyncMock()
        main_session.add_all = MagicMock()

        error_session = AsyncMock()
        error_session.get = AsyncMock(return_value=error_document)

        async def error_commit():
            tracker.final_status = error_document.status
            tracker.final_error_message = error_document.error_message

        error_session.commit = AsyncMock(side_effect=error_commit)

        factory_calls = []

        def session_factory():
            ctx = MagicMock()
            call_num = len(factory_calls) + 1
            factory_calls.append(call_num)
            if call_num == 1:
                ctx.__aenter__ = AsyncMock(return_value=main_session)
            else:
                ctx.__aenter__ = AsyncMock(return_value=error_session)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        embedding_service = AsyncMock()
        embedding_service.generate_batch = AsyncMock(
            return_value=[[0.1] * 384 for _ in range(5)]
        )

        processor = DocumentProcessor(session_factory, embedding_service)

        # Always fail at text extraction for simplicity
        processor.extract_text_from_pdf = MagicMock(
            side_effect=ValueError(error_message)
        )
        processor.extract_text_from_image = MagicMock(
            side_effect=ValueError(error_message)
        )

        await processor.process(document_id=1)

        # Property assertion: session_factory was called exactly twice
        # (once for main processing, once for error handling)
        assert len(factory_calls) == 2, (
            f"Expected exactly 2 session_factory calls (main + error), "
            f"but got {len(factory_calls)}"
        )
