"""Property-based tests for document upload file validation (Properties 8, 9).

**Validates: Requirements 2.1, 2.2, 2.3**

Property 8: File Type Enforcement
— For any file with MIME type not in {application/pdf, image/png, image/jpeg},
upload is rejected with HTTP 422.

Property 9: Size Enforcement
— For any file exceeding 10,485,760 bytes, upload is rejected with HTTP 422.
"""

import pytest
from fastapi import HTTPException
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.api.documents import _validate_file, MAX_FILE_SIZE, ALLOWED_MIME_TYPES


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------

# Strategy for MIME types that are NOT in the allowed set
# Generates random strings that look like MIME types but are not allowed
_mime_type_strategy = st.one_of(
    # Random "type/subtype" patterns
    st.tuples(
        st.text(
            alphabet=st.characters(whitelist_categories=("L",)),
            min_size=1,
            max_size=20,
        ),
        st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=30,
        ),
    ).map(lambda t: f"{t[0]}/{t[1]}"),
    # Common invalid MIME types
    st.sampled_from([
        "text/plain",
        "application/json",
        "image/gif",
        "image/bmp",
        "image/webp",
        "application/zip",
        "application/octet-stream",
        "video/mp4",
        "audio/mpeg",
        "text/html",
        "application/xml",
        "image/svg+xml",
        "application/msword",
    ]),
).filter(lambda mime: mime not in ALLOWED_MIME_TYPES)

# Strategy for file sizes that exceed the maximum
_oversized_strategy = st.integers(
    min_value=MAX_FILE_SIZE + 1,
    max_value=MAX_FILE_SIZE + 5_000_000,  # Up to ~15 MB to keep memory reasonable
)


# ---------------------------------------------------------------------------
# Property 8: File Type Enforcement
# ---------------------------------------------------------------------------


class TestFileTypeEnforcementProperty:
    """Property 8: File Type Enforcement.

    **Validates: Requirements 2.1**

    For any file with MIME type not in {application/pdf, image/png, image/jpeg},
    upload is rejected with HTTP 422.
    """

    @given(invalid_mime=_mime_type_strategy)
    @settings(max_examples=100, deadline=None)
    def test_invalid_mime_type_rejected_with_422(self, invalid_mime: str):
        """For any MIME type not in the allowed set, _validate_file raises
        HTTPException with status_code 422."""
        # Use minimal valid content (non-empty, under size limit)
        content = b"x"

        with pytest.raises(HTTPException) as exc_info:
            _validate_file(
                content=content,
                content_type=invalid_mime,
                filename="test.pdf",
            )

        assert exc_info.value.status_code == 422
        assert "Tipo de archivo no soportado" in exc_info.value.detail

    @given(valid_mime=st.sampled_from(sorted(ALLOWED_MIME_TYPES)))
    @settings(max_examples=30, deadline=None)
    def test_valid_mime_type_not_rejected_for_mime_reason(self, valid_mime: str):
        """For any MIME type in the allowed set with matching extension,
        _validate_file does NOT raise HTTPException for MIME type reasons."""
        # Map MIME types to valid matching extensions
        mime_to_ext = {
            "application/pdf": "test.pdf",
            "image/png": "test.png",
            "image/jpeg": "test.jpg",
        }
        filename = mime_to_ext[valid_mime]
        content = b"valid content here"

        # Should NOT raise any exception
        _validate_file(content=content, content_type=valid_mime, filename=filename)


# ---------------------------------------------------------------------------
# Property 9: Size Enforcement
# ---------------------------------------------------------------------------


class TestSizeEnforcementProperty:
    """Property 9: Size Enforcement.

    **Validates: Requirements 2.2, 2.3**

    For any file exceeding 10,485,760 bytes, upload is rejected with HTTP 422.
    """

    @given(file_size=_oversized_strategy)
    @settings(max_examples=50, deadline=None)
    def test_oversized_file_rejected_with_422(self, file_size: int):
        """For any file exceeding MAX_FILE_SIZE bytes, _validate_file raises
        HTTPException with status_code 422."""
        content = b"x" * file_size

        with pytest.raises(HTTPException) as exc_info:
            _validate_file(
                content=content,
                content_type="application/pdf",
                filename="test.pdf",
            )

        assert exc_info.value.status_code == 422
        assert "tamaño máximo" in exc_info.value.detail

    @given(
        file_size=st.integers(min_value=1, max_value=MAX_FILE_SIZE),
    )
    @settings(max_examples=50, deadline=None)
    def test_file_within_size_limit_not_rejected_for_size(self, file_size: int):
        """For any file at or under MAX_FILE_SIZE with valid MIME and extension,
        _validate_file does NOT raise HTTPException for size reasons."""
        content = b"x" * file_size

        # Use valid MIME type and matching extension
        _validate_file(
            content=content,
            content_type="application/pdf",
            filename="test.pdf",
        )

    def test_boundary_exactly_max_size_accepted(self):
        """A file of exactly MAX_FILE_SIZE bytes is accepted (boundary test)."""
        content = b"x" * MAX_FILE_SIZE

        # Should NOT raise
        _validate_file(
            content=content,
            content_type="application/pdf",
            filename="test.pdf",
        )

    def test_boundary_one_byte_over_max_size_rejected(self):
        """A file of MAX_FILE_SIZE + 1 bytes is rejected (boundary test)."""
        content = b"x" * (MAX_FILE_SIZE + 1)

        with pytest.raises(HTTPException) as exc_info:
            _validate_file(
                content=content,
                content_type="application/pdf",
                filename="test.pdf",
            )

        assert exc_info.value.status_code == 422
