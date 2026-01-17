"""add knowledge chunks

Revision ID: 7c1c8b9e3a2a
Revises: c543b9f0b770
Create Date: 2026-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "7c1c8b9e3a2a"
down_revision: Union[str, Sequence[str], None] = "c543b9f0b770"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "chunk_index",
            name="uq_knowledge_chunks_source_chunk_index",
        ),
    )
    op.create_index(
        "ix_knowledge_chunks_embedding",
        "knowledge_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_knowledge_chunks_embedding", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
