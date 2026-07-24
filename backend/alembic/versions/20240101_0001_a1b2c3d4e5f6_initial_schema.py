"""Initial schema with pgvector extension and all tables.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2024-01-01 00:01:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- classrooms ---
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("grades", sa.ARRAY(sa.Integer), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- subjects ---
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- activities ---
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "classroom_id",
            sa.Integer,
            sa.ForeignKey("classrooms.id"),
            nullable=True,
        ),
        sa.Column(
            "subject_id",
            sa.Integer,
            sa.ForeignKey("subjects.id"),
            nullable=True,
        ),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("grades", sa.ARRAY(sa.Integer), nullable=False),
        sa.Column("subject_name", sa.String(255), nullable=False),
        sa.Column("classroom_name", sa.String(255), nullable=True),
        sa.Column("available_resources", sa.ARRAY(sa.String), nullable=True),
        sa.Column("anchor_activity", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
    )

    # --- activity_variants ---
    op.create_table(
        "activity_variants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "activity_id",
            sa.Integer,
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("grade", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("instructions", sa.Text, nullable=False),
        sa.Column("exercises", sa.Text, nullable=False),
    )

    # --- curriculum_embeddings ---
    op.create_table(
        "curriculum_embeddings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("country", sa.String(100), nullable=False, index=True),
        sa.Column("grade", sa.Integer, nullable=False, index=True),
        sa.Column("subject", sa.String(255), nullable=False, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Add the vector column using raw SQL (pgvector 384 dimensions)
    op.execute(
        "ALTER TABLE curriculum_embeddings "
        "ADD COLUMN embedding vector(384) NOT NULL"
    )

    # --- variant_standards ---
    op.create_table(
        "variant_standards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "variant_id",
            sa.Integer,
            sa.ForeignKey("activity_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "curriculum_embedding_id",
            sa.Integer,
            sa.ForeignKey("curriculum_embeddings.id"),
            nullable=True,
        ),
        sa.Column("standard_text", sa.Text, nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("grade", sa.Integer, nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("variant_standards")
    op.drop_table("curriculum_embeddings")
    op.drop_table("activity_variants")
    op.drop_table("activities")
    op.drop_table("subjects")
    op.drop_table("classrooms")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
