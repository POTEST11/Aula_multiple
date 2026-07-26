"""Unit tests for the document delete endpoint."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.dependencies import get_current_user, get_db
from app.models.class_document import ClassDocument
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: int = 1) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "profesor@aula.com"
    user.name = "Profesor Test"
    user.password_hash = "hashed"
    user.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return user


def _make_document(doc_id: int = 1, classroom_id: int = 10, status: str = "ready") -> MagicMock:
    doc = MagicMock(spec=ClassDocument)
    doc.id = doc_id
    doc.classroom_id = classroom_id
    doc.user_id = 1
    doc.filename = "abc123.pdf"
    doc.original_filename = "notes.pdf"
    doc.file_path = "/app/uploads/10/abc123.pdf"
    doc.mime_type = "application/pdf"
    doc.file_size_bytes = 1024
    doc.status = status
    doc.error_message = None
    doc.chunk_count = 5
    doc.uploaded_at = datetime(2024, 6, 2, 10, 0, 0, tzinfo=timezone.utc)
    doc.processed_at = datetime(2024, 6, 2, 10, 1, 0, tzinfo=timezone.utc)
    return doc


def _make_classroom(classroom_id: int = 10, user_id: int = 1) -> MagicMock:
    c = MagicMock()
    c.id = classroom_id
    c.user_id = user_id
    c.owner_id = user_id
    return c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_document_success():
    """DELETE returns 204 and removes document from DB and disk."""
    app = create_app()
    user = _make_user()
    doc = _make_document()

    mock_db = AsyncMock()
    # Mock the execute call that verifies classroom ownership
    mock_result_classroom = MagicMock()
    # Mock the execute call that queries document
    mock_result_doc = MagicMock()
    mock_result_doc.scalar_one_or_none.return_value = doc

    mock_db.execute = AsyncMock(side_effect=[
        MagicMock(),  # get_class_by_id result (handled internally)
        mock_result_doc,
    ])
    mock_db.delete = AsyncMock()
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.crud.classes.get_class_by_id", new_callable=AsyncMock) as mock_get_class:
        mock_get_class.return_value = _make_classroom()

        # Mock Path.unlink to simulate file deletion
        with patch.object(Path, "unlink") as mock_unlink:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.delete("/api/v1/classes/10/documents/1")

            assert resp.status_code == 204
            mock_unlink.assert_called_once()
            mock_db.delete.assert_called_once_with(doc)
            mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_document_not_found():
    """DELETE returns 404 when document doesn't exist."""
    app = create_app()
    user = _make_user()

    mock_db = AsyncMock()
    # First execute call is for ownership check (returns classroom), second is for document query
    mock_result_classroom = MagicMock()
    mock_result_classroom.scalar_one_or_none.return_value = _make_classroom()
    mock_result_doc = MagicMock()
    mock_result_doc.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(side_effect=[mock_result_classroom, mock_result_doc])
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.delete("/api/v1/classes/10/documents/999")

    assert resp.status_code == 404
    assert "Documento no encontrado" in resp.json()["detail"]


@pytest.mark.anyio
async def test_delete_document_classroom_not_owned():
    """DELETE returns 404 when classroom doesn't belong to user."""
    app = create_app()
    user = _make_user()

    mock_db = AsyncMock()
    # Ownership check: get_class_by_id calls db.execute and .scalar_one_or_none() returns None
    mock_result_classroom = MagicMock()
    mock_result_classroom.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result_classroom)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.delete("/api/v1/classes/10/documents/1")

    assert resp.status_code == 404
    assert "Clase no encontrada" in resp.json()["detail"]


@pytest.mark.anyio
async def test_delete_document_file_missing_on_disk():
    """DELETE succeeds even when physical file doesn't exist on disk (Req 9.3)."""
    app = create_app()
    user = _make_user()
    doc = _make_document()

    mock_db = AsyncMock()
    mock_result_doc = MagicMock()
    mock_result_doc.scalar_one_or_none.return_value = doc
    mock_db.execute = AsyncMock(return_value=mock_result_doc)
    mock_db.delete = AsyncMock()
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.crud.classes.get_class_by_id", new_callable=AsyncMock) as mock_get_class:
        mock_get_class.return_value = _make_classroom()

        # File doesn't exist on disk - unlink raises FileNotFoundError
        with patch.object(Path, "unlink", side_effect=FileNotFoundError):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.delete("/api/v1/classes/10/documents/1")

            # Should still succeed
            assert resp.status_code == 204
            mock_db.delete.assert_called_once_with(doc)
            mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_document_with_processing_status():
    """DELETE succeeds even when document has status 'processing' (Req 9.6)."""
    app = create_app()
    user = _make_user()
    doc = _make_document(status="processing")

    mock_db = AsyncMock()
    mock_result_doc = MagicMock()
    mock_result_doc.scalar_one_or_none.return_value = doc
    mock_db.execute = AsyncMock(return_value=mock_result_doc)
    mock_db.delete = AsyncMock()
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.crud.classes.get_class_by_id", new_callable=AsyncMock) as mock_get_class:
        mock_get_class.return_value = _make_classroom()

        with patch.object(Path, "unlink"):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.delete("/api/v1/classes/10/documents/1")

            assert resp.status_code == 204
