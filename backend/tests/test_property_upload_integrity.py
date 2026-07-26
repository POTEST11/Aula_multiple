"""Property-based tests for upload integrity (Property 1).

**Validates: Requirements 1.1**

Property 1: Upload Integrity
— For any valid file upload that returns HTTP 202, a file exists on disk at
the stored path AND a row exists in class_documents with status="pending" and
correct metadata (filename, mime_type, file_size_bytes, classroom_id, user_id).
"""

import asyncio
import tempfile
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


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------

# Valid MIME types and their valid extensions
_VALID_FILE_TYPES = [
    ("application/pdf", ".pdf"),
    ("image/png", ".png"),
    ("image/jpeg", ".jpg"),
    ("image/jpeg", ".jpeg"),
]

# Strategy for picking a valid (mime_type, extension) pair
_file_type_strategy = st.sampled_from(_VALID_FILE_TYPES)

# Strategy for file content: non-empty binary content up to ~100 KB
# (keeping small to avoid memory pressure in hypothesis)
_file_content_strategy = st.binary(min_size=1, max_size=100_000)

# Strategy for original filenames (reasonable characters)
_filename_base_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="-_",
    ),
    min_size=1,
    max_size=30,
).filter(lambda s: len(s.strip()) > 0)

# Strategy for class_id and user_id
_class_id_strategy = st.integers(min_value=1, max_value=10_000)
_user_id_strategy = st.integers(min_value=1, max_value=10_000)


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


async def _run_upload_test(
    mime_type: str,
    extension: str,
    content: bytes,
    original_filename: str,
    class_id: int,
    user_id: int,
    tmp_upload_dir: Path,
) -> None:
    """Run a single upload test iteration asynchronously."""
    # Track documents added to "database"
    created_documents: list = []

    # Create a mock DB session that captures the document created
    mock_db = AsyncMock()

    async def mock_commit():
        for doc in created_documents:
            if not hasattr(doc, "id") or doc.id is None:
                doc.id = 1
            if doc.uploaded_at is None:
                doc.uploaded_at = datetime.now(timezone.utc)

    async def mock_refresh(obj):
        pass

    def mock_add(obj):
        created_documents.append(obj)

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh
    mock_db.add = mock_add

    # Create the app with overrides
    app = create_app()
    user = _make_user(user_id)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock classroom ownership and the upload directory
    mock_classroom = MagicMock()
    mock_classroom.id = class_id
    mock_classroom.user_id = user_id

    with patch(
        "app.api.documents.get_class_by_id", new_callable=AsyncMock
    ) as mock_get_class, patch(
        "app.api.documents.UPLOAD_BASE_DIR", tmp_upload_dir
    ), patch(
        "app.api.documents.process_document_task", new_callable=AsyncMock
    ) as mock_process:
        mock_get_class.return_value = mock_classroom

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                f"/api/v1/classes/{class_id}/documents",
                files={
                    "file": (original_filename, content, mime_type),
                },
            )

    # --- Assertions ---
    # 1. Response is HTTP 202
    assert resp.status_code == 202, (
        f"Expected 202, got {resp.status_code}: {resp.text}"
    )

    # 2. A ClassDocument was created
    assert len(created_documents) == 1, (
        f"Expected 1 document created, got {len(created_documents)}"
    )
    doc = created_documents[0]

    # 3. Document has status="pending"
    assert doc.status == "pending", (
        f"Expected status='pending', got '{doc.status}'"
    )

    # 4. Metadata is correct
    assert doc.classroom_id == class_id, (
        f"Expected classroom_id={class_id}, got {doc.classroom_id}"
    )
    assert doc.user_id == user_id, (
        f"Expected user_id={user_id}, got {doc.user_id}"
    )
    assert doc.mime_type == mime_type, (
        f"Expected mime_type='{mime_type}', got '{doc.mime_type}'"
    )
    assert doc.file_size_bytes == len(content), (
        f"Expected file_size_bytes={len(content)}, got {doc.file_size_bytes}"
    )
    assert doc.original_filename == original_filename, (
        f"Expected original_filename='{original_filename}', "
        f"got '{doc.original_filename}'"
    )

    # 5. A file exists on disk at the stored path
    stored_path = Path(doc.file_path)
    assert stored_path.exists(), (
        f"File does not exist at stored path: {doc.file_path}"
    )

    # 6. The file content matches what was uploaded
    disk_content = stored_path.read_bytes()
    assert disk_content == content, (
        f"File content on disk ({len(disk_content)} bytes) "
        f"does not match uploaded content ({len(content)} bytes)"
    )

    # 7. The filename has the correct extension
    assert doc.filename.endswith(extension), (
        f"Expected filename to end with '{extension}', got '{doc.filename}'"
    )

    # 8. The file is stored in the correct classroom subdirectory
    expected_dir = tmp_upload_dir / str(class_id)
    assert stored_path.parent == expected_dir, (
        f"Expected file in '{expected_dir}', got '{stored_path.parent}'"
    )

    # 9. Response JSON matches the document metadata
    resp_data = resp.json()
    assert resp_data["status"] == "pending"
    assert resp_data["mime_type"] == mime_type
    assert resp_data["file_size_bytes"] == len(content)
    assert resp_data["classroom_id"] == class_id
    assert resp_data["original_filename"] == original_filename
    assert resp_data["chunk_count"] is None
    assert resp_data["processed_at"] is None


# ---------------------------------------------------------------------------
# Property 1: Upload Integrity
# ---------------------------------------------------------------------------


class TestUploadIntegrityProperty:
    """Property 1: Upload Integrity.

    **Validates: Requirements 1.1**

    For any valid file upload that returns HTTP 202, a file exists on disk at
    the stored path AND a row exists in class_documents with status="pending"
    and correct metadata (filename, mime_type, file_size_bytes, classroom_id,
    user_id).
    """

    @given(
        file_type=_file_type_strategy,
        content=_file_content_strategy,
        filename_base=_filename_base_strategy,
        class_id=_class_id_strategy,
        user_id=_user_id_strategy,
    )
    @settings(max_examples=50, deadline=None)
    def test_successful_upload_creates_file_and_record(
        self,
        file_type: tuple[str, str],
        content: bytes,
        filename_base: str,
        class_id: int,
        user_id: int,
    ):
        """For any valid file upload that returns HTTP 202:
        - A file exists on disk at the stored path
        - A row exists in class_documents with status="pending"
        - Metadata (filename, mime_type, file_size_bytes, classroom_id, user_id)
          is correct
        """
        mime_type, extension = file_type
        original_filename = f"{filename_base}{extension}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_upload_dir = Path(tmp_dir)
            asyncio.run(
                _run_upload_test(
                    mime_type=mime_type,
                    extension=extension,
                    content=content,
                    original_filename=original_filename,
                    class_id=class_id,
                    user_id=user_id,
                    tmp_upload_dir=tmp_upload_dir,
                )
            )
