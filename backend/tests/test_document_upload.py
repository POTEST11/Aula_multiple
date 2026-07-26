"""Unit tests for the document upload endpoint validation logic."""

import pytest
from fastapi import HTTPException

from app.api.documents import _validate_file


class TestValidateFile:
    """Tests for _validate_file validation function."""

    def test_empty_file_rejected(self):
        """A 0-byte file is rejected with appropriate message."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=b"", content_type="application/pdf", filename="doc.pdf")
        assert exc_info.value.status_code == 422
        assert "vacío" in exc_info.value.detail

    def test_oversized_file_rejected(self):
        """A file exceeding 10 MB is rejected."""
        content = b"x" * (10_485_761)
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=content, content_type="application/pdf", filename="doc.pdf")
        assert exc_info.value.status_code == 422
        assert "tamaño máximo" in exc_info.value.detail

    def test_invalid_mime_type_rejected(self):
        """A file with unsupported MIME type is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=b"data", content_type="application/msword", filename="doc.docx")
        assert exc_info.value.status_code == 422
        assert "Formatos válidos" in exc_info.value.detail

    def test_extension_mime_mismatch_rejected(self):
        """A file whose extension doesn't match its MIME type is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=b"data", content_type="application/pdf", filename="image.png")
        assert exc_info.value.status_code == 422
        assert "no coincide" in exc_info.value.detail

    def test_valid_pdf_passes(self):
        """A valid PDF file passes all validation."""
        _validate_file(content=b"pdf content", content_type="application/pdf", filename="doc.pdf")

    def test_valid_png_passes(self):
        """A valid PNG file passes all validation."""
        _validate_file(content=b"png content", content_type="image/png", filename="image.png")

    def test_valid_jpeg_passes(self):
        """A valid JPEG with .jpg extension passes."""
        _validate_file(content=b"jpeg content", content_type="image/jpeg", filename="photo.jpg")

    def test_valid_jpeg_long_extension_passes(self):
        """A valid JPEG with .jpeg extension passes."""
        _validate_file(content=b"jpeg content", content_type="image/jpeg", filename="photo.jpeg")

    def test_exactly_10mb_passes(self):
        """A file that is exactly 10 MB should pass size validation."""
        content = b"x" * 10_485_760
        _validate_file(content=content, content_type="application/pdf", filename="big.pdf")

    def test_validation_order_empty_before_size(self):
        """Empty file check comes before size check (0 bytes → empty message, not size)."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=b"", content_type="invalid/type", filename="bad.xyz")
        assert "vacío" in exc_info.value.detail

    def test_validation_order_size_before_mime(self):
        """Size check comes before MIME type check."""
        content = b"x" * (10_485_761)
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=content, content_type="application/msword", filename="doc.docx")
        assert "tamaño máximo" in exc_info.value.detail

    def test_validation_order_mime_before_extension(self):
        """MIME type check comes before extension-MIME match check."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=b"data", content_type="text/plain", filename="doc.pdf")
        assert "Formatos válidos" in exc_info.value.detail

    def test_unknown_extension_with_valid_mime_rejected(self):
        """An unknown extension that doesn't map to MIME type is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(content=b"data", content_type="application/pdf", filename="doc.xyz")
        assert "no coincide" in exc_info.value.detail
