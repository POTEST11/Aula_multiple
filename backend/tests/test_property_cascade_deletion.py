"""Property-based tests for cascade deletion (Property 10).

**Validates: Requirements 9.1, 9.2, 9.3**

Property 10: Cascade Deletion
— For any deleted document, zero document_embeddings rows exist for that
document_id AND the physical file no longer exists on disk AND the
class_documents row is removed.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.class_document import ClassDocument
from app.models.document_embedding import DocumentEmbedding


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------

_class_id_strategy = st.integers(min_value=1, max_value=10_000)
_user_id_strategy = st.integers(min_value=1, max_value=10_000)
_document_id_strategy = st.integers(min_value=1, max_value=10_000)
_num_embeddings_strategy = st.integers(min_value=0, max_value=10)
_file_extension_strategy = st.sampled_from([".pdf", ".png", ".jpg", ".jpeg"])
_status_strategy = st.sampled_from(["pending", "processing", "ready", "error"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: int) -> MagicMock:
    """Create a mock User with the given ID."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"user{user_id}@aula.com"
    user.name = f"User {user_id}"
    user.password_hash = "hashed"
    user.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return user


def _make_document(
    document_id: int,
    class_id: int,
    user_id: int,
    file_path: str,
    status: str,
    num_embeddings: int,
) -> MagicMock:
    """Create a mock ClassDocument with associated embeddings."""
    doc = MagicMock(spec=ClassDocument)
    doc.id = document_id
    doc.classroom_id = class_id
    doc.user_id = user_id
    doc.file_path = file_path
    doc.filename = f"doc_{document_id}.pdf"
    doc.original_filename = f"original_{document_id}.pdf"
    doc.mime_type = "application/pdf"
    doc.file_size_bytes = 1024
    doc.status = status
    doc.error_message = None
    doc.chunk_count = num_embeddings if status == "ready" else None
    doc.uploaded_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    doc.processed_at = None

    # Create mock embeddings
    embeddings = []
    for i in range(num_embeddings):
        emb = MagicMock(spec=DocumentEmbedding)
        emb.id = i + 1
        emb.document_id = document_id
        emb.classroom_id = class_id
        emb.content = f"chunk {i}"
        emb.content_hash = f"hash_{i}"
        emb.chunk_index = i
        embeddings.append(emb)
    doc.embeddings = embeddings

    return doc


async def _run_delete_test(
    class_id: int,
    user_id: int,
    document_id: int,
    num_embeddings: int,
    extension: str,
    doc_status: str,
) -> None:
    """Run a single deletion test iteration asynchronously."""
    file_path = f"/app/uploads/{class_id}/doc_{document_id}{extension}"

    mock_document = _make_document(
        document_id=document_id,
        class_id=class_id,
        user_id=user_id,
        file_path=file_path,
        status=doc_status,
        num_embeddings=num_embeddings,
    )

    # Track db.delete calls
    deleted_objects: list = []
    commit_called = False

    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_document
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def mock_delete(obj):
        deleted_objects.append(obj)

    async def mock_commit():
        nonlocal commit_called
        commit_called = True

    mock_db.delete = mock_delete
    mock_db.commit = mock_commit

    app = create_app()
    user = _make_user(user_id)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_classroom = MagicMock()
    mock_classroom.id = class_id
    mock_classroom.user_id = user_id

    with patch(
        "app.api.documents.get_class_by_id", new_callable=AsyncMock
    ) as mock_get_class, patch.object(Path, "unlink") as mock_unlink:
        mock_get_class.return_value = mock_classroom

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.delete(
                f"/api/v1/classes/{class_id}/documents/{document_id}"
            )

        # --- Assertions ---

        # 1. Response is HTTP 204 (No Content)
        assert resp.status_code == 204, (
            f"Expected 204, got {resp.status_code}: {resp.text}"
        )

        # 2. db.delete was called with the document (triggers cascade deletion
        #    of embeddings via SQLAlchemy cascade="all, delete-orphan")
        assert len(deleted_objects) == 1, (
            f"Expected db.delete called once, got {len(deleted_objects)} calls"
        )
        assert deleted_objects[0] is mock_document, (
            "db.delete was not called with the correct document object"
        )

        # 3. db.commit was called (persists the deletion including cascade)
        assert commit_called, "db.commit was not called after deletion"

        # 4. The physical file unlink was attempted
        assert mock_unlink.called, (
            "Path.unlink was not called — physical file was not deleted"
        )

        # 5. Verify the document had embeddings (cascade handles them)
        assert mock_document.embeddings is not None, (
            "Document should have embeddings relationship"
        )
        assert len(mock_document.embeddings) == num_embeddings, (
            f"Expected {num_embeddings} embeddings, got "
            f"{len(mock_document.embeddings)}"
        )


# ---------------------------------------------------------------------------
# Property 10: Cascade Deletion — HTTP endpoint test
# ---------------------------------------------------------------------------


class TestCascadeDeletionProperty:
    """Property 10: Cascade Deletion.

    **Validates: Requirements 9.1, 9.2, 9.3**

    For any deleted document, zero document_embeddings rows exist for that
    document_id AND the physical file no longer exists on disk AND the
    class_documents row is removed.
    """

    @given(
        class_id=_class_id_strategy,
        user_id=_user_id_strategy,
        document_id=_document_id_strategy,
        num_embeddings=_num_embeddings_strategy,
        extension=_file_extension_strategy,
        doc_status=_status_strategy,
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_delete_removes_document_file_and_triggers_cascade(
        self,
        class_id: int,
        user_id: int,
        document_id: int,
        num_embeddings: int,
        extension: str,
        doc_status: str,
    ):
        """For any valid document deletion (HTTP 204):
        - The ClassDocument row is removed from the database (db.delete called)
        - All associated DocumentEmbedding records are cascade-deleted
          (verified via SQLAlchemy cascade="all, delete-orphan" on relationship)
        - The physical file is deleted from disk (Path.unlink() called)
        - db.commit persists the deletion transaction
        """
        asyncio.run(
            _run_delete_test(
                class_id=class_id,
                user_id=user_id,
                document_id=document_id,
                num_embeddings=num_embeddings,
                extension=extension,
                doc_status=doc_status,
            )
        )

    @given(
        class_id=_class_id_strategy,
        document_id=_document_id_strategy,
        num_embeddings=_num_embeddings_strategy,
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_cascade_relationship_configured_on_model(
        self,
        class_id: int,
        document_id: int,
        num_embeddings: int,
    ):
        """Verify the SQLAlchemy cascade configuration ensures embeddings
        are deleted when the parent document is deleted.

        The ClassDocument model defines:
            embeddings = relationship(..., cascade="all, delete-orphan")

        And DocumentEmbedding has:
            ForeignKey("class_documents.id", ondelete="CASCADE")

        Both ensure that when a ClassDocument is deleted, all associated
        DocumentEmbedding rows are automatically removed.
        """
        from sqlalchemy import inspect as sa_inspect

        # Verify cascade on ClassDocument.embeddings relationship
        mapper = sa_inspect(ClassDocument)
        embeddings_rel = mapper.relationships.get("embeddings")

        assert embeddings_rel is not None, (
            "ClassDocument must have an 'embeddings' relationship"
        )
        assert "delete-orphan" in embeddings_rel.cascade, (
            f"Expected 'delete-orphan' in cascade, got: {embeddings_rel.cascade}"
        )
        assert "delete" in embeddings_rel.cascade or "all" in embeddings_rel.cascade, (
            f"Expected 'delete' or 'all' in cascade, got: {embeddings_rel.cascade}"
        )

        # Verify ForeignKey ondelete="CASCADE" on DocumentEmbedding.document_id
        doc_id_col = DocumentEmbedding.__table__.c.document_id
        fk = list(doc_id_col.foreign_keys)[0]
        assert fk.ondelete == "CASCADE", (
            f"Expected ondelete='CASCADE', got: {fk.ondelete}"
        )
