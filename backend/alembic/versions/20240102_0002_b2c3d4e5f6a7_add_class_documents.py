"""Add class_documents and document_embeddings tables.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2024-01-02 00:02:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension is enabled (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- class_documents ---
    op.create_table(
        "class_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "classroom_id",
            sa.Integer,
            sa.ForeignKey("classrooms.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- document_embeddings ---
    op.create_table(
        "document_embeddings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("class_documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "classroom_id",
            sa.Integer,
            sa.ForeignKey("classrooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Add the vector column using raw SQL (pgvector 384 dimensions)
    op.execute(
        "ALTER TABLE document_embeddings "
        "ADD COLUMN embedding vector(384) NOT NULL"
    )

    # Add unique constraint on (document_id, content_hash)
    op.create_unique_constraint(
        "uq_doc_chunk_hash",
        "document_embeddings",
        ["document_id", "content_hash"],
    )

    # Add index on classroom_id for document_embeddings
    op.create_index(
        "ix_doc_embed_classroom",
        "document_embeddings",
        ["classroom_id"],
    )


def downgrade() -> None:
    op.drop_table("document_embeddings")
    op.drop_table("class_documents")
