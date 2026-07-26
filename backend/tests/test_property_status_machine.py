"""Property-based tests for status machine validity (Property 7).

**Validates: Requirements 5.1, 5.2**

Property 7: Status Machine Validity
— For any document, status transitions follow exactly:
  pending → processing → ready OR pending → processing → error.
No other transitions are permitted.

This test verifies that the DocumentProcessor.process() method:
1. Successful processing follows pending → processing → ready exactly
2. Failed processing follows pending → processing → error exactly
3. Document with status != "pending" is rejected (no processing occurs)
4. No invalid transitions occur (e.g., pending → ready, pending → error directly,
   processing → pending, etc.)
"""

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class StatusTransitionTracker:
    """Tracks all status transitions that occur on a document during processing."""

    def __init__(self, initial_status: str):
        self.transitions: list[tuple[str, str]] = []
        self._current_status = initial_status
        self.initial_status = initial_status

    @property
    def current_status(self) -> str:
        return self._current_status

    @current_status.setter
    def current_status(self, new_status: str):
        self.transitions.append((self._current_status, new_status))
        self._current_status = new_status

    @property
    def status_sequence(self) -> list[str]:
        """Returns the full sequence of statuses the document went through."""
        if not self.transitions:
            return [self.initial_status]
        sequence = [self.initial_status]
        for _, to_status in self.transitions:
            sequence.append(to_status)
        return sequence


def _create_tracked_document(initial_status: str, mime_type: str) -> tuple[MagicMock, StatusTransitionTracker]:
    """Create a mock document with status tracking.

    Returns (mock_document, tracker) where tracker records all status changes.
    """
    tracker = StatusTransitionTracker(initial_status)

    mock_document = MagicMock()
    mock_document.id = 1
    mock_document.classroom_id = 42
    mock_document.file_path = "/app/uploads/42/test-doc.pdf"
    mock_document.mime_type = mime_type
    mock_document.error_message = None
    mock_document.chunk_count = None
    mock_document.processed_at = None

    # Use a property-like approach to track status changes
    type(mock_document).status = property(
        lambda self: tracker.current_status,
        lambda self, value: setattr(tracker, "current_status", value),
    )
    # Set initial status via the tracker directly (not through setter to avoid recording)
    tracker._current_status = initial_status

    return mock_document, tracker


def _build_success_processor(
    mock_document: MagicMock,
    mime_type: str,
) -> DocumentProcessor:
    """Build a DocumentProcessor that will succeed during processing."""
    # --- Main session ---
    main_session = AsyncMock()
    main_session.get = AsyncMock(return_value=mock_document)
    main_session.commit = AsyncMock()
    main_session.rollback = AsyncMock()
    main_session.add_all = MagicMock()

    # --- Session factory ---
    def session_factory():
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=main_session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    # --- Embedding service ---
    embedding_service = AsyncMock()
    embedding_service.generate_batch = AsyncMock(
        return_value=[[0.1] * 384 for _ in range(3)]
    )

    # --- Create processor with mocked extraction ---
    processor = DocumentProcessor(session_factory, embedding_service)
    processor.extract_text_from_pdf = MagicMock(return_value="Valid extracted text content for testing")
    processor.extract_text_from_image = MagicMock(return_value="Valid extracted text content for testing")
    processor.chunk_text = MagicMock(return_value=["chunk1", "chunk2", "chunk3"])

    return processor


def _build_failure_processor(
    mock_document: MagicMock,
    error_message: str,
) -> DocumentProcessor:
    """Build a DocumentProcessor that will fail during text extraction."""
    # --- Error document for the second session ---
    error_document = MagicMock()
    error_document.id = 1
    error_document.status = "processing"
    error_document.error_message = None

    # We need a separate tracker for the error document status changes
    # but what we really care about is the main document's transitions
    # The error session sets status on a re-fetched document

    # --- Main session ---
    main_session = AsyncMock()
    main_session.get = AsyncMock(return_value=mock_document)
    main_session.commit = AsyncMock()
    main_session.rollback = AsyncMock()
    main_session.add_all = MagicMock()

    # --- Error session ---
    error_session = AsyncMock()
    error_session.get = AsyncMock(return_value=mock_document)
    error_session.commit = AsyncMock()

    # --- Session factory (first call = main, second call = error) ---
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

    # --- Embedding service ---
    embedding_service = AsyncMock()

    # --- Create processor that fails at extraction ---
    processor = DocumentProcessor(session_factory, embedding_service)
    processor.extract_text_from_pdf = MagicMock(
        side_effect=ValueError(error_message)
    )
    processor.extract_text_from_image = MagicMock(
        side_effect=ValueError(error_message)
    )

    return processor


def _build_rejection_processor(
    mock_document: MagicMock,
) -> DocumentProcessor:
    """Build a DocumentProcessor for documents that should be rejected (status != pending)."""
    # --- Main session ---
    main_session = AsyncMock()
    main_session.get = AsyncMock(return_value=mock_document)
    main_session.commit = AsyncMock()
    main_session.rollback = AsyncMock()

    # --- Session factory ---
    def session_factory():
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=main_session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    # --- Embedding service ---
    embedding_service = AsyncMock()

    processor = DocumentProcessor(session_factory, embedding_service)
    return processor


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# MIME types that the processor handles
_mime_type = st.sampled_from(["application/pdf", "image/png", "image/jpeg"])

# Non-empty error messages
_error_message = st.text(min_size=1, max_size=300).filter(lambda s: s.strip())

# Statuses that are NOT "pending" — these should cause rejection
_non_pending_status = st.sampled_from(["processing", "ready", "error"])

# Valid allowed transitions
VALID_TRANSITIONS = {
    ("pending", "processing"),
    ("processing", "ready"),
    ("processing", "error"),
}

# Valid complete paths through the state machine
VALID_SUCCESS_PATH = ["pending", "processing", "ready"]
VALID_ERROR_PATH = ["pending", "processing", "error"]


# ---------------------------------------------------------------------------
# Property 7: Status Machine Validity
# ---------------------------------------------------------------------------


class TestStatusMachineValidityProperty:
    """Property 7: Status Machine Validity.

    **Validates: Requirements 5.1, 5.2**

    For any document, status transitions follow exactly:
    pending → processing → ready OR pending → processing → error.
    No other transitions are permitted.
    """

    @given(mime_type=_mime_type)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_successful_processing_follows_pending_processing_ready(
        self, mime_type: str
    ):
        """For any successful processing, the status sequence is exactly:
        pending → processing → ready."""
        mock_document, tracker = _create_tracked_document("pending", mime_type)
        processor = _build_success_processor(mock_document, mime_type)

        await processor.process(document_id=1)

        # Property assertion: status sequence must be exactly pending → processing → ready
        assert tracker.status_sequence == VALID_SUCCESS_PATH, (
            f"Expected status sequence {VALID_SUCCESS_PATH}, "
            f"but got {tracker.status_sequence}"
        )

    @given(mime_type=_mime_type, error_message=_error_message)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_failed_processing_follows_pending_processing_error(
        self, mime_type: str, error_message: str
    ):
        """For any failed processing, the status sequence is exactly:
        pending → processing → error."""
        mock_document, tracker = _create_tracked_document("pending", mime_type)
        processor = _build_failure_processor(mock_document, error_message)

        await processor.process(document_id=1)

        # Property assertion: status sequence must be exactly pending → processing → error
        assert tracker.status_sequence == VALID_ERROR_PATH, (
            f"Expected status sequence {VALID_ERROR_PATH}, "
            f"but got {tracker.status_sequence}"
        )

    @given(initial_status=_non_pending_status, mime_type=_mime_type)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_non_pending_document_is_rejected_no_transitions(
        self, initial_status: str, mime_type: str
    ):
        """For any document with status != 'pending', no status transitions occur.
        The processor returns early without modifying the document."""
        mock_document, tracker = _create_tracked_document(initial_status, mime_type)
        processor = _build_rejection_processor(mock_document)

        await processor.process(document_id=1)

        # Property assertion: no transitions should have occurred
        assert tracker.transitions == [], (
            f"Document with initial status '{initial_status}' should not have "
            f"any transitions, but got {tracker.transitions}"
        )
        # Status should remain unchanged
        assert tracker.current_status == initial_status, (
            f"Document status should remain '{initial_status}', "
            f"but got '{tracker.current_status}'"
        )

    @given(mime_type=_mime_type, error_message=_error_message)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_all_transitions_are_valid_on_success(self, mime_type: str, error_message: str):
        """For any successful processing, every individual transition is in the
        set of allowed transitions."""
        mock_document, tracker = _create_tracked_document("pending", mime_type)
        processor = _build_success_processor(mock_document, mime_type)

        await processor.process(document_id=1)

        # Property assertion: every transition must be in the valid set
        for from_status, to_status in tracker.transitions:
            assert (from_status, to_status) in VALID_TRANSITIONS, (
                f"Invalid transition: {from_status} → {to_status}. "
                f"Allowed transitions: {VALID_TRANSITIONS}. "
                f"Full sequence: {tracker.status_sequence}"
            )

    @given(mime_type=_mime_type, error_message=_error_message)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_all_transitions_are_valid_on_failure(self, mime_type: str, error_message: str):
        """For any failed processing, every individual transition is in the
        set of allowed transitions."""
        mock_document, tracker = _create_tracked_document("pending", mime_type)
        processor = _build_failure_processor(mock_document, error_message)

        await processor.process(document_id=1)

        # Property assertion: every transition must be in the valid set
        for from_status, to_status in tracker.transitions:
            assert (from_status, to_status) in VALID_TRANSITIONS, (
                f"Invalid transition: {from_status} → {to_status}. "
                f"Allowed transitions: {VALID_TRANSITIONS}. "
                f"Full sequence: {tracker.status_sequence}"
            )

    @given(mime_type=_mime_type)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_no_direct_pending_to_ready_transition(self, mime_type: str):
        """For any document processing, there is never a direct pending → ready
        transition (must always go through processing first)."""
        mock_document, tracker = _create_tracked_document("pending", mime_type)
        processor = _build_success_processor(mock_document, mime_type)

        await processor.process(document_id=1)

        # Property assertion: pending → ready must NOT be in transitions
        assert ("pending", "ready") not in tracker.transitions, (
            f"Invalid direct transition pending → ready detected. "
            f"Full sequence: {tracker.status_sequence}"
        )

    @given(mime_type=_mime_type, error_message=_error_message)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_no_direct_pending_to_error_transition(self, mime_type: str, error_message: str):
        """For any document processing that fails, there is never a direct
        pending → error transition (must always go through processing first)."""
        mock_document, tracker = _create_tracked_document("pending", mime_type)
        processor = _build_failure_processor(mock_document, error_message)

        await processor.process(document_id=1)

        # Property assertion: pending → error must NOT be in transitions
        assert ("pending", "error") not in tracker.transitions, (
            f"Invalid direct transition pending → error detected. "
            f"Full sequence: {tracker.status_sequence}"
        )
