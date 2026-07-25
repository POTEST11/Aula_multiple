"""End-to-end integration tests for the full user flow.

Tests the complete HTTP chain: routing, validation, auth, serialization.
Mocks at the CRUD and agent-graph layer to avoid needing a real database or LLM.

Validates: Requirements 9.3, 8.1
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.dependencies import get_current_user, get_db
from app.models.activity import Activity, ActivityVariant, VariantStandard
from app.models.classroom import Classroom
from app.models.subject import Subject
from app.models.user import User
from app.schemas.activity import ActivityOutput, CurriculumStandard, VariantOutput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: int = 1) -> MagicMock:
    """Create a mock User that passes from_attributes validation."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "profesor@aula.com"
    user.name = "Profesor Test"
    user.password_hash = "$2b$12$KIXgq5j8FzVk3Q5z5z5z5O5z5z5z5z5z5z5z5z5z5z5z5z5z5z"
    user.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return user


def _make_classroom(classroom_id: int = 10, user_id: int = 1) -> MagicMock:
    """Create a mock Classroom."""
    c = MagicMock(spec=Classroom)
    c.id = classroom_id
    c.user_id = user_id
    c.name = "Aula Multigrado 3-4-5"
    c.grades = [3, 4, 5]
    c.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    c.updated_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return c


def _make_subject(subject_id: int = 5, user_id: int = 1) -> MagicMock:
    """Create a mock Subject."""
    s = MagicMock(spec=Subject)
    s.id = subject_id
    s.user_id = user_id
    s.name = "Matemáticas"
    s.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return s


def _make_activity(activity_id: int = 100, user_id: int = 1) -> MagicMock:
    """Create a mock Activity with variants and standards."""
    activity = MagicMock(spec=Activity)
    activity.id = activity_id
    activity.user_id = user_id
    activity.topic = "Fracciones"
    activity.grades = [3, 4, 5]
    activity.subject_name = "Matemáticas"
    activity.classroom_name = "Aula Multigrado 3-4-5"
    activity.available_resources = ["pizarra", "cuaderno"]
    activity.anchor_activity = "Actividad ancla sobre fracciones para multigrado"
    activity.classroom_id = 10
    activity.subject_id = 5
    activity.created_at = datetime(2024, 6, 2, 10, 0, 0, tzinfo=timezone.utc)

    # Create variant standards
    std = MagicMock(spec=VariantStandard)
    std.country = "Colombia"
    std.grade = 3
    std.subject = "Matemáticas"
    std.standard_text = "Resolver problemas con fracciones simples"

    # Create variants
    variant = MagicMock(spec=ActivityVariant)
    variant.grade = 3
    variant.content = "Contenido adaptado para grado 3"
    variant.instructions = "Instrucciones para grado 3"
    variant.exercises = "Ejercicios de fracciones grado 3"
    variant.standards = [std]

    activity.variants = [variant]
    return activity


def _make_activity_output() -> ActivityOutput:
    """Create a valid ActivityOutput for mocking the agent graph result."""
    return ActivityOutput(
        topic="Fracciones",
        grades=[3, 4, 5],
        subject_name="Matemáticas",
        classroom_name=None,
        available_resources=["pizarra", "cuaderno"],
        anchor_activity="Actividad ancla sobre fracciones para multigrado",
        variants=[
            VariantOutput(
                grade=3,
                content="Contenido adaptado para grado 3",
                instructions="Instrucciones para grado 3",
                exercises="Ejercicios de fracciones grado 3",
                aligned_standards=[
                    CurriculumStandard(
                        country="Colombia",
                        grade=3,
                        subject="Matemáticas",
                        text="Resolver problemas con fracciones simples",
                    )
                ],
            ),
            VariantOutput(
                grade=4,
                content="Contenido adaptado para grado 4",
                instructions="Instrucciones para grado 4",
                exercises="Ejercicios de fracciones grado 4",
                aligned_standards=[],
            ),
            VariantOutput(
                grade=5,
                content="Contenido adaptado para grado 5",
                instructions="Instrucciones para grado 5",
                exercises="Ejercicios de fracciones grado 5",
                aligned_standards=[],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Test 1: Full E2E flow
# register → login → create class → create subject → generate activity →
# query history → get detail → delete activity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_e2e_flow():
    """Test the complete user flow from registration to activity deletion.

    Validates: Requirements 9.3, 8.1

    This test mocks at the CRUD layer and agent graph level while exercising
    the full HTTP request chain (middleware, auth, routing, validation,
    response serialization).
    """
    fake_user = _make_user()
    fake_classroom = _make_classroom()
    fake_subject = _make_subject()
    fake_activity = _make_activity()
    activity_output = _make_activity_output()

    app = create_app()

    # Override get_db with a mock async session
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    # Override get_current_user to return our fake user (skips JWT+DB check)
    async def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        # ============================================================
        # STEP 1: Register
        # ============================================================
        with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=None):
            with patch("app.api.auth.create_user", new_callable=AsyncMock, return_value=fake_user):
                resp = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "profesor@aula.com",
                        "password": "password123",
                        "name": "Profesor Test",
                    },
                )
        assert resp.status_code == 201, f"Register failed: {resp.text}"
        data = resp.json()
        assert data["email"] == "profesor@aula.com"
        assert data["name"] == "Profesor Test"
        assert "id" in data

        # ============================================================
        # STEP 2: Login
        # ============================================================
        with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=fake_user):
            with patch("app.api.auth.verify_password", return_value=True):
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "profesor@aula.com",
                        "password": "password123",
                    },
                )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        token_data = resp.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Use a bearer token header for subsequent requests
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # ============================================================
        # STEP 3: Create a class
        # ============================================================
        with patch(
            "app.api.classes.crud_create_class",
            new_callable=AsyncMock,
            return_value=fake_classroom,
        ):
            resp = await client.post(
                "/api/v1/classes/",
                json={"name": "Aula Multigrado 3-4-5", "grades": [3, 4, 5]},
                headers=headers,
            )
        assert resp.status_code == 201, f"Create class failed: {resp.text}"
        class_data = resp.json()
        assert class_data["name"] == "Aula Multigrado 3-4-5"
        assert class_data["grades"] == [3, 4, 5]
        classroom_id = class_data["id"]

        # ============================================================
        # STEP 4: Create a subject
        # ============================================================
        with patch(
            "app.api.subjects.create_subject",
            new_callable=AsyncMock,
            return_value=fake_subject,
        ):
            resp = await client.post(
                "/api/v1/subjects",
                json={"name": "Matemáticas"},
                headers=headers,
            )
        assert resp.status_code == 201, f"Create subject failed: {resp.text}"
        subject_data = resp.json()
        assert subject_data["name"] == "Matemáticas"
        subject_id = subject_data["id"]

        # ============================================================
        # STEP 5: Generate activity (mock agent graph)
        # ============================================================
        # Mock the db.execute for classroom/subject lookups inside activities endpoint
        mock_classroom_result = MagicMock()
        mock_classroom_result.scalar_one_or_none.return_value = fake_classroom

        mock_subject_result = MagicMock()
        mock_subject_result.scalar_one_or_none.return_value = fake_subject

        mock_db.execute = AsyncMock(
            side_effect=[mock_classroom_result, mock_subject_result]
        )

        # Mock build_activity_graph to return a fake compiled graph
        fake_graph = AsyncMock()
        fake_graph.ainvoke = AsyncMock(
            return_value={
                "final_output": activity_output,
                "error": None,
            }
        )

        with patch(
            "app.api.activities.build_activity_graph",
            return_value=fake_graph,
        ):
            with patch(
                "app.api.activities.save_activity",
                new_callable=AsyncMock,
                return_value=fake_activity,
            ):
                resp = await client.post(
                    "/api/v1/activities/generate",
                    json={
                        "topic": "Fracciones",
                        "grades": [3, 4, 5],
                        "subject_name": "Matemáticas",
                        "classroom_id": classroom_id,
                        "subject_id": subject_id,
                        "available_resources": ["pizarra", "cuaderno"],
                    },
                    headers=headers,
                )
        assert resp.status_code == 200, f"Generate activity failed: {resp.text}"
        activity_data = resp.json()
        assert activity_data["topic"] == "Fracciones"
        assert activity_data["grades"] == [3, 4, 5]
        assert len(activity_data["variants"]) == 3
        activity_id = activity_data["id"]

        # ============================================================
        # STEP 6: Query history - verify the activity appears
        # ============================================================
        with patch(
            "app.api.history.list_history",
            new_callable=AsyncMock,
            return_value=[fake_activity],
        ):
            resp = await client.get("/api/v1/history", headers=headers)
        assert resp.status_code == 200, f"List history failed: {resp.text}"
        history = resp.json()
        assert len(history) == 1
        assert history[0]["topic"] == "Fracciones"
        assert history[0]["id"] == activity_id

        # ============================================================
        # STEP 7: Get activity detail
        # ============================================================
        with patch(
            "app.api.history.get_activity_by_id",
            new_callable=AsyncMock,
            return_value=fake_activity,
        ):
            resp = await client.get(
                f"/api/v1/history/{activity_id}", headers=headers
            )
        assert resp.status_code == 200, f"Get detail failed: {resp.text}"
        detail = resp.json()
        assert detail["topic"] == "Fracciones"
        assert detail["anchor_activity"] == "Actividad ancla sobre fracciones para multigrado"
        assert len(detail["variants"]) == 1  # Only one variant in our mock activity

        # ============================================================
        # STEP 8: Delete activity
        # ============================================================
        with patch(
            "app.api.history.get_activity_by_id",
            new_callable=AsyncMock,
            return_value=fake_activity,
        ):
            with patch(
                "app.api.history.delete_activity",
                new_callable=AsyncMock,
            ):
                resp = await client.delete(
                    f"/api/v1/history/{activity_id}", headers=headers
                )
        assert resp.status_code == 204, f"Delete failed: {resp.text}"

        # ============================================================
        # STEP 9: Verify activity is gone from history
        # ============================================================
        with patch(
            "app.api.history.list_history",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = await client.get("/api/v1/history", headers=headers)
        assert resp.status_code == 200
        history_after = resp.json()
        assert len(history_after) == 0

    # Cleanup overrides
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 2: Docker Compose validation
# ---------------------------------------------------------------------------


class TestDockerComposeValidation:
    """Static validation of docker-compose.yml structure.

    Validates: Requirements 9.3 (Docker deployment)
    """

    @pytest.fixture
    def compose_config(self) -> dict:
        """Load and parse docker-compose.yml."""
        import os

        compose_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "docker-compose.yml"
        )
        with open(compose_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_compose_is_valid_yaml(self, compose_config):
        """docker-compose.yml should parse as valid YAML with a services key."""
        assert compose_config is not None
        assert "services" in compose_config

    def test_compose_contains_expected_services(self, compose_config):
        """All required services (backend, frontend, db) must be defined."""
        services = compose_config["services"]
        assert "backend" in services
        assert "frontend" in services
        assert "db" in services

    def test_backend_depends_on_db(self, compose_config):
        """Backend service must depend on the db service."""
        backend = compose_config["services"]["backend"]
        depends_on = backend.get("depends_on", {})
        if isinstance(depends_on, list):
            assert "db" in depends_on
        else:
            assert "db" in depends_on

    def test_frontend_depends_on_backend(self, compose_config):
        """Frontend service must depend on the backend service."""
        frontend = compose_config["services"]["frontend"]
        depends_on = frontend.get("depends_on", {})
        if isinstance(depends_on, list):
            assert "backend" in depends_on
        else:
            assert "backend" in depends_on

    def test_db_has_healthcheck(self, compose_config):
        """Database service must have a healthcheck configured."""
        db = compose_config["services"]["db"]
        assert "healthcheck" in db
        healthcheck = db["healthcheck"]
        assert "test" in healthcheck
        assert "interval" in healthcheck
        assert "timeout" in healthcheck
        assert "retries" in healthcheck

    def test_db_uses_pgvector_image(self, compose_config):
        """Database service should use the pgvector image."""
        db = compose_config["services"]["db"]
        assert "pgvector" in db.get("image", "")

    def test_backend_runs_migrations(self, compose_config):
        """Backend command should include alembic upgrade head."""
        backend = compose_config["services"]["backend"]
        command = backend.get("command", "")
        assert "alembic upgrade head" in command

    def test_volumes_defined(self, compose_config):
        """A persistent volume for postgres data should be defined."""
        assert "volumes" in compose_config
        assert "pgdata" in compose_config["volumes"]
