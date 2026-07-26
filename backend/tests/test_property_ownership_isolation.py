"""Property-based tests for ownership isolation (Property 5).

**Validates: Requirements 8.1, 8.2**

Property 5: Ownership Isolation
— For any user who does not own a classroom, all upload, list, and delete
operations on that classroom's documents are rejected with HTTP 404.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st
from httpx import ASGITransport, AsyncClient

from app.api.documents import verify_classroom_ownership
from app.main import create_app
from app.dependencies import get_current_user, get_db
from app.models.user import User


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------

# Generate positive integer IDs for users and classrooms
_user_id_strategy = st.integers(min_value=1, max_value=1_000_000)
_class_id_strategy = st.integers(min_value=1, max_value=1_000_000)
_document_id_strategy = st.integers(min_value=1, max_value=1_000_000)


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


# Minimal valid PDF-like content for upload requests
_MINIMAL_PDF_CONTENT = b"%PDF-1.4 minimal content for testing"


# ---------------------------------------------------------------------------
# Property 5: Ownership Isolation
# ---------------------------------------------------------------------------


class TestOwnershipIsolationProperty:
    """Property 5: Ownership Isolation.

    **Validates: Requirements 8.1, 8.2**

    For any user who does not own a classroom, all upload, list, and delete
    operations on that classroom's documents are rejected with HTTP 404.
    The system responds with "Clase no encontrada" without revealing whether
    the classroom exists for another user.
    """

    @given(user_id=_user_id_strategy, class_id=_class_id_strategy)
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_non_owner_rejected_with_404(self, user_id: int, class_id: int):
        """For any user_id and class_id combination where get_class_by_id returns
        None (non-ownership), verify_classroom_ownership raises HTTPException 404.

        This property covers all three operations (upload, list, delete)
        because they all call verify_classroom_ownership as their first gate.
        """
        mock_db = AsyncMock()

        with patch(
            "app.api.documents.get_class_by_id", new_callable=AsyncMock
        ) as mock_get_class:
            # Simulate non-ownership: get_class_by_id returns None
            mock_get_class.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await verify_classroom_ownership(
                    db=mock_db, class_id=class_id, user_id=user_id
                )

            assert exc_info.value.status_code == 404
            assert "Clase no encontrada" in exc_info.value.detail

            # Verify get_class_by_id was called with the correct parameters
            mock_get_class.assert_called_once_with(
                mock_db, class_id=class_id, user_id=user_id
            )

    @given(user_id=_user_id_strategy, class_id=_class_id_strategy)
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_owner_not_rejected(self, user_id: int, class_id: int):
        """For any user_id and class_id combination where get_class_by_id returns
        a classroom (ownership confirmed), verify_classroom_ownership does NOT raise."""
        mock_db = AsyncMock()
        mock_classroom = MagicMock()
        mock_classroom.id = class_id
        mock_classroom.user_id = user_id

        with patch(
            "app.api.documents.get_class_by_id", new_callable=AsyncMock
        ) as mock_get_class:
            mock_get_class.return_value = mock_classroom

            # Should NOT raise any exception
            await verify_classroom_ownership(
                db=mock_db, class_id=class_id, user_id=user_id
            )

            mock_get_class.assert_called_once_with(
                mock_db, class_id=class_id, user_id=user_id
            )


class TestOwnershipIsolationEndpoints:
    """Integration tests verifying ownership isolation at the HTTP layer.

    **Validates: Requirements 8.1, 8.2**

    Confirms that all three document endpoints (upload, list, delete)
    return HTTP 404 when the authenticated user does not own the classroom.
    """

    @pytest.mark.anyio
    async def test_upload_rejected_for_non_owner(self):
        """POST /classes/{class_id}/documents returns 404 for non-owner."""
        app = create_app()
        user = _make_user(42)
        mock_db = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.api.documents.get_class_by_id", new_callable=AsyncMock
        ) as mock_get_class:
            mock_get_class.return_value = None

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/api/v1/classes/99/documents",
                    files={"file": ("test.pdf", _MINIMAL_PDF_CONTENT, "application/pdf")},
                )

            assert resp.status_code == 404
            assert "Clase no encontrada" in resp.json()["detail"]

    @pytest.mark.anyio
    async def test_list_rejected_for_non_owner(self):
        """GET /classes/{class_id}/documents returns 404 for non-owner."""
        app = create_app()
        user = _make_user(42)
        mock_db = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.api.documents.get_class_by_id", new_callable=AsyncMock
        ) as mock_get_class:
            mock_get_class.return_value = None

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/api/v1/classes/99/documents")

            assert resp.status_code == 404
            assert "Clase no encontrada" in resp.json()["detail"]

    @pytest.mark.anyio
    async def test_delete_rejected_for_non_owner(self):
        """DELETE /classes/{class_id}/documents/{doc_id} returns 404 for non-owner."""
        app = create_app()
        user = _make_user(42)
        mock_db = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.api.documents.get_class_by_id", new_callable=AsyncMock
        ) as mock_get_class:
            mock_get_class.return_value = None

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.delete("/api/v1/classes/99/documents/1")

            assert resp.status_code == 404
            assert "Clase no encontrada" in resp.json()["detail"]
